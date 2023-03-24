## Adrian Vrouwenvelder
## December 1, 2022
## March 2023

import threading
import time
from modules.status import ENABLED as STATUS_ENABLED, DISABLED as STATUS_DISABLED

# Called asynchronously from ArduinoInterface
def from_arduino(interface, msg):
    if msg.startswith('m='):  # Text message
        interface._messages = msg[2:]
    elif msg.startswith('r='):  # Right limit
        interface._stbd_limit = int(msg[2:])
    elif msg.startswith('l='):  # Left limit
        interface._port_limit = int(msg[2:])
    elif msg.startswith('s='):  # Motor speed
        interface._motor_speed = int(msg[2:])
    elif msg.startswith('d='):  # Motor direction
        interface._motor_direction = int(msg[2:])
    elif msg.startswith('p='):  # Rudder position magnitude
        interface._rudder_position = int(msg[2:])
    elif msg.startswith('x='):  # Rudder position direction
        interface._rudder_direction = int(msg[2:])
    elif msg.startswith('c='):  # Rudder position direction
        interface._clutch_status = int(msg[2:])
    else:
        print(f"Unsupported message {msg}")
        interface._messages = f"Unsupported message `{msg}`"

# Private
class ArduinoInterface():
    def __init__(self):
        self._monitor_thread = threading.Thread(target=self.serial_monitor)
        self._monitor_thread.daemon = True
        self._check_interval = 1
        self._running = False

        self._status = STATUS_DISABLED
        self._messages = ""
        self._rudder_position = 127
        self._rudder_direction = 0
        self._max_port_limit = 127
        self._max_stbd_limit = 127
        self._port_limit = self._max_port_limit
        self._stbd_limit = self._max_stbd_limit
        self._motor_speed = 0
        self._motor_direction = 0
        self._clutch_status = 0

    def start(self):
        self._running = True
        self._monitor_thread.start()

    def stop(self):
        self._running = False

    # Seconds between polling for messages. Seconds between loops in Arduino monitor
    def get_check_interval(self):
        return self._check_interval

    def is_running(self):
        return self._running

    # Status: 0 = disengaged, 1 = engaged
    def get_status(self) -> int:
        return self._clutch_status

    def set_status(self, status: int):
        self.write(f"c{status}")

    # Speed: 0 <= speed <= 255
    def set_motor_speed(self, speed: int):
        self.write(f"s{speed:03}")

    def get_motor_speed(self):
        return self._motor_speed

    # Direction: 0 neither. 1 = left. 2 = right.
    def set_motor_direction(self, motor_direction: int):
        self.write(f"d{motor_direction}")

    def get_motor_direction(self):
        return self._motor_direction

    def get_messages(self) -> str:
        return self._messages

    # 4 digit number whose range is determined by arduino value for rudder sensor at rudder limit
    def set_port_limit(self, port_limit: int):
        self.write(f"l{port_limit:04}")

    # 4 digit number whose range is determined by arduino value for rudder sensor at rudder limit
    def get_port_limit(self):
        return self._port_limit

    # 4 digit number whose range is determined by arduino value for rudder sensor at rudder limit
    def set_stbd_limit(self, stbd_limit: int):
        self.write(f"r{stbd_limit:04}")

    # 4 digit number whose range is determined by arduino value for rudder sensor at rudder limit
    def get_stbd_limit(self):
        return self._stbd_limit

    def set_status_interval(self, interval: int):
        self.write(f"i{interval:04}")

    # Rudder position. Cannot be set. Determined by rudder angle sensor.
    def get_rudder_position(self):
        return self._rudder_position

    # Rudder Direction: 0 = neither. 1 = Left. 2 = Right. Cannot be set. Determined by rudder angle sensor.
    def get_rudder_direction(self):
        return self._rudder_direction

    #override this
    def serial_monitor(self) -> str:
        # Implement this
        k = 0
        while True:
            from_arduino(self, msg=f"publishing {k}")
            k = k + 1
            time.sleep(1)

    #override this
    def write(self, msg: str) -> None:
        print(f"ArduinoInterface.write({msg})")


#override factory method
def getInterface():
    return ArduinoInterface()

################################################################################
# For testing and exemplification
def testBrain():

    arduino = getInterface()  # Create monitor and writer.
    arduino.start()  # Start monitor thread
    k = 0
    while k < 5:
        time.sleep(4)
        arduino.write(f"{k}")
        k = k + 1
    print("Stopped.")

if __name__ == "__main__":
    testBrain()
    
#Brain Received 'publishing 0'
#Brain Received 'publishing 1'
#Brain Received 'publishing 2'
#Brain Received 'publishing 3'
#ArduinoInterface.write(0)
#Brain Received 'publishing 4'
#Brain Received 'publishing 5'
#Brain Received 'publishing 6'
#Brain Received 'publishing 7'
#ArduinoInterface.write(1)
#Brain Received 'publishing 8'
#Brain Received 'publishing 9'
#Brain Received 'publishing 10'
#Brain Received 'publishing 11'
#ArduinoInterface.write(2)
#Brain Received 'publishing 12'
