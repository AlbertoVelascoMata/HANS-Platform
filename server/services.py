from typing import Callable, Union
from context import AppContext
from api import ServerAPI
from mqtt import BrokerWrapper, Subscriber

def start_services(
    on_start_cb: Callable[[Union[BrokerWrapper, ServerAPI]], None]=None
):
    print("Starting services")
    AppContext.mqtt_broker = BrokerWrapper('localhost', AppContext.args.mqtt_port)
    if on_start_cb:
        AppContext.mqtt_broker.on_start = lambda: on_start_cb(AppContext.mqtt_broker)
    AppContext.mqtt_broker.start()

    AppContext.mqtt_session_sub = Subscriber("swarm/session/#", 'localhost', AppContext.args.mqtt_port)
    AppContext.mqtt_session_sub.start()

    AppContext.api_service = ServerAPI(port=AppContext.args.api_port)
    if on_start_cb:
        AppContext.api_service.on_start = lambda: on_start_cb(AppContext.api_service)
    AppContext.api_service.start()

    print("Services up and running")

def stop_services():
    if AppContext.mqtt_broker:
        AppContext.mqtt_broker.stop()
    
    if AppContext.mqtt_session_sub:
        AppContext.mqtt_session_sub.shutdown()
    
    if AppContext.api_service:
        AppContext.api_service.shutdown()