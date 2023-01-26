from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QVBoxLayout, QWidget, QLabel

from context import AppContext


class ServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

    def on_services_started(self, service):
        if 'broker' in service.__class__.__name__.lower():
            self.mqtt_status_lbl.setText('🟢 MQTT Broker')
        elif 'api' in service.__class__.__name__.lower():
            self.api_status_lbl.setText('🟢 HTTP API')

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(5000, lambda: AppContext.start_services(self.on_services_started))

    def setupUI(self):
        self.setWindowTitle("Swarm Platform - Coordinator")
        self.resize(300, 100)

        main_panel = QWidget(self)
        self.setCentralWidget(main_panel)
        main_panel_layout = QVBoxLayout(main_panel)

        self.mqtt_status_lbl = QLabel(main_panel)
        main_panel_layout.addWidget(self.mqtt_status_lbl)
        self.mqtt_status_lbl.setText('🔴 MQTT Broker')

        self.api_status_lbl = QLabel(main_panel)
        main_panel_layout.addWidget(self.api_status_lbl)
        self.api_status_lbl.setText('🔴 HTTP API')

        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)
    
    def shutdown(self):
        pass
