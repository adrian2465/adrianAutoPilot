# Adrian Vrouwenvelder

import threading


def _rudder_val_from_arduino(v):
    """
    Normalize a rudder value received from the arduino
    Mapping: 0 <= v <= 1023 :: -1 <= rc <= 1
    :return: normalized value  -1 to 1
    """
    return v / 512 - 1


def _rudder_val_to_arduino(v):
    """
    Encode a normalized rudder to a rudder value to be sent to the arduino
    Mapping: -1 <= v <= 1 :: 0 <= rc <= 1023
    :return: 0 - 1023 rudder value to send to arduino
    """
    return int(512 * (v + 1))


def _motor_from_arduino(v):
    """
    Normalize a motor speed value received from the arduino
    Mapping: 0 <= v <= 255 :: 0 <= rc <= 1
    NOTE: No direction is included. 
    :return: normalized value 0 to 1
    """
    return v / 255


def _motor_to_arduino(v):
    """
    Encode a normalized motor value to a motor speed to be sent to arduino
    Mapping: 0 <= |v| <= 1 :: 0 <= rc <= 255
    :return: 0 - 255 motor speed to send to arduino
    """
    return int(255 * v)


# Called asynchronously from ArduinoInterface
def from_arduino(interface, msg):
    if msg.startswith('m='):  # Text message
        interface._messages = msg[2:]
    elif msg.startswith('r='):  # Right limit
        interface._stbd_limit = _rudder_val_from_arduino(int(msg[2:]))
    elif msg.startswith('l='):  # Left limit
        interface._port_limit = _rudder_val_from_arduino(int(msg[2:]))
    elif msg.startswith('p='):  # Rudder position magnitude
        interface._rudder_position = _rudder_val_from_arduino(int(msg[2:]))
    elif msg.startswith('x='):  # Rudder position exception (out of bounds)
        v = int(msg[2:])
        interface._rudder_fault = 1 if v == 2 else -1 if v == 1 else 0
    elif msg.startswith('s='):  # Motor speed
        interface._motor_speed = _motor_from_arduino(int(msg[2:]))
    elif msg.startswith('d='):  # Motor direction
        interface._direction = -1 if int(msg[2:]) == 1 else 1 if int(msg[2:]) == 2 else 0
    elif msg.startswith('c='):  # Clutch disposition
        interface._clutch_status = int(msg[2:])
    elif msg.startswith('i='):
        interface._status_interval = int(msg[2:])
    elif msg.startswith('e='):
        interface._echo_status = int(msg[2:])
    else:
        print(f"Unsupported message {msg}")
        interface._messages = f"Unsupported message `{msg}`"


class ArduinoInterface():
    def __init__(self):
        self._monitor_thread = threading.Thread(target=self.serial_monitor)
        self._monitor_thread.daemon = True
        self._check_interval = 0.2
        self._status_interval = 1000
        self._running: bool = False

        self._messages = ""
        self._port_limit = -1
        self._stbd_limit = 1
        self._rudder_position = 0
        self._rudder_fault = 0
        self._motor_speed = 0
        self._direction = 0
        self._clutch_status = 0
        self._echo_status = 0

    def start(self):
        self._running = True
        self._monitor_thread.start()

    def stop(self):
        self.set_motor_speed(0.0)
        self.set_status(0)
        self._running = False

    @property
    def check_interval_s(self):
        """
        Seconds between polling the arduino.
        """
        return self._check_interval

    @check_interval_s.setter
    def check_interval_s(self, i):
        self._check_interval = i

    def is_running(self) -> bool:
        """
        True if Web Server App has not been terminated.
        """
        return self._running

    def get_message(self) -> str:
        """
        Message from arduino
        """
        return "Online" if self._messages == "REBOOTED" else self._messages

    def get_rudder_limits(self):
        """
        At tuple (port, stbd) representing Port and Starboard Rudder limits.
        Each limit is normalized to range from -1 <= limit <= 1.
        """
        return self._port_limit, self._stbd_limit

    def set_rudder_limits(self, port_limit, stbd_limit):
        self.write(f"l{_rudder_val_to_arduino(port_limit):04}")
        self.write(f"r{_rudder_val_to_arduino(stbd_limit):04}")

    def get_rudder(self) -> int:
        """
        Rudder position. Sensed by Arduino. Not settable - to move rudder, operate the motor.
        Range is-1 <= rudder_position <= 1, where neg is to port, pos is to starboard.
        """
        return self._rudder_position

    def get_rudder_fault(self):
        """
        Rudder exceeded stops. Fault. Sent by Arduino. Read-only. Clears when rudder is back within specs.
        Value is 0 if no fault, -1 if rudder exceeded to port, 1 if rudder exceeded to starboard.
        """
        return self._rudder_fault

    def get_motor_speed(self):
        """
        Motor Speed: -1 <= speed <= 1.  -1 is to port. 1 is to starboard.
        """
        return self._motor_speed * self._direction

    def set_motor_speed(self, motor_speed):
        """
        Motor Speed: -1 <= speed <= 1.  -1 is to port. 1 is to starboard.
        Internally, also sets direction.
        """
        direction = 1 if motor_speed > 0 else -1 if motor_speed < 0 else 0
        motor_speed = abs(motor_speed)
        self.write(f"d{1 if direction < -0 else 2 if direction > 0 else 0}")
        self.write(f"s{_motor_to_arduino(motor_speed):03}")

    def get_status(self) -> int:
        """
        Status of autopilot.
        0 = disengaged, 1 = engaged
        """
        return self._clutch_status

    def set_status(self, status: int):
        self.write(f"c{status}")

    def get_status_interval_ms(self):
        """
        Milliseconds between status reports from Arduino. 4 digit int. 0 <= interval <= 9999
        """
        return self._status_interval

    def set_status_interval_ms(self, interval: int):
        self.write(f"i{interval:04}")

    def get_echo_status(self):
        return self._echo_status

    def set_echo_status(self, status: int):
        self.write(f"e{status:01}")
    # override this
    def serial_monitor(self) -> None: pass

    # override this
    def write(self, msg: str) -> None: pass


# override factory method
def get_interface():
    return ArduinoInterface()
