from typing import Callable, Union
from context import AppContext
from api import ServerAPI
from mqtt import BrokerWrapper

def start_services(
    on_start_cb: Callable[[Union[BrokerWrapper, ServerAPI]], None]=None
):
    print("Starting services")
    AppContext.mqtt_broker = BrokerWrapper('localhost', AppContext.args.mqtt_port)
    if on_start_cb:
        AppContext.mqtt_broker.on_start = lambda: on_start_cb(AppContext.mqtt_broker)
    AppContext.mqtt_broker.start()

    AppContext.api_service = ServerAPI(port=AppContext.args.api_port)
    if on_start_cb:
        AppContext.api_service.on_start.connect(lambda: on_start_cb(AppContext.api_service))
    AppContext.api_service.start()

    print("Services up and running")

def stop_services():
    if AppContext.mqtt_broker:
        AppContext.mqtt_broker.stop()

    if AppContext.api_service:
        AppContext.api_service.shutdown()