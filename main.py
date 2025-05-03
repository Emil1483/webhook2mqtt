import logging
import os
import traceback
from flask import Flask, request

from webhook2mqtt.setup_logging import setup_logging
from webhook2mqtt.MQTTWrapper import MQTTWrapper

app = Flask(__name__)


def catch_all(path=""):
    logging.info(
        f"Received request: Method: {request.method}. Path: {path}. Data: {request.data}"
    )

    try:

        host = os.getenv("MQTT_HOST", "localhost")
        port = int(os.getenv("MQTT_PORT", 1883))
        username = os.getenv("MQTT_USERNAME", None)
        password = os.getenv("MQTT_PASSWORD", None)

        with MQTTWrapper(
            host=host,
            port=port,
            client_id="webhook2mqtt",
            username=username,
            password=password,
        ) as mqtt:
            mqtt.client.publish(path, payload=request.data)
        return "ok"

    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(f"Error processing request: {e}")
        return "error", 500


for rule in ["/", "/<path:path>"]:
    app.add_url_rule(
        rule,
        endpoint=rule,
        view_func=catch_all,
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    )

if __name__ == "__main__":
    setup_logging(level=logging.DEBUG)
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=DEBUG)
