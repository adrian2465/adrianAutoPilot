## Adrian Vrouwenvelder
## December 1, 2022
from arduinoInterface import ArduinoInterface
from modules.direction import normalize
from modules.status import ENABLED as STATUS_ENABLED, DISABLED as STATUS_DISABLED
from modules.arduinoSerialInterface import getInterface

import time


class Brain():

    def __init__(self):
        self._status = STATUS_DISABLED
        self._course = 0
        self._messages = "Disabled"
        self._rudder_position = 127
        self._max_port_limit = 127
        self._max_stbd_limit = 127
        self._port_limit = self._max_port_limit
        self._stbd_limit = self._max_stbd_limit
        self._motor_speed = 0
        self._interface = None

    def exceeds_port(self, portRudder: int):
        # if _max_port_limit < _max_stbd_limit: 
        return False    # TODO - Coding exceeds_ functions.

    def exceeds_stbd(self, stbdRudder: int):
        return False    # TODO - Coding exceeds_ functions.

    def adjust_course(self, delta: int) -> int:
        self._course = normalize(self._course + delta)

    def set_course(self, course: int) -> int:
        self._course = normalize(course)

    def get_course(self) -> int:
        return self._course

    def get_messages(self) -> str:
        return self._messages

    def set_messages(self, messages:str) -> str:
        self._messages = messages

    def get_status(self) -> str:
        return STATUS_ENABLED if self._clutch_status == 1 else STATUS_DISABLED

    def set_status(self, status:str):
        self._clutch_status = 1 if status == STATUS_ENABLED else 0
        self._interface.write(f"C{self._clutch_status}".encode())

    def set_rudder_position(self, rudder_position: int):
        self._rudder_position = rudder_position

    def set_rudder_direction(self, rudder_direction: int):
        self._rudder_direction = rudder_direction

    def set_port_limit(self, port_limit: int):
        self._port_limit = port_limit

    def set_stbd_limit(self, stbd_limit: int):
        self._stbd_limit = stbd_limit

    def set_max_port_limit(self, port_limit: int):
        self._port_limit = port_limit

    def set_max_stbd_limit(self, stbd_limit: int):
        self._stbd_limit = stbd_limit

    def set_interface(self, interface: ArduinoInterface):
        self._interface = interface

_brain: Brain

# Called asynchronously from ArduinoInterface
def from_arduino(msg):
    global _brain
    # Put just enough processing here to communicate with brain loop.
    #  TODO Left off here. Parse messages from arduino.
    if msg.startswith('m'):  # Text message
        _brain._messages = int(msg[1:])
        _brain.set_messages(f"Messages = {_brain._messages}")
    elif msg.startswith('r'):  # Right limit
        _brain._stbd_limit = int(msg[1:])
        _brain.set_messages(f"Starboard limit = {_brain._stbd_limit}")
    elif msg.startswith('l'):  # Left limit
        _brain._port_limit = int(msg[1:])
        _brain.set_messages(f"Port limit = {_brain._port_limit}")
    elif msg.startswith('s'):  # Motor speed
        _brain._motor_speed = int(msg[1:])
        _brain.set_messages(f"Motor speed = {_brain._motor_speed}")
    elif msg.startswith('d'):  # Motor direction
        _brain._motor_direction = int(msg[1:])
        _brain.set_messages(f"Motor direction = {_brain._motor_direction}")
    elif msg.startswith('p'):  # Rudder position magnitude
        _brain._rudder_position = int(msg[1:])
        _brain.set_messages(f"Rudder position= {_brain._rudder_position}")
    elif msg.startswith('x'):  # Rudder position direction
        _brain._rudder_direction = int(msg[1:])
        _brain.set_messages(f"Rudder direction = {_brain._rudder_direction}")
    else:
        _brain.set_messages(f"Unsupported message {msg} from Arduino")

def getInstance():
    global _brain
    _brain = Brain()
    _brain.set_interface(getInterface())
    _brain._interface.setFromArduino(from_arduino)
    _brain._interface.start()  # Create monitor and writer.
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
