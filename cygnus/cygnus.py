"""
Code for integration of Waterlinked DVL A50 with Companion and ArduSub
"""
import json
import math
import os
import threading
import time
import random
import serial
import serial.tools.list_ports
from enum import Enum
from select import select
from typing import Any, Dict, List

from loguru import logger

from blueoshelper import request
from mavlink2resthelper import GPS_GLOBAL_ORIGIN_ID, Mavlink2RestHelper

# pylint: disable=too-many-instance-attributes
# pylint: disable=unspecified-encoding
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
class CygnusDriver(threading.Thread):
    """
    This driver opens the serial port and reads the sensor. 
    It makes it available to the REST API.
    """

    status = "Starting"
    version = ""
    mav = Mavlink2RestHelper()
    enabled = False
    serial_port = ""
    serial_ports = []
    baud = 2400
    timeout = 3  # timeout in seconds
    settings_path = os.path.join(os.path.expanduser("~"), ".config", "cygnus", "settings.json")
    log_path = os.path.join(os.path.expanduser("~"), ".config", "cygnus", "log.json")

    sound_velocity = 6400 # m/s
    resolution = 0 # 0 for low, 1 for high
    units = 0 # 0 for mm, 1 for inches
    reading_range = 0 # 0 for low range, 1 for high range
    echo_count = 0
    is_valid = False
    raw_thickness = 0.0
    thickness = 0.0

    def __init__(self) -> None:
        threading.Thread.__init__(self)
        self.ser = serial.Serial()

    def report_status(self, msg: str) -> None:
        self.status = msg
        logger.debug(msg)

    def get_serial_ports(self):
        valid_ports = []
        ports = serial.tools.list_ports.comports()

        for port in ports:
            if "/dev/ttyUSB" in port.device or "/dev/ttyACM" in port.device or "/dev/tty.usbserial" in port.device:
                valid_ports.append(port.device)

        return valid_ports

    def load_settings(self) -> None:
        """
        Load settings from .config/cygnus/settings.json
        """
        try:
            with open(self.settings_path) as settings:
                data = json.load(settings)
                logger.debug(data)
                self.enabled = data["enabled"]
                self.serial_port = data["port"]
                self.baud = data["baud"]
                logger.debug("Loaded settings: ", data)
        except FileNotFoundError:
            logger.warning("Settings file not found, using default.")
        except ValueError:
            logger.warning("File corrupted, using default settings.")
        except KeyError as error:
            logger.warning("key not found: ", error)
            logger.warning("using default instead")

    def save_settings(self) -> None:
        """
        Load settings from .config/cygnus/settings.json
        """

        def ensure_dir(file_path) -> None:
            """
            Helper to guarantee that the file path exists
            """
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)

        ensure_dir(self.settings_path)
        with open(self.settings_path, "w") as settings:
            settings.write(
                json.dumps(
                    {
                        "enabled": self.enabled,
                        "port": self.serial_port,
                        "baud": self.baud
                    }
                )
            )

    def save_log(self, log):
        def ensure_dir(file_path) -> None:
            """
            Helper to guarantee that the file path exists
            """
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)

        ensure_dir(self.log_path)
        with open(self.log_path, "w") as settings:
            settings.write(
                json.dumps(log)
            )
            return "Saved log data"
        return "Failed to save log data"

    def load_log(self):
        try:
            with open(self.log_path) as log:
                return json.load(log)
        except FileNotFoundError:
            logger.warning("Settings file not found, using default.")
        except ValueError:
            logger.warning("File corrupted, using default settings.")
        except KeyError as error:
            logger.warning("key not found: ", error)
            logger.warning("using default instead")
        return "Failed to remember logged data"

    def get_data(self) -> dict:
        """
        Returns a dict with the current data
        """
        return {
            "status": self.status,
            "enabled": self.enabled,
            "port": self.serial_port,
            "baud": self.baud,
            "resolution": self.resolution,
            "units": "mm",
            "echo_count": self.echo_count,
            "is_valid": self.is_valid,
            "raw_thickness": self.raw_thickness,
            "thickness": self.thickness
        }

    def setup_mavlink(self) -> None:
        """
        Sets up mavlink streamrates so we have the needed messages at the
        appropriate rates
        """
        self.report_status("Setting up MAVLink streams...")
        # we don't actually need anything in this example
        #self.mav.ensure_message_frequency("ATTITUDE", 30, 5)

    def wait_for_vehicle(self):
        """
        Waits for a valid heartbeat to Mavlink2Rest
        """
        self.report_status("Waiting for vehicle...")
        while not self.mav.get("/HEARTBEAT"):
            time.sleep(1)

    def set_serial_port(self, serial_port) -> bool:
        """
        Sets the serial port settings
        """
        self.serial_port = serial_port
        self.save_settings()
        self.connect()
        return True

    def set_baud(self, baud) -> bool:
        """
        Sets the serial baud settings
        """
        self.baud = baud
        self.save_settings()
        self.connect()
        return True

    def set_enabled(self, enable: bool) -> bool:
        """
        Enables/disables the driver
        """
        self.enabled = enable
        self.save_settings()
        return True

    def set_sound_velocity(self, velocity) -> bool:
        """
        Sets sound velocity
        """
        self.sound_velocity = velocity
        self.save_settings()
        return True

    def connect(self):
        """
        Waits for the device to show up at the designated serial port
        """
        self.status = f"Trying to connect to device at {self.serial_port}/{self.baud}"
        self.ser.port = self.serial_port
        self.ser.baudrate = self.baud
        self.ser.timeout = 1.0
        try:
            self.ser.open()
        except serial.SerialException as e:
            print("Serial port error:", str(e))
            self.report_status(f"Failed to open device at {self.serial_port}/{self.baud}.")
        if self.ser.is_open:
            self.report_status(f"Device connected at {self.serial_port}/{self.baud}.")
            return

    def reconnect(self):
        """
        attempt to reestablish connection
        """
        self.ser.close()
        time.sleep(1)
        self.connect()

    def fakeRead(self):
        self.resolution = 0
        self.units = 0
        self.reading_range = 0
        self.echo_count = 3
        self.is_valid = True
        self.raw_thickness = round(random.uniform(10.0, 15.0),2)
        return True
    
    def read(self):
        """
        Read the serial port to get status byte and measurement
        """
        while self.ser.is_open and time.time() - self.last_recv_time < self.timeout:
            byte = self.ser.read(1) # read bytes until starting byte is received
            if byte == b'\x01':
                status = self.ser.read(1)

                self.resolution = status[0] & 0b01000000 > 0
                self.units = status[0] & 0b00100000 > 0
                self.reading_range = status[0] & 0b00010000 > 0
                self.echo_count = (status[0] & 0b00001100) >> 2
                self.is_valid = not status[0] & 0b00000001

                # self.report_status(self.resolution) 
                # self.report_status(self.units) 
                # self.report_status(self.reading_range)
                # self.report_status(self.echo_count)  
                # self.report_status(self.is_valid) 

                if self.is_valid:
                    data = int(self.ser.read(4))

                    if self.units == 0: # metric, always
                        if self.resolution == 0: # low resolution
                            self.raw_thickness = data/10.0
                        else: # high resolution
                            if self.reading_range == 0: # low range
                                self.raw_thickness = data/100.0
                            else: # high range
                                self.raw_thickness = data/10.0
                    else:
                        self.report_status("Received measurement in inches, unsupported and unexpected.")
                else:
                    # just keep last valid measurement
                    pass
                
                self.ser.read(1) # read ending byte (0x17)
                self.last_recv_time = time.time()
                return True
        return False

    def process_measurement(self):
        """
        This uses speed of sound info to make a corrected measurement.
        """
        self.thickness = self.raw_thickness/6400*self.sound_velocity

    def run(self):
        self.load_settings()
        #self.wait_for_vehicle()
        #self.setup_mavlink()
        time.sleep(1)
        self.report_status("Running")
        self.last_recv_time = time.time()

        # Main loop
        while True:
            # Skip if driver is disabled
            if not self.enabled:
                time.sleep(1)
                continue

            connected = self.ser.is_open or self.serial_port == "Demo Mode"          

            if not connected:
                self.report_status("Restarting serial port")
                self.reconnect()
                time.sleep(0.003)
                continue

            # Read the next measurement or get a demo measurement
            success = False
            if self.serial_port == "Demo Mode":
                success = self.fakeRead()
            else:
                success = self.read()

            if not success:
                self.report_status("Read failure or timeout, restarting serial port")
                self.reconnect()
                continue

            self.status = "Running"

            # correct the data for speed of sound
            self.process_measurement()

            time.sleep(0.003)
        logger.error("Driver Quit! This should not happen.")
