## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
## April 2023

from modules.direction import normalize
from modules.sensor import Sensor
from modules.status import DISABLED as STATUS_DISABLED, ENABLED as STATUS_ENABLED

from modules.arduinoInterface import ArduinoInterface
from modules.arduinoSerialInterface import getInterface as getArduinoInterface
from anglemath import calculate_angle_difference, normalize_angle

import threading
import time
from pid_controller import PID

class Brain:

    def __init__(self, config):
        self._course = 0
        self._sensor = Sensor(config)
        self._arduino_interface: ArduinoInterface = None
        self._brain_thread = threading.Thread(target=self.daemon)
        self._brain_thread.daemon = True
        self._check_interval = 1.0/60  # NOTE: IMU data refresh rate is 400kHz on i2c interface (so smallest interval = 1/400000)
        self._is_running = True
        self._config = config
        self._course_difference_theshold = 2  # TODO Make this adjustable based on sea state
        self._controller = PID(self.config.get_P_gain(), self.config.get_I_gain(), self.config.get_D_gain(), self.config.get_sampling_interval_ms())

    def get_messages(self):
        return self._arduino_interface.get_messages()

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

    def get_heel(self) -> int:
        return self._sensor.get_heel_angle()

    def set_status(self, status):
        self._arduino_interface.set_status(1 if status == STATUS_ENABLED else 0)

    def get_status(self) -> str:
        return STATUS_ENABLED if self._arduino_interface.get_status() == 1 else STATUS_DISABLED

    def adjust_course(self, delta: int) -> int:
        self._course = normalize(self._course + delta)
        self.controller.set_target_value(self._course)

    def start(self):
        self._running = True
        self._brain_thread.start()

    def stop(self):
       self._running = False
       self._arduino_interface.stop()
       print("INFO: Brain stopped")

    def daemon(self):
        print("INFO: Brain running")
        while (self._is_running):
            ##########################  FIX THIS vvvv
            if self._arduino_interface.get_status() == 1:
                rudder_adjustment = self.controller.output(self, self.get_heading())
                # TODO LEFT OFF HERE Try this code.
                self._arduino_interface.set_motor_direction(1 if rudder_adjustment > 0 else -1)
                self._arduino_interface.set_motor_speed(abs(rudder_adjustment))
                #  boat.request_rudder_angle(self.controller.compute_output(process_value=boat.sensor.get_heading()))
                # timestamp = time.time() - start_time

            time.sleep(0.1)
        ##########################  FIX THIS ^^^
        print("INFO: Brain exited")

def getInstance(config):
    b = Brain(config)
    arduino_interface = getArduinoInterface()
    b.set_arduino_interface(arduino_interface)
    arduino_interface.start()  # Create monitor and writer.
    return b


if __name__ == "__main__":
    brain = getInstance()
    i = 0
    print("INFO: echo messages to /tmp/fromArduino.txt to simulate sending messages from Arduino")
    while True:
        i = i + 1
        print(f"Brain cycle {i}")
        print(f"messages {brain.get_messages()}")
        time.sleep(5)