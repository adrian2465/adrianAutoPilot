## Adrian Vrouwenvelder
## December 1, 2022
## March 2023

from modules.direction import normalize
from modules.sensor import Sensor
from modules.status import DISABLED as STATUS_DISABLED, ENABLED as STATUS_ENABLED

from modules.arduinoInterface import ArduinoInterface
from modules.arduinoSerialInterface import getInterface as getArduinoInterface

# from modules.arduinoFileInterface import getInterface as getArduinoInterface

import time


class Brain():

    def __init__(self):
        self._course = 0
        self._sensor = Sensor()
        self._arduino_interface: ArduinoInterface = None

    def get_messages(self):
        return self._arduino_interface.get_messages();

    def set_arduino_interface(self, interface: ArduinoInterface):
        self._arduino_interface = interface

    def get_arduino_interface(self) -> ArduinoInterface:
        return self._arduino_interface

    def set_course(self, course: int) -> int:
        self._course = normalize(course)

    def get_course(self) -> int:
        return self._course

    def get_heading(self) -> int:
        return self._sensor.get_heading()

    def set_status(self, status):
        self._arduino_interface.set_status(1 if status == STATUS_ENABLED else 0)

    def get_status(self) -> str:
        return STATUS_ENABLED if self._arduino_interface.get_status() == 1 else STATUS_DISABLED

    def adjust_course(self, delta: int) -> int:
        self._course = normalize(self._course + delta)

_brain: Brain


def getInstance():
    global _brain
    _brain = Brain()
    arduino_interface = getArduinoInterface()
    _brain.set_arduino_interface(arduino_interface)
    arduino_interface.start()  # Create monitor and writer.
    return _brain

# For exemplification and testing from the command line
def brain_cmdline():
    brain = getInstance()
    i = 0
    print("echo messages to /tmp/fromArduino.txt to simulate sending messages from Arduino")
    while True:
        i = i + 1
        print(f"Brain cycle {i}")
        print(f"messages {brain.get_messages()}")
        time.sleep(5)

if __name__ == "__main__":
    brain_cmdline()
