import json
from typing import Callable, Dict, Union
from threading import Thread

from mqtt import MQTTClient
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

from .question import Question
from .participant import Participant

import context as ctx

class SessionCommunicator(MQTTClient):
    class Status(Enum):
        DISCONNECTED = 'disconnected'
        CONNECTED = 'connected'
        SUBSCRIBED = 'subscribed'

    @property
    def status(self) -> Status:
        return self._status
    
    @status.setter
    def status(self, status: Status):
        self._status = status
        if self.on_status_changed:
            self.on_status_changed(self.status)

    def __init__(self, session_id: int, host='localhost', port=1883):
        self.session_id: int = session_id
        self._status = SessionCommunicator.Status.DISCONNECTED
        
        self.on_status_changed: Callable[[SessionCommunicator.Status], None] = None
        self.on_participant_ready: Callable[[int], None] = None
        self.on_participant_update: Callable[[int, dict]] = None

        MQTTClient.__init__(self, host, port)
        self.client.message_callback_add('swarm/session/+/control/+', self.control_message_handler)
        self.client.message_callback_add('swarm/session/+/updates/+', self.updates_message_handler)

    def connection_handler(self, connected, reason) -> None:
        if not connected:
            self.status = SessionCommunicator.Status.DISCONNECTED
            return

        self.status = SessionCommunicator.Status.CONNECTED

        # Subscribe to session topic
        def callback(success: bool):
            if success:
                self.status = SessionCommunicator.Status.SUBSCRIBED
        self.subscribe(f"swarm/session/{self.session_id}/#", callback)        

    def control_message_handler(self, client, obj, msg):
        client_id = int(msg.topic.split('/')[-1])
        print(f"[session {self.session_id}] CONTROL (client={client_id}): {msg.payload}")

        payload = json.loads(msg.payload)
        msg_type = payload.get('type', '')

        if msg_type == 'ready' and self.on_participant_ready:
            self.on_participant_ready(client_id)
        else:
            print("Unknown message received in control topic")

    def updates_message_handler(self, client, obj, msg):
        client_id = int(msg.topic.split('/')[-1])
        print(f"[session {self.session_id}] UPDATE (client={client_id}): {msg.payload}")
        payload = json.loads(msg.payload)

        if self.on_participant_update:
            self.on_participant_update(client_id, payload.get('data', {}))

class Session(QObject):
    '''
        Contains all attributes, methods and events to handle a SWARM Session.
    '''
    last_id = 0

    class Status(Enum):
        WAITING = 'waiting' # Waiting for clients to join
        ACTIVE = 'active'   # The Swarm Session is active (answering a question)

    on_status_changed = pyqtSignal(QObject, Status)
    '''
        `on_status_changed(session: Session, status: Session.Status)`

        Emitted when the session status changes.
    '''
    on_connection_status_changed = pyqtSignal(QObject, SessionCommunicator.Status)
    '''
        `on_connection_status_changed(session: Session, status: SessionCommunicator.Status)`

        Emitted when the session MQTT communication changed its state.
    '''

    on_question_notified = pyqtSignal(QObject, bool)
    '''
        `on_question_notified(session: Session, success: bool)`

        Emitted when the question setup event was sent. The `success`
        param indicates whether the event was successfully published or not.
    '''

    on_participants_ready_changed = pyqtSignal(int, int)
    '''
        `on_participants_ready_changed(ready_count: int, total_count: int)`

        Emitted when the number of ready participants changed.
    '''

    on_start = pyqtSignal(QObject, bool)
    '''
        `on_start(session: Session, started: bool)`

        Emitted when the start event was sent. The `started` param indicates
        whether the event was successfully published or not.
    '''

    on_stop = pyqtSignal(QObject, bool)
    '''
        `on_stop(session: Session, stopped: bool)`

        Emitted when the stop event was sent. The `stopped` param indicates
        whether the event was successfully published or not.
    '''

    @property
    def status(self) -> Status:
        return self._status
    
    @status.setter
    def status(self, status: Status):
        self._status = status
        self.on_status_changed.emit(self, status)

    def __init__(self):
        if ctx.AppContext.mqtt_broker is None:
            raise RuntimeError("MQTT broker not started")

        QObject.__init__(self)

        Session.last_id += 1
        self.id = Session.last_id
        self._status = Session.Status.WAITING
        self._question = None
        self.duration = 30
        self.participants: Dict[Participant] = {}

        self.communicator = SessionCommunicator(self.id, port=ctx.AppContext.mqtt_broker.port)
        self.communicator.on_status_changed = lambda status: self.on_connection_status_changed.emit(self, status)
        self.communicator.on_participant_ready = self.participant_ready_handler
        self.communicator.start()

    def __eq__(self, other):
        return isinstance(other, Session) and self.id == other.id

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'status': self._status.value,
            'question_id': self._question.id if self._question else None,
            'duration': self.duration,
        }

    @property
    def active_question(self):
        return self._question

    @active_question.setter
    def active_question(self, question: Union[int, Question]):
        if question is None or isinstance(question, Question):
            self._question = question
        else:
            self._question = ctx.AppContext.questions[question]

        self.communicator.publish(
            f'swarm/session/{self.id}/control',
            json.dumps({
                'type': 'setup',
                'question_id': self._question.id if question is not None else None
            }),
            lambda success: self.on_question_notified.emit(self, success)
        )

    @property
    def ready_participants_count(self):
        return sum(
                participant.status == Participant.Status.READY
                for participant in self.participants.values()
            )

    def participant_ready_handler(self, participant_id: int):
        participant = self.participants.get(participant_id, None)
        if participant is None:
            print(f"ERROR: Participant [id={participant_id}] not found in Session [id={self.id}]")
            return

        participant.status = Participant.Status.READY
        self.on_participants_ready_changed.emit(
            self.ready_participants_count,
            len(self.participants)
        )

    def start(self):
        def callback(success):
            self.status = Session.Status.ACTIVE
            self.on_start.emit(self, success)

        self.communicator.publish(
            f'swarm/session/{self.id}/control',
            json.dumps({
                'type': 'start'
            }),
            callback
        )

    def stop(self):
        def callback(success):
            self.status = Session.Status.WAITING
            self.on_stop.emit(self, success)

        self.communicator.publish(
            f'swarm/session/{self.id}/control',
            json.dumps({
                'type': 'stop',
            }),
            callback
        )
