from dataclasses import dataclass
import json
from typing import Callable, List
from time import sleep
from enum import Enum
from argparse import ArgumentParser

import paho.mqtt.client as mqtt
import requests
from collections import namedtuple

API_URL = 'http://localhost:5000'
MQTT_URL = 'ws://localhost:1883'

@dataclass
class Action:
    func: Callable[..., bool]
    args: tuple = ()

action_queue: List[Action] = []


class SessionStatus(Enum):
    WAITING = 'waiting'     # Waiting for clients to join
    ACTIVE = 'active'     # The Swarm Session is active (answering a question)

class State:
    continue_after_stop = False
    session_id = None
    session_status = SessionStatus.WAITING
    participant_id = None
    question = None

def request_join_session(username, session_id) -> bool:
    print(f"> Trying to join session (user={username}, id={session_id})")
    res = requests.post(f"{API_URL}/api/session/{session_id}/participants", json={'user': username})
    print(f"\t[{res.status_code}] {res.text}")
    if res.status_code != 200:
        return False

    State.session_id = session_id
    State.participant_id = res.json()['id']
    action_queue.append(Action(get_session_info))
    return True

def get_session_info() -> bool:
    print(f"> Retrieving session info (id={State.session_id})")
    res = requests.get(f"{API_URL}/api/session/{State.session_id}")
    print(f"\t[{res.status_code}] {res.text}")
    if res.status_code != 200:
        return False

    session_info = res.json()
    action_queue.append(Action(subscribe_to_session_control))

    if session_info['question_id'] is not None:
        action_queue.append(Action(get_question_info, (session_info['question_id'],)))
    return True

def subscribe_to_session_control() -> bool:
    print(f"> Subscribing to control topic (session={State.session_id})")
    mqtt_client.subscribe([
        (f'swarm/session/{State.session_id}/control', 0),
        (f'swarm/session/{State.session_id}/updates/+', 0)
    ])
    return True

def on_message(client, obj, msg):
    print(f"[MQTT] {msg.topic}: {msg.payload}")

    topic_data = msg.topic.split('/', 4)
    if (
        len(topic_data) < 4
        or topic_data[0] != 'swarm'
        or topic_data[1] != 'session'
        or not topic_data[2].isdigit()
    ):
        print(f"* ERROR: Invalid topic '{msg.topic}'")
        return

    session_id = int(topic_data[2])
    if session_id != State.session_id:
        print(f"* WARNING: Unknown session ID '{session_id}'")
        return
    
    if topic_data[3] == 'control':
        if len(topic_data) > 4:
            print("* WARNING: Participants should not receive other participants control messages")
            return
        
        payload = json.loads(msg.payload)
        if payload['type'] == 'setup':
            action_queue.append(Action(get_question_info, (payload['question_id'],)))
        elif payload['type'] == 'start':
            State.session_status = SessionStatus.ACTIVE
            action_queue.append(Action(send_position_update))
        elif payload['type'] == 'stop':
            State.session_status = SessionStatus.WAITING
            State.question = None
    
    elif topic_data[3] == 'updates':
        if len(topic_data) != 5:
            print("* WARNING: An update was received in a non-participant-specific topic")
            return
        
        participant_id = int(topic_data[4])
        if participant_id == State.participant_id:
            print("\tSelf update discarded")
            return
        payload = json.loads(msg.payload)
        # TODO: Handle other participants updates

def get_question_info(question_id) -> bool:
    print(f"> Retrieving question details (id={question_id})")
    res = requests.get(f"{API_URL}/api/question/{question_id}")
    print(f"\t[{res.status_code}] {res.text}")
    if res.status_code != 200:
        return False

    State.question = res.json()
    action_queue.append(Action(notify_client_ready))
    return True

def notify_client_ready() -> bool:
    print(f"> Notifying participant READY (session={State.session_id}, participant={State.participant_id})")
    mqtt_client.publish(f'swarm/session/{State.session_id}/control/{State.participant_id}', json.dumps({'type': 'ready'}))
    return True

def send_position_update() -> bool:
    if State.session_status != SessionStatus.ACTIVE:
        print(f"> Stopping continous position updates")
        return State.continue_after_stop

    print(f"> Sending POSITION UPDATE (session={State.session_id}, participant={State.participant_id}, question={State.question['id'] if State.question else None})")
    mqtt_client.publish(f'swarm/session/{State.session_id}/updates/{State.participant_id}', json.dumps({
        'data': {'position': [0,0,0,0,0]}
    }))
    sleep(1)
    action_queue.append(Action(send_position_update))
    return True

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-s', '--session', dest='session_id', type=int, help="Session ID (default: 1)", default=1)
    parser.add_argument('-u', '--user', dest='username', help="Username (default: 'test.user1')", default='test.user1')
    parser.add_argument('-c', '--continue', dest='continue_after_stop', action='store_true', help="Continue running after a successful session")
    args = parser.parse_args()

    State.continue_after_stop = args.continue_after_stop

    mqtt_client = mqtt.Client(transport='websockets')
    mqtt_client.on_message = on_message
    mqtt_client.ws_set_options(path='/')
    mqtt_client.connect('localhost', 1883, 60)
    mqtt_client.loop_start()

    action_queue.append(Action(request_join_session, (args.username, args.session_id)))

    try:
        while True:
            try:
                action = action_queue.pop(0)
                success = action.func(*action.args)
                if not success:
                    break
            except IndexError:
                sleep(.5)
    except KeyboardInterrupt:
        print("[Ctrl+C] Exit")
    finally:
        mqtt_client.loop_stop()
