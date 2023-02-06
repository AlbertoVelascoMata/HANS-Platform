from argparse import Namespace
from typing import Dict

from .session import Session
from .participant import Participant

class AppContext:
    args = Namespace(
        mqtt_port=1883,
        api_port=5000,
    )

    mqtt_broker = None
    api_service = None

    sessions: 'Dict[Session]' = {}
