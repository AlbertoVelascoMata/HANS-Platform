import json
from typing import Callable, Dict

from mqtt import Subscriber
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

from .participant import Participant

import context as ctx

class SessionEventMonitor(Subscriber):
    def __init__(self, session_id: int, host='localhost', port=1883):
        Subscriber.__init__(self, host, port)
        self.session_id: int = session_id
        self.on_participant_ready: Callable[[int], None] = None

        self.client.subscribe(f"swarm/session/{session_id}/control/+", 0)
        self.client.subscribe(f"swarm/session/{session_id}/updates/+", 0)

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

    on_participant_ready = pyqtSignal(Participant)

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
        self.active_question = None
        self.duration = 30
        self.participants: Dict[Participant] = {}

        self.monitor = SessionEventMonitor(self.id, port=ctx.AppContext.mqtt_broker.port)
        self.monitor.on_participant_ready = self.participant_ready_handler
        self.monitor.start()

    def participant_ready_handler(self, participant_id: int):
        participant = self.participants.get(participant_id, None)
        if participant is None:
            print(f"ERROR: Participant [id={participant_id}] not found in Session [id={self.id}]")
            return

        participant.status = Participant.Status.READY
        self.on_participant_ready.emit(participant)

    @property
    def as_json(self):
        return {
            'id': self.id,
            'status': self.status.value,
            'question_id': self.active_question,
            'duration': self.duration,
        }

    def __eq__(self, other):
        return isinstance(other, Session) and self.id == other.id

    def start(self):
        self.monitor.client.publish(
            f'swarm/session/{self.id}/control',
            json.dumps({
                'type': 'setup',
                'question_id': 1
            }))
