import json
from typing import Callable, Dict, Union
from threading import Thread

from mqtt import Subscriber
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

from .question import Question
from .participant import Participant

import context as ctx

class SessionEventMonitor(Subscriber):
    def __init__(self, session_id: int, host='localhost', port=1883):
        Subscriber.__init__(self, host, port)
        self.session_id: int = session_id
        self.on_participant_ready: Callable[[int], None] = None

        self.client.subscribe([
            (f"swarm/session/{session_id}/control/+", 0),
            (f"swarm/session/{session_id}/updates/+", 0)]
        )

    def on_message(self, client, obj, msg):
        topic_data = msg.topic.split('/', 4)
        if (
            len(topic_data) != 5
            or topic_data[0] != 'swarm'
            or topic_data[1] != 'session'
            or topic_data[2] != str(self.session_id)
            or topic_data[3] not in ['control', 'updates']
        ):
            print(f"ERROR: Invalid topic '{msg.topic}' for Session ID={self.session_id}")
            return

        client_id = int(topic_data[4])

        if topic_data[3] == 'control':
            print(f"[session {self.session_id}] CONTROL: {msg.payload}")
            data = json.loads(msg.payload)
            if data['type'] == 'ready' and self.on_participant_ready:
                self.on_participant_ready(client_id)

        elif topic_data[3] == 'updates':
            print(f"[session {self.session_id}] UPDATE: {msg.payload}")

class Session(QObject):
    last_id = 0

    #on_participant_ready = pyqtSignal(Participant)
    on_question_notified = pyqtSignal(QObject, bool)
    on_start = pyqtSignal(QObject, bool)
    on_stop = pyqtSignal(QObject, bool)

    class Status(Enum):
        WAITING = 'waiting'     # Waiting for clients to join
        STARTING = 'starting'   # The question has been notified to clients
        STARTED = 'started'     # The Swarm Session is active (answering a question)

    def __init__(self):
        if ctx.AppContext.mqtt_broker is None:
            raise RuntimeError("MQTT broker not started")

        QObject.__init__(self)

        Session.last_id += 1
        self.id = Session.last_id
        self.status = Session.Status.WAITING
        self._question = None
        self.duration = 30
        self.participants: Dict[Participant] = {}

        self.monitor = SessionEventMonitor(self.id, port=ctx.AppContext.mqtt_broker.port)
        self.monitor.on_participant_ready = self.participant_ready_handler
        self.monitor.start()

    def __eq__(self, other):
        return isinstance(other, Session) and self.id == other.id

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'status': self.status.value,
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

        self.publish_async(
            f'swarm/session/{self.id}/control',
            json.dumps({
                'type': 'setup',
                'question_id': self._question.id if question is not None else None
            }),
            lambda success: self.on_question_notified.emit(self, success)
        )
    
    def publish(self, topic, msg, callback: Callable[[bool], None] = None):
        msg_handle = self.monitor.client.publish(topic, msg)
        msg_handle.wait_for_publish()
        if callback: callback(True) # TODO: Send false if message could not be queued
    
    def publish_async(self, topic, msg, post_signal=None):
        Thread(
            target=self.publish,
            args=(topic, msg, post_signal),
            daemon=True
        ).start()

    def participant_ready_handler(self, participant_id: int):
        participant = self.participants.get(participant_id, None)
        if participant is None:
            print(f"ERROR: Participant [id={participant_id}] not found in Session [id={self.id}]")
            return

        participant.status = Participant.Status.READY
        #self.on_participant_ready.emit(participant)

    def start(self):
        def callback(success):
            self.status = Session.Status.STARTED
            self.on_start.emit(self, success)

        self.publish_async(
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

        self.publish_async(
            f'swarm/session/{self.id}/control',
            json.dumps({
                'type': 'stop',
            }),
            callback
        )
