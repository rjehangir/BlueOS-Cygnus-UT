#!/usr/bin/env python3
"""
Driver for the Cygnus Thickness Gauge, a serial device with simple output
"""

import json

from flask import Flask, request
from urllib.parse import unquote

from cygnus import CygnusDriver

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path="/static", static_folder="static")
thread = None


class API:
    device = None

    def __init__(self, device: CygnusDriver):
        self.device = device

    def get_status(self) -> str:
        """
        Returns the driver status as a JSON containing the keys
        status, orientation, hostname, and enabled
        """
        return json.dumps(self.device.get_status())

    def set_serial_port(self, port) -> bool:
        """
        Sets the port info
        """
        return self.device.set_serial_port(unquote(port))

    def set_baud(self, baud) -> bool:
        """
        Sets the baud info
        """
        return self.device.set_baud(baud) 

    def set_enabled(self, enabled: str) -> bool:
        """
        Enables/Disables the DVL driver
        """
        if enabled in ["true", "false"]:
            return self.device.set_enabled(enabled == "true")
        return False 

    def set_sound_velocity(self, velocity) -> bool:
        """
        Sets the sound velocity
        """
        return self.device.set_sound_velocity(velocity) 

    def set_message_type(self, messagetype: str):
        self.device.set_should_send(messagetype)

    def save_log(self, log):
        return self.device.save_log(log)

    def load_log(self):
        return self.device.load_log()


if __name__ == "__main__":
    driver = CygnusDriver()
    api = API(driver)

    @app.route("/get_status")
    def get_status():
        return api.get_status()

    @app.route("/enable/<enable>")
    def set_enabled(enable: str):
        return str(api.set_enabled(enable))

    @app.route("/setserialport/<path:serialport>")
    def set_serial_port(serialport):
        return str(api.set_serial_port(serialport))

    @app.route("/setbaud/<int:baud>")
    def set_baud(baud: int):
        return str(api.set_baud(baud))

    @app.route('/savelog', methods=['POST'])
    def save_log():
        return api.save_log(request.get_json())

    @app.route('/loadlog')
    def load_log():
        return api.load_log()

    @app.route("/register_service")
    def register_service():
        return app.send_static_file("service.json")

    @app.route("/")
    def root():
        return app.send_static_file("index.html")

    driver.start()
    app.run(host="0.0.0.0", port=9001)
