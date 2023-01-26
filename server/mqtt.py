import subprocess
from pathlib import Path
from threading import Thread

import paho.mqtt.client as mqtt

MOSQUITTO_PATH = "mosquitto"

'''
def publish(client):
    sleep(3)
    client.publish('swarm/session/2', 'hello')
    print("message sent")
#t = Thread(target=publish, args=(subscriber.client,), daemon=True)
#t.start()
'''

class Subscriber:
    def on_connect(self, client, obj, flags, rc):
        print("rc: "+str(rc))

    def on_message(self, client, obj, msg):
        print(f"{msg.topic}: {msg.payload}")

    def on_publish(self, client, obj, mid):
        print("mid: "+str(mid))

    def on_subscribe(self, client, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, client, obj, level, string):
        print(string)

    def __init__(self, topic, host='localhost', port=1883):
        self.client = mqtt.Client(transport="websockets")
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_subscribe = self.on_subscribe
        self.client.ws_set_options(path="/")
        self.client.connect(host, port, 60)
        self.client.subscribe(topic, 0)

    def start(self):
        self.client.loop_start()
    
    def shutdown(self):
        self.client.loop_stop()

class BrokerWrapper:
    def __init__(self, host, port=1883):
        self.port = port
        self.thread = None
        self.process = None

        self.on_start = None

    @property
    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def _monitor(self, stream):
        for line in iter(stream.readline, b''):
            print("[mosquitto]", line.decode('utf-8', errors='replace'), end='', flush=True)
        print(f"[mosquitto] Stream '{stream.name}' closed")

    def start(self):
        tmp_file = Path('tmp/mosquitto.conf')
        tmp_file.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp_file, 'w') as f:
            f.write(f"listener {self.port}\n")
            f.write("protocol websockets\n")
            f.write("allow_anonymous true\n")
            #listener 1883
            #protocol mqtt
            #
            #listener 9001
            #protocol websockets

        self.process = subprocess.Popen([MOSQUITTO_PATH, '-v', '-c', tmp_file],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
        self.stdout_monitor = Thread(target=self._monitor, args=(self.process.stdout,), daemon=True)
        self.stdout_monitor.start()
        self.stderr_monitor = Thread(target=self._monitor, args=(self.process.stderr,), daemon=True)
        self.stderr_monitor.start()

        if callable(self.on_start): self.on_start(self)

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
        if self.stdout_monitor is not None:
            self.stdout_monitor.join()
        if self.stderr_monitor is not None:
            self.stderr_monitor.join()

        return self.process.poll()
