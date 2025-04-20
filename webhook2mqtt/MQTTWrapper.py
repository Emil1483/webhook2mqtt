from datetime import datetime
import threading
from typing import Any, Callable
import paho.mqtt.client as mqtt
from paho.mqtt.client import CallbackAPIVersion, Client, MQTTMessage

import logging


class MQTTDisconnectedError(Exception):
    pass


class MQTTConnectionFailedError(Exception):
    pass


class MQTTConnected(Exception):
    pass


class MQTTWrapper:
    def __init__(self, host: str, port=1883, keepalive=60, client_id: str = None):
        self.client = mqtt.Client(
            CallbackAPIVersion.VERSION2,
            protocol=mqtt.MQTTv311,
            client_id=client_id,
        )

        self.host = host
        self.port = port
        self.keepalive = keepalive

        self.disconnecting_flag = False

        self.topic_callbacks: dict[
            str, list[Callable[[Client, Any, MQTTMessage], None]]
        ] = {}

    def subscribe(
        self,
        topic: str,
        qos=0,
        options: mqtt.SubscribeOptions = None,
        properties: mqtt.Properties = None,
    ):

        @self.topic_callback(topic)
        def on_message(_, __, message: MQTTMessage):
            self.last_messages_at[message.topic] = datetime.now()
            if message.topic in self.topic_timeout_callbacks:
                for callback in self.topic_timeout_callbacks[message.topic]:
                    callback.clear_executed()

        self.client.subscribe(
            topic,
            qos=qos,
            options=options,
            properties=properties,
        )

    def topic_callback(self, topic: str):
        def wrapper(func):
            if topic not in self.topic_callbacks:
                self.topic_callbacks[topic] = []
            self.topic_callbacks[topic].append(func)

            @self.client.topic_callback(topic)
            def func_wrapper(client, userdata, message):
                for cb in self.topic_callbacks[topic]:
                    cb(client, userdata, message)

            return func

        return wrapper

    def connect(self):
        logging.debug(f"Connecting to MQTT broker at {self.host}:{self.port}")

        def on_connect(*args):
            logging.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            raise MQTTConnected()

        def on_connect_fail(*args):
            logging.error(
                f"Failed to connect to MQTT broker at {self.host}:{self.port}"
            )
            raise MQTTConnectionFailedError()

        def on_disconnect(_, *args):
            logging.warning(f"Disconnected from MQTT broker at {self.host}:{self.port}")

            if not self.disconnecting_flag:
                raise MQTTDisconnectedError(*args)

        self.client.on_connect = on_connect
        self.client.on_connect_fail = on_connect_fail
        self.client.on_disconnect = on_disconnect

        rc = self.client.connect(self.host, self.port, self.keepalive)
        if rc != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(
                f"Failed to connect to MQTT broker at {self.host}:{self.port}"
            )

        try:
            self.client.loop_forever()
        except MQTTConnected:
            self.client.on_connect = None
            self.client.on_connect_fail = None

    def disconnect(self):
        self.disconnecting_flag = True
        self._running = False
        try:
            if self.client._thread is not None:
                self.client.loop_stop()
            self.client.disconnect()
        finally:
            self.disconnecting_flag = False

    def __enter__(self):
        self.connect()
        self.client.loop_start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
