from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

class Participant(QObject):
    last_id = 0

    class Status(Enum):
        JOINING = 'joining'
        JOINED = 'joined'
        READY = 'ready'

    on_status_changed = pyqtSignal(QObject, Status)

    @property
    def as_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'status': self._status.value,
        }

    def __init__(self, username):
        QObject.__init__(self)
        Participant.last_id += 1
        self.id = Participant.last_id
        self.username = username
        self._status = Participant.Status.JOINING

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        if status != self._status:
            self._status = status
            self.on_status_changed.emit(self, status)
