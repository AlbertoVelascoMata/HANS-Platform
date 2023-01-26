from argparse import Namespace
from api import ServerAPI
from mqtt import BrokerWrapper, Subscriber

class AppContext:
    args = Namespace(
        mqtt_port=1883,
        api_port=5000,
    )

    mqtt_broker = None
    mqtt_session_sub = None

    api_service = None

    @staticmethod
    def start_services(on_start_cb=None):
        print("Starting services")
        AppContext.mqtt_broker = BrokerWrapper('localhost', AppContext.args.mqtt_port)
        AppContext.mqtt_broker.on_start = on_start_cb
        AppContext.mqtt_broker.start()

        AppContext.mqtt_session_sub = Subscriber("swarm/session/#", 'localhost', AppContext.args.mqtt_port)
        AppContext.mqtt_session_sub.start()

        AppContext.api_service = ServerAPI(port=AppContext.args.api_port)
        AppContext.api_service.on_start = on_start_cb
        AppContext.api_service.start()

        print("Services up and running")

    @staticmethod
    def stop_services():
        if AppContext.mqtt_broker:
            AppContext.mqtt_broker.stop()
        
        if AppContext.mqtt_session_sub:
            AppContext.mqtt_session_sub.shutdown()
        
        if AppContext.api_service:
            AppContext.api_service.shutdown()
