## Adrian Vrouwenvelder
## December 1, 2022

from modules.direction import normalize
from modules.status import ENABLED as STATUS_ENABLED, DISABLED as STATUS_DISABLED
from modules.arduinoFileInterface import getInterface

import time


class Brain():

    def __init__(self):
        self._status = STATUS_DISABLED
        self._course = 0
        self._messages = "Disabled"
        self._rudder_position = 127
        self._clutch_status = 0
        self._max_port_limit = 127
        self._max_stbd_limit = 127
        self._port_limit = self._max_port_limit
        self._stbd_limit = self._max_stbd_limit

    def exceeds_port(self, portRudder: int):
        # if _max_port_limit < _max_stbd_limit: 
        return False    # LEFT OFF HERE - Coding exceeds_ functions.
    def adjustCourse(self, delta:int) -> int:
      self._course = normalize(self._course + delta)
    
    def setCourse(self, course:int) -> int:
      self._course = normalize(course)
    
    def getCourse(self) -> int:
      return self._course
    
    def getStatus(self) -> str:
      return self._status

    def getMessages(self) -> str:
      return self._messages

    def setMessages(self, messages:str) -> str:
        self._messages = messages

    def setStatus(self, status:str):
        self._status = status
        self._messages = status

    def set_rudder_position(self, rudder_position: int):
        self._rudder_position = rudder_position

    def set_clutch_status(self, clutch_status: int):
        self._clutch_status = clutch_status

    def set_port_limit(self, port_limit: int):
        self._port_limit = port_limit
        if exceeds_port(self._port_limit): self._port_limit = self._max_port_limit

    def set_stbd_limit(self, stbd_limit: int):
        self._stbd_limit = stbd_limit
        if exceeds_stbd(self._stbd_limit): self._stbd_limit = self._max_stbd_limit

    def set_max_port_limit(self, port_limit: int):
        self._port_limit = port_limit

    def set_max_stbd_limit(self, stbd_limit: int):
        self._stbd_limit = stbd_limit


_brain: Brain

# Called asynchronously from ArduinoInterface
def from_arduino(msg): 
    global _brain, _rudder_position, _clutch_status, _port_limit, _stbd_limit
    # Put just enough processing here to communicate with brain loop.
    if (msg.startswith('r')):
        _rudder_position = int(msg[1:4])
        _brain.setMessages(f"New rudder position: {_rudder_position}")
    elif (msg.startswith('c')):
        _clutch_status = int(msg[1:2])
        output = "Disabled" if clutch == 0 else "Enabled"
        _brain.setMessage(f"Clutch at {_clutch_status}")
    elif (msg.startswith('p')):
        _port_limit = int(msg[1:4])
        _brain.setMessage(f"Port limit = {_port_limit}")
    elif (msg.startswith('s')):
        _stbd_limit = int(msg[1:4])
        _brain.setMessage(f"Stbd limit = {_stbd_limit}")

def getInstance():
    global _brain
    _brain = Brain()
    interface = getInterface()
    interface.setFromArduino(from_arduino)
    interface.start() # Create monitor and writer.
    return _brain

# For exemplification and testing from the command line
def brain_cmdline():
    brain = getInstance()
    i = 0
    print("echo messages to /tmp/fromArduino.txt to simulate sending messages from Arduino")
    while True:
        i = i + 1
        print(f"Brain cycle {i}")
        print(f"messages {brain.getMessages()}")
        time.sleep(5)

if __name__ == "__main__":
    brain_cmdline()
