import subprocess
from pathlib import Path
from threading import Thread
from typing import Callable, Dict

import paho.mqtt.client as mqtt
from paho.mqtt.client import CONNACK_ACCEPTED, MQTT_ERR_SUCCESS
from abc import ABC, abstractmethod
MOSQUITTO_PATH = "mosquitto"

class MQTTClient(ABC):
    @abstractmethod
    def connection_handler(self, connected: bool, reason: int) -> None: ...

    def __init__(self, host='localhost', port=1883):
        self.host = host
        self.port = port
        self.connected = False
        self.pending_subscriptions: Dict[int, Callable[[bool], None]] = {}
        self.client = mqtt.Client(transport="websockets")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe
        self.client.ws_set_options(path="/")

    def start(self):
        self.client.connect_async(self.host, self.port, 60)
        self.client.loop_start()

    def shutdown(self):
        self.client.loop_stop()

    def on_connect(self, client, obj, flags, rc):
        self.connected = rc == CONNACK_ACCEPTED
        self.connection_handler(self.connected, rc)

    def on_disconnect(self, client, obj, rc):
        self.connected = False
        self.connection_handler(False, rc)

    def on_subscribe(self, client, obj, message_id, granted_qos):
        if message_id not in self.pending_subscriptions:
            return
        self.pending_subscriptions[message_id](True)

    def subscribe(self, topic, callback: Callable[[bool], None] = None):
        result, message_id = self.client.subscribe(topic)
        if callback:
            if result == MQTT_ERR_SUCCESS:
                self.pending_subscriptions[message_id] = callback
            else:
                callback(False)

    def publish_sync(self, topic, msg, callback: Callable[[bool], None] = None):
        msg_handle = self.client.publish(topic, msg)
        msg_handle.wait_for_publish()
        if callback: callback(True) # TODO: Send false if message could not be queued

    def publish(self, topic, msg, post_callback=None):
        Thread(
            target=self.publish_sync,
            args=(topic, msg, post_callback),
            daemon=True
        ).start()

class BrokerWrapper:
    def __init__(self, host, port=9001):
        self.port = port
        self.thread = None
        self.process = None

        self.on_start = None
        self.on_stop = None

    @property
    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def _monitor(self, stream, header="[mosquitto]"):
        for line in iter(stream.readline, b''):
            print(header, line.decode('utf-8', errors='replace'), end='', flush=True)
        print(f"{header} Stream '{stream.name}' closed")
        if callable(self.on_stop): self.on_stop()

    def start(self):
        tmp_file = Path('tmp/mosquitto.conf')
        tmp_file.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp_file, 'w') as f:
            f.write(f"listener 9002\n")
            f.write("protocol mqtt\n")
            f.write('\n')
            f.write(f"listener {self.port}\n")
            f.write("protocol websockets\n")
            f.write("allow_anonymous true\n")

        self.process = subprocess.Popen([MOSQUITTO_PATH, '-v', '-c', tmp_file],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        self.stdout_monitor = Thread(target=self._monitor, args=(self.process.stdout, "[mosquitto-stdout]"), daemon=True)
        self.stdout_monitor.start()
        self.stderr_monitor = Thread(target=self._monitor, args=(self.process.stderr, "[mosquitto-stderr]"), daemon=True)
        self.stderr_monitor.start()

        if callable(self.on_start): self.on_start()

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        if self.stdout_monitor is not None:
            self.stdout_monitor.join()
            self.stdout_monitor = None
        if self.stderr_monitor is not None:
            self.stderr_monitor.join()
            self.stderr_monitor = None

        return self.process.poll()
