from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import (
    QVBoxLayout, QGridLayout,
    QWidget, QGroupBox,
    QListWidget, QListWidgetItem,
    QLabel, QLineEdit,
    QComboBox, QPushButton
)

from context import AppContext, Session, Participant
from gui.participant import ParticipantWidget

class SessionListItem(QListWidgetItem):
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.setText(f"Session {session.id}")

class SessionPanelWidget(QWidget):
    def __init__(self,
        session: Session = None,
        parent: QWidget = None
    ):
        super().__init__(parent)
        self.session = None

        self.setupUI()

        if session is not None:
            self.set_session(session)


    ### SET QUESTION

    def on_question_changed(self, question_id: str):
        self.question_cbbox.setEnabled(False)
        if question_id == '<none>':
            self.session.active_question = None
        else:
            try:
                self.session.active_question = int(question_id)
            except (ValueError, KeyError):
                self.session.active_question = None
                self.question_cbbox.setCurrentIndex(0)

    @pyqtSlot(Session, bool)
    def on_question_notified(self, session, notified):
        self.question_cbbox.setEnabled(True)


    ### ADD PARTICIPANT

    def add_participant_widget(self, participant: Participant):
        widget = ParticipantWidget(participant)
        item = QListWidgetItem(self.participants_list)
        item.setSizeHint(widget.sizeHint())
        self.participants_list.addItem(item)
        self.participants_list.setItemWidget(item, widget)

    @pyqtSlot(Session, Participant)
    def on_participant_joined(self, session, participant):
        if session != self.session:
            return

        self.add_participant_widget(participant)
        self.start_btn.setEnabled(False)
        self.participants_ready_txt.setText(f"{session.ready_participants_count}/{len(session.participants)} participants")

    @pyqtSlot(int, int)
    def on_participants_ready_changed(self, ready_count, total_count):
        if self.session.status == Session.Status.WAITING:
            self.start_btn.setEnabled(ready_count == total_count)
            self.participants_ready_txt.setText(f"{ready_count}/{total_count} participants")


    ### START / STOP

    def on_start_btn_clicked(self):
        self.start_btn.setEnabled(False)
        if self.session.status == Session.Status.WAITING:
            self.session.start()
        elif self.session.status == Session.Status.ACTIVE:
            self.session.stop()

    @pyqtSlot(Session, bool)
    def on_start(self, session, started):
        self.status_txt.setText('Active')
        self.start_btn.setText('Stop')
        self.start_btn.setEnabled(True)

    @pyqtSlot(Session, bool)
    def on_stop(self, session, stopped):
        self.status_txt.setText('Waiting')
        self.start_btn.setText('Start')
        self.start_btn.setEnabled(True)


    ### UI SETUP

    def set_session(self, session: Session):
        if self.session is not None:
            self.session.on_question_notified.disconnect()
            self.session.on_participant_joined.disconnect()
            self.session.on_participants_ready_changed.disconnect()
            self.session.on_start.disconnect()
            self.session.on_stop.disconnect()

        self.session = session
        if session is None:
            return

        self.id_txt.setText(str(session.id))
        self.duration_txt.setText(str(session.duration))
        self.duration_txt.setEnabled(session.status == Session.Status.WAITING)
        self.status_txt.setText(session.status.value)
        self.question_cbbox.setCurrentText(str(session.active_question.id) if session.active_question else '<none>')
        self.question_cbbox.setEnabled(session.status == Session.Status.WAITING)

        # Refresh participants list
        self.participants_list.clear()
        for participant in session.participants.values():
            self.add_participant_widget(participant)

        # Update participants ready count
        participants_ready_count = session.ready_participants_count
        participants_total_count = len(session.participants)
        self.participants_ready_txt.setText(f"{participants_ready_count}/{participants_total_count} participants")

        # Configure Start/Stop button
        if session.status == Session.Status.WAITING:
            self.start_btn.setText('Start')
            self.start_btn.setEnabled((participants_ready_count == participants_total_count) and (participants_total_count > 0))
        elif session.status == Session.Status.ACTIVE:
            self.start_btn.setText('Stop')
            self.start_btn.setEnabled(True)

        session.on_question_notified.connect(self.on_question_notified)
        session.on_participant_joined.connect(self.on_participant_joined)
        session.on_participants_ready_changed.connect(self.on_participants_ready_changed)
        session.on_start.connect(self.on_start)
        session.on_stop.connect(self.on_stop)

    def setupUI(self):
        main_panel_layout = QVBoxLayout(self)

        details_panel = QGroupBox(self)
        main_panel_layout.addWidget(details_panel)
        details_panel_layout = QGridLayout(details_panel)
        details_panel.setTitle('Session details')

        id_lbl = QLabel(details_panel)
        details_panel_layout.addWidget(id_lbl, 0, 0)
        id_lbl.setText('ID:')

        self.id_txt = QLineEdit(details_panel)
        details_panel_layout.addWidget(self.id_txt, 0, 1)

        duration_lbl = QLabel(details_panel)
        details_panel_layout.addWidget(duration_lbl, 1, 0)
        duration_lbl.setText('Duration:')

        self.duration_txt = QLineEdit(details_panel)
        details_panel_layout.addWidget(self.duration_txt, 1, 1)

        status_lbl = QLabel(details_panel)
        details_panel_layout.addWidget(status_lbl, 2, 0)
        status_lbl.setText('Status:')

        self.status_txt = QLabel(details_panel)
        details_panel_layout.addWidget(self.status_txt, 2, 1)

        question_lbl = QLabel(details_panel)
        details_panel_layout.addWidget(question_lbl, 3, 0)
        question_lbl.setText("Question:")

        self.question_cbbox = QComboBox(details_panel)
        details_panel_layout.addWidget(self.question_cbbox, 3, 1)
        self.question_cbbox.addItem('<none>')
        self.question_cbbox.addItems([str(id) for id in AppContext.questions])
        self.question_cbbox.currentTextChanged.connect(self.on_question_changed)

        participants_ready_lbl = QLabel(details_panel)
        details_panel_layout.addWidget(participants_ready_lbl, 4, 0)
        participants_ready_lbl.setText("Ready:")

        self.participants_ready_txt = QLabel(details_panel)
        details_panel_layout.addWidget(self.participants_ready_txt, 4, 1)

        self.start_btn = QPushButton(self)
        main_panel_layout.addWidget(self.start_btn)
        self.start_btn.setText('Start')
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.on_start_btn_clicked)

        self.participants_list = QListWidget(self)
        main_panel_layout.addWidget(self.participants_list)
