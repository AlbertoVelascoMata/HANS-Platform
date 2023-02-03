from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QGroupBox, QListWidget, QListWidgetItem, QLabel, QLineEdit, QPushButton

from context import AppContext, Session, Participant
import services


class SessionListItem(QListWidgetItem):
    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setText(f"Session {session.id}")


#class ParticipantWidget(QWidget):
#    def __init__(self,
#        username,
#        status=Participant.Status.JOINING,
#        parent=None
#    ):
#        super().__init__(parent)
#
#        main_layout = QHBoxLayout(self)
#        #self.setLayout(main_layout)
#
#        self.username_label = QLabel(self)
#        main_layout.addWidget(self.username_label)
#        self.username_label.setText(username)
#
#        self.status_label = QLabel(self)
#        main_layout.addWidget(self.status_label)
#        self.status_label.setText(status.value)


class ServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_session = None

    def on_services_started(self, service):
        if 'broker' in service.__class__.__name__.lower():
            self.mqtt_status_lbl.setText('🟢 MQTT Broker')
        elif 'api' in service.__class__.__name__.lower():
            self.api_status_lbl.setText('🟢 HTTP API')
            AppContext.api_service.on_participant_joined = self.on_participant_joined
            AppContext.api_service.on_session_created = self.on_session_created
            self.session_list_add_btn.setEnabled(True)

    def on_session_created(self, session):
        self.session_list.addItem(SessionListItem(session))

    def update_session_info(self, session):
        self.selected_session = session
        if session is None:
            self.session_info_panel.setHidden(True)
            return

        self.session_id_txt.setText(str(session.id))
        self.session_duration_txt.setText(str(session.duration))
        self.session_status_txt.setText(session.status.value)

        self.session_info_panel.setHidden(False)

    def on_add_session_clicked(self):
        session = Session()
        AppContext.sessions[session.id] = session
        self.on_session_created(session)

    def on_participant_joined(self, session, participant):
        if session == self.selected_session:
            #widget = ParticipantWidget(participant.username, participant.status)
            #item = QListWidgetItem(self.session_participants_list)
            #item.setSizeHint(widget.sizeHint())
            #self.session_participants_list.addItem(item)
            #self.session_participants_list.setItemWidget(item, widget)
            self.session_participants_list.addItem(participant.username)

    def session_start_clicked(self):
        self.selected_session.start()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, lambda: services.start_services(self.on_services_started))

    def setupUI(self):
        self.setWindowTitle("Swarm Platform - Coordinator")
        self.resize(800, 600)

        main_panel = QWidget(self)
        self.setCentralWidget(main_panel)
        main_panel_layout = QVBoxLayout(main_panel)

        session_panel = QWidget(main_panel)
        main_panel_layout.addWidget(session_panel)
        session_panel_layout = QHBoxLayout(session_panel)

        session_list_panel = QWidget(session_panel)
        session_panel_layout.addWidget(session_list_panel)
        session_list_panel_layout = QVBoxLayout(session_list_panel)

        self.session_list = QListWidget(session_list_panel)
        session_list_panel_layout.addWidget(self.session_list)
        self.session_list.itemClicked.connect(lambda item: self.update_session_info(item.session))

        self.session_list_add_btn = QPushButton(session_list_panel)
        session_list_panel_layout.addWidget(self.session_list_add_btn)
        self.session_list_add_btn.setText('New session')
        self.session_list_add_btn.setEnabled(False)
        self.session_list_add_btn.clicked.connect(self.on_add_session_clicked)

        self.session_info_panel = QWidget(session_panel)
        session_panel_layout.addWidget(self.session_info_panel)
        session_info_panel_layout = QVBoxLayout(self.session_info_panel)
        self.session_info_panel.setHidden(True)

        session_details_panel = QGroupBox(self.session_info_panel)
        session_info_panel_layout.addWidget(session_details_panel)
        session_details_panel_layout = QGridLayout(session_details_panel)
        session_details_panel.setTitle('Session details')

        session_id_lbl = QLabel(session_details_panel)
        session_details_panel_layout.addWidget(session_id_lbl, 0, 0)
        session_id_lbl.setText('ID:')

        self.session_id_txt = QLineEdit(session_details_panel)
        session_details_panel_layout.addWidget(self.session_id_txt, 0, 1)

        session_duration_lbl = QLabel(session_details_panel)
        session_details_panel_layout.addWidget(session_duration_lbl, 1, 0)
        session_duration_lbl.setText('Duration:')

        self.session_duration_txt = QLineEdit(session_details_panel)
        session_details_panel_layout.addWidget(self.session_duration_txt, 1, 1)

        session_status_lbl = QLabel(session_details_panel)
        session_details_panel_layout.addWidget(session_status_lbl, 2, 0)
        session_status_lbl.setText('Status:')

        self.session_status_txt = QLabel(session_details_panel)
        session_details_panel_layout.addWidget(self.session_status_txt, 2, 1)

        session_start_btn = QPushButton(self.session_info_panel)
        session_info_panel_layout.addWidget(session_start_btn)
        session_start_btn.setText('Start')
        session_start_btn.clicked.connect(self.session_start_clicked)

        self.session_participants_list = QListWidget(self.session_info_panel)
        session_info_panel_layout.addWidget(self.session_participants_list)
        

        

        services_status_panel = QWidget(main_panel)
        main_panel_layout.addWidget(services_status_panel)
        services_status_panel_layout = QVBoxLayout(services_status_panel)

        self.mqtt_status_lbl = QLabel(services_status_panel)
        services_status_panel_layout.addWidget(self.mqtt_status_lbl)
        self.mqtt_status_lbl.setText('🔴 MQTT Broker')

        self.api_status_lbl = QLabel(services_status_panel)
        services_status_panel_layout.addWidget(self.api_status_lbl)
        self.api_status_lbl.setText('🔴 HTTP API')

        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)
    
    def shutdown(self):
        services.stop_services()
