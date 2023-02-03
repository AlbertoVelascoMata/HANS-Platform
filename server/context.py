import json
from argparse import Namespace
from typing import Dict, List

from mqtt import Subscriber
from enum import Enum

class AppContext:
    args = Namespace(
        mqtt_port=1883,
        api_port=5000,
    )

    mqtt_broker = None
    mqtt_session_sub = None

    api_service = None

    sessions: 'Dict[Session]' = {}


class SessionControlMonitor(Subscriber):
    def __init__(self, session_id, host='localhost', port=1883):
        self.session_id = session_id
        self.on_ready = None
        Subscriber.__init__(self,
                            f"swarm/session/{session_id}/control",
                            host, port)
    
    def on_message(self, client, obj, msg):
        print(f"[session {self.session_id}] CONTROL: {msg}")

class SessionUpdatesMonitor(Subscriber):
    def __init__(self, session_id, host='localhost', port=1883):
        self.session_id = session_id
        Subscriber.__init__(self,
                            f"swarm/session/{session_id}/updates",
                            host, port)

    def on_message(self, client, obj, msg):
        print(f"[session {self.session_id}] UPDATE: {msg}")

class Participant:
    class Status(Enum):
        JOINING = 'joining'
        JOINED = 'joined'
        READY = 'ready'

    @property
    def as_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'status': self.status.value,
        }

    def __init__(self, username):
        self.id = 1
        self.username = username
        self.status = Participant.Status.JOINING

class Session:
    last_id = 0

    class Status(Enum):
        WAITING = 'waiting'     # Waiting for clients to join
        STARTING = 'starting'   # The question has been notified to clients
        STARTED = 'started'     # The Swarm Session is active (answering a question)

    def __init__(self):
        if AppContext.mqtt_broker is None:
            raise RuntimeError("MQTT broker not started")

        Session.last_id += 1
        self.id = Session.last_id
        self.status = Session.Status.WAITING
        self.active_question = None
        self.duration = 30
        self.participants: Dict[Participant] = {}

        self.control_monitor = SessionControlMonitor(self.id,
                                                     port=AppContext.mqtt_broker.port)
        self.control_monitor.on_ready = lambda participant: self.participants.append(participant)

        self.updates_monitor = SessionUpdatesMonitor(self.id,
                                                     port=AppContext.mqtt_broker.port)

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
        self.control_monitor.client.publish(
            f'swarm/session/{self.id}/control',
            json.dumps({
                'type': 'setup',
                'question_id': 1
            }))
