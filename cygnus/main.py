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

    def get_data(self) -> str:
        """
        Returns the driver status as a JSON containing the keys
        status, orientation, hostname, and enabled
        """
        return json.dumps(self.device.get_data())

    def get_serial_ports(self):
        """
        Get the available serial ports to show to the user
        """
        return json.dumps(self.device.get_serial_ports())

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

    def set_material(self, material, soundvelocity) -> bool:
        """
        Sets material and sound velocity
        """
        return self.device.set_material(unquote(material), soundvelocity) 

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

    @app.route("/get_data")
    def get_data():
        return api.get_data()

    @app.route("/get_serial_ports")
    def get_serial_ports():
        return api.get_serial_ports()

    @app.route("/enable/<enable>")
    def set_enabled(enable: str):
        return str(api.set_enabled(enable))

    @app.route("/setserialport/<path:serialport>")
    def set_serial_port(serialport):
        return str(api.set_serial_port(serialport))

    @app.route("/setbaud/<int:baud>")
    def set_baud(baud: int):
        return str(api.set_baud(baud))

    @app.route("/setmaterial/<material>/<int:soundvelocity>")
    def set_material(material, soundvelocity):
        return str(api.set_material(material, soundvelocity))

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
    app.run(host="0.0.0.0", port=8000)
