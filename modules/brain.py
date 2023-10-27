## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
## April 2023
from modules.common.anglemath import normalize_angle
from modules.interfaces.boat_interface import BoatInterface
from modules.common.config import Config

import threading
import time
from modules.pid_controller import PID
from modules.common.file_logger import Logger

_log = Logger(config_path="brain", dest=None, who="brain")


class Brain:

    def __init__(self, cfg: Config, boat: BoatInterface):
        self._boat = boat
        self._brain_thread = threading.Thread(target=self.motor_manager_daemon)
        self._brain_thread.daemon = True
        self._boat_sampling_interval = int(cfg.boat["sampling_interval"])
        self._stop_requested = False
        self._controller = PID(cfg)
        self._rudder_tolerance = float(cfg.boat["rudder_tolerance"])
        self._target_course = None
        self._commanded_rudder = None
        self._course_tolerance_deg = float(cfg.boat['course_tolerance_deg'])

    def target_course(self):
        """Desired course for autopilot to steer"""
        return self._target_course

    def set_target_course(self, course):
        _log.debug(f"Setting target_course to {course}")
        self._target_course = normalize_angle(course)

    def adjust_course(self, delta):
        self.set_target_course(self._target_course + delta)

    def commanded_rudder(self):
        """Desired rudder angle. Range is 0 <= commanded_rudder <= 1"""
        return self._commanded_rudder

    def set_commanded_rudder(self, commanded_rudder):
        _log.debug(f"Setting commanded rudder to {'starboard' if commanded_rudder > 0 else 'port' if commanded_rudder < 0 else 'center'} ({commanded_rudder})")
        self._commanded_rudder = commanded_rudder

    def is_on_course(self):
        return abs(self._target_course - self._boat.heading()) <= self._course_tolerance_deg

    def is_clutch_engaged(self):
        return self._boat.is_clutch_engaged()

    def engage_autopilot(self):
        self._boat.engage_autopilot()

    def disengage_autopilot(self):
        self._boat.disengage_autopilot()

    def start(self):
        self._boat.start()  # Create monitor and writer.
        self._brain_thread.start()

    def stop(self):
        self._stop_requested = True
        self.disengage_autopilot()
        _log.info("Brain stop requested")

    def get_recommended_motor_direction(self):
        return 0 if not self.is_clutch_engaged()\
            else 0 if abs(self._commanded_rudder - self._boat.rudder()) <= self._rudder_tolerance \
            else 1 if (self._commanded_rudder > 0 and self._commanded_rudder > self._boat.rudder()) \
            else -1

    def motor_manager_daemon(self):
        # Brain should check on course, heading, and rudder, and compute a new commanded rudder based on that.
        # Brain also talks to the arduino (which is the hydraulic ram actuator) to effectuate changes

        _log.info(f"motor_manager_daemon started.")
        while not self._stop_requested:
            if self.is_clutch_engaged():
                _recommended_direction = self.get_recommended_motor_direction()
                _log.debug(f"boat rudder={self._boat.rudder()} "
                           f"commanded rudder={self.commanded_rudder()}  "
                           f"rudder diff={abs(self._boat.rudder() - self.commanded_rudder())}  "
                           f"tolerance={self._rudder_tolerance} "
                           f"recommended direction={_recommended_direction}")
                if _recommended_direction == 1:
                    _log.debug(f"Applying more starboard rudder (set_motor to 1)")
                elif _recommended_direction == -1:
                    _log.debug(f"Applying more port rudder (set_motor to -1)")
                else:
                    _log.debug(f"Keeping rudder where it is (set_motor to 0)")
                    _recommended_direction = 0
                self._boat.set_motor(_recommended_direction)
            time.sleep(self._boat_sampling_interval/1000)

        _log.info("motor_manager_daemon stopped")

    @property
    def boat(self):
        return self._boat

    @property
    def arduino(self):
        return self._boat.arduino

    @property
    def controller(self):
        return self._controller
