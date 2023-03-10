import json
from datetime import datetime
from enum import Enum
from io import TextIOBase
from typing import Callable, Dict, Union

from PyQt5.QtCore import QElapsedTimer, QObject, pyqtSignal

import src.context as ctx
from .mqtt_utils import MQTTClient
from .participant import Participant
from .question import Question


class SessionCommunicator(MQTTClient):
    class Status(Enum):
        DISCONNECTED = 'disconnected'
        CONNECTED = 'connected'
        SUBSCRIBED = 'subscribed'

    def __init__(self, session_id: int, host='localhost', port=1883):
        self.session_id: int = session_id
        self._status = SessionCommunicator.Status.DISCONNECTED

        self.on_status_changed: Callable[[SessionCommunicator.Status], None] = None
        self.on_participant_ready: Callable[[int], None] = None
        self.on_participant_update: Callable[[int, float, dict]] = None

        MQTTClient.__init__(self, host, port)
        self.client.message_callback_add('swarm/session/+/control/+', self.control_message_handler)
        self.client.message_callback_add('swarm/session/+/updates/+', self.updates_message_handler)

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, status: Status):
        self._status = status
        if self.on_status_changed:
            self.on_status_changed(self.status)

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
            # TODO: Participants should also notify their configured question_id and duration,
            #       so the server can check if their ready state matches de current session or
            #       is older (i.e. the question has changed twice and the participant still has
            #       the previous question configured)
            #       Message format: {"type": "ready", "question_id": 1, "duration": 30}
            self.on_participant_ready(client_id)
        else:
            print("Unknown message received in control topic")
            # TODO: Implement a 'keep-alive' mechanism: participants must send keep-alive messages
            #       periodically so the server can determine if they have left without notifying

    def updates_message_handler(self, client, obj, msg):
        client_id = int(msg.topic.split('/')[-1])
        print(f"[session {self.session_id}] UPDATE (client={client_id}): {msg.payload}")
        payload = json.loads(msg.payload)

        if self.on_participant_update:
            self.on_participant_update(client_id, payload.get('timestamp', None), payload.get('data', {}))

class Session(QObject):
    '''
        Contains all attributes, methods and events to handle a SWARM Session.
    '''
    last_id = 0

    class Status(Enum):
        WAITING = 'waiting' # Waiting for clients to join
        ACTIVE = 'active'   # The Swarm Session is active (answering a question)
        # TODO: There should be at least an additional state where the server is
        #       waiting for clients to get ready. This would be useful for the GUI
        #       to check if the session can start or not

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

    on_participant_joined = pyqtSignal(QObject, Participant)
    '''
        `on_participant_joined(session: Session, participant: Participant)`

        Emitted when the a new participant joins the session.
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
        self.log_file: TextIOBase = None
        self.timer = QElapsedTimer()

        self.communicator = SessionCommunicator(self.id, port=ctx.AppContext.mqtt_broker.port)
        self.communicator.on_status_changed = lambda status: self.on_connection_status_changed.emit(self, status)
        self.communicator.on_participant_ready = self.participant_ready_handler
        self.communicator.on_participant_update = self.participant_update_handler
        self.communicator.start()

    def __eq__(self, other):
        return isinstance(other, Session) and self.id == other.id

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, status: Status):
        self._status = status
        self.on_status_changed.emit(self, status)

    @property
    def active_question(self):
        return self._question

    @active_question.setter
    def active_question(self, question: Union[int, Question]):
        for participant in self.participants.values():
            participant.status = Participant.Status.JOINED
        self.on_participants_ready_changed.emit(0, len(self.participants))

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

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'status': self._status.value,
            'question_id': self._question.id if self._question else None,
            'duration': self.duration,
        }

    def add_participant(self, participant: Participant):
        self.participants[participant.id] = participant
        self.on_participant_joined.emit(self, participant)

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

    def start(self) -> bool:
        if self._question is None:
            self.on_start.emit(self, False)
            return

        # TODO: This should be done asynchronously
        session_time = datetime.now()
        self.timer.restart()
        log_folder = ctx.SESSION_LOG_FOLDER / session_time.strftime('%Y-%m-%d-%H-%M-%S')
        log_folder.mkdir(parents=True, exist_ok=True)
        with open(log_folder / 'session.json', 'w') as f:
            json.dump({
                'time': session_time.isoformat(),
                'id': self.id,
                'question': self._question.id,
                'duration': self.duration,
                'participants': [participant.as_dict for participant in self.participants.values()]
            }, f, indent=4)

        def callback(success):
            self.log_file = open(log_folder / 'log.csv', 'w')
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

        if self.log_file:
            self.log_file.close()
            self.log_file = None

    def participant_update_handler(self, participant_id: int, timestamp: float, data: dict):
        position_data = data.get('position', None)
        if not position_data:
            return

        if self.log_file:
            self.log_file.write(f"{participant_id},{timestamp},{','.join(str(e) for e in position_data)}\n")

        # TODO: Maybe the server should not rely the calculation of the central cue
        #       position to the clients, but instead calculate it every X milliseconds
        #       and send it over the topic 'swarm/session/<session-id>/updates' (which
        #       is currently not used since clients send updates over their own subtopics)
