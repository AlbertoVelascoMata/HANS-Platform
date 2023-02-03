import json
from typing import List
from time import sleep

import paho.mqtt.client as mqtt
import requests
from collections import namedtuple

API_URL = 'http://localhost:5000'
MQTT_URL = 'ws://localhost:1883'



Action = namedtuple('Action', ['func', 'args'])

def request_join_session(session_id):
    print("> Trying to join session")
    res = requests.post(f"{API_URL}/api/session/{session_id}/participants", json={
        'user': 'test.user'
    })
    print(f"{res.status_code}: {res.text}")
    action_queue.append(Action(get_session_info, (session_id,)))

def get_session_info(session_id):
    print("> Retrieving session info")
    res = requests.get(f"{API_URL}/api/session/{session_id}")
    print(f"{res.status_code}: {res.text}")
    data = res.json()
    action_queue.append(Action(subscribe_to_session_control, (session_id,)))
    if data['status'] == 'starting':
        action_queue.append(Action(get_question_info, (data['question_id'],)))

def subscribe_to_session_control(session_id):
    print("> Subscribing to control topic")
    mqtt_client.subscribe(f'swarm/session/{session_id}/control')

def on_message(client, obj, msg):
    print(f"[MQTT] {msg.topic}: {msg.payload}")

    if msg.topic == 'swarm/session/1/control':
        data = json.loads(msg.payload)
        if data['type'] == 'setup':
            action_queue.append(Action(get_question_info, (data['question_id'],)))
        elif data['type'] == 'start':
            pass

def get_question_info(question_id):
    print("> Retrieving question details")
    res = requests.get(f"{API_URL}/api/question/{question_id}")
    print(f"{res.status_code}: {res.text}")
    #data = res.json()
    action_queue.append(Action(notify_client_ready, (1,)))

def notify_client_ready(session_id):
    mqtt_client.publish(f'swarm/session/{session_id}/control', json.dumps({
        'type': 'ready'
    }))

if __name__ == '__main__':
    

    mqtt_client = mqtt.Client(transport='websockets')
    mqtt_client.on_message = on_message
    mqtt_client.ws_set_options(path='/')
    mqtt_client.connect('localhost', 1883, 60)
    mqtt_client.loop_start()

    action_queue: List[Action] = []
    action_queue.append(Action(request_join_session, (1,)))

    try:
        while True:
            try:
                action = action_queue.pop(0)
                action.func(*action.args)
            except IndexError:
                sleep(.5)
    except KeyboardInterrupt:
        print("[Ctrl+C] Exit")
        mqtt_client.loop_stop()
