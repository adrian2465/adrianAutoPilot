# Adrian Vrouwenvelder
# October 2023
import logging
import traceback

from modules.common.angle_math import normalize_angle, is_on_course as _is_on_course
from modules.common.config import Config

import threading
import time

from modules.imu_interface import Imu
from modules.pid_controller import PID
from modules.rudder_interface import RudderInterface


class Brain:
    _course_lock = threading.Lock()  # To prevent toggling None / val during brain loop

    def __init__(self, rudder, imu):
        cfg = Config.getConfig()
        self._log = logging.getLogger('brain')
        self._rudder = rudder
        self._imu = imu
        self._rudder_turn_rate_ups = 1000 / float(cfg['rudder_hard_over_time_ms'])
        self._rudder_tolerance = float(cfg['rudder_position_tolerance'])
        self._course_tolerance_deg = float(cfg['course_tolerance_deg'])
        imu_sampling_interval_ms = float(cfg['imu_sampling_interval_ms'])
        rudder_reporting_interval_ms = float(cfg['rudder_reporting_interval_ms'])
        self._loop_interval_s = min(rudder_reporting_interval_ms, imu_sampling_interval_ms)/1000.0
        self._actuator_manager_thread = threading.Thread(target=self._actuator_manager_daemon)
        self._actuator_manager_thread.daemon = True
        self._is_killed = False
        self._is_initialized = False
        self._course = None
        self._heading = None
        self._controller = None
        self.gains_selector = 'calm'

    def _get_desired_rudder(self):
        with Brain._course_lock:
            if self.is_engaged:
                return self._controller.compute(self._course, normalize_angle(self._imu.compass_deg))
            else:
                return None

    def _actuator_manager_daemon(self):
        self._log.info("Actuator Manager daemon started")
        rudder_movement_per_iteration = self._rudder_turn_rate_ups * self._loop_interval_s
        rudder_tolerance = max(rudder_movement_per_iteration, self._rudder_tolerance)
        self._log.debug(f"rudder units per iteration: {rudder_movement_per_iteration}. Tolerance: {rudder_tolerance}")
        while not self._is_killed:
            desired_rudder = self._get_desired_rudder()
            if desired_rudder is not None:
                self._log.debug(f"Heading: {self._imu.compass_deg:6.2f} Rudder: Desired: {desired_rudder:6.4f} actual: {self._rudder.rudder_position:6.4f}")
                desired_motor = \
                    0 if abs(desired_rudder - self._rudder.rudder_position) < rudder_tolerance \
                    else 1 if desired_rudder > self._rudder.rudder_position \
                    else -1
                self._rudder.set_motor_speed(desired_motor)
            self._is_initialized = True
            time.sleep(self._loop_interval_s)
        self._log.info("Actuator Manager daemon exited")
        self._is_initialized = False

    def start_daemon(self):
        self._log.debug("Starting Actuator Manager daemon...")
        self._actuator_manager_thread.start()
        self._log.debug("Waiting for Actuator Manager daemon to initialize...")
        while not self._is_initialized:
            time.sleep(0.1)
        self._log.info("Actuator Manager is ready for queries")

    def stop_daemon(self):
        self._log.debug("Disabling autopilot")
        self._course = None
        self._log.debug("Killing Actuator Manager daemon...")
        self._is_killed = True
        while self._is_initialized:
            time.sleep(0.1)  # wait for daemon to die.
        self._log.info("Actuator Manager daemon terminated")
        self._course = None
        self._heading = None

    @property
    def course(self):
        """Desired course for autopilot to steer. Set to None to disengage pilot"""
        return self._course

    @course.setter
    def course(self, course):
        """Desired course for autopilot to steer.None if pilot is disengaged"""
        self._rudder.set_motor_speed(0)
        with Brain._course_lock:
            if course is not None:
                new_course = normalize_angle(course)
                if self._course is None:
                    msg = f"Autopilot enabled with course = {new_course}"
                    new_clutch = 1
                    self._controller = PID(gains=self.gains_selector)
                else:
                    msg = f"New course: {new_course}"
                self._course = new_course
            else:
                msg = "Autopilot disabled" if self._course is not None else "Autopilot is already disabled"
                self._controller = None
                new_clutch = 0  # Disable whether enabled or not, as a safety.
                self._course = None
        if new_clutch is not None:
            self._rudder.set_clutch(new_clutch)
        self._log.info(msg)

    @property
    def is_on_course(self):
        return True if self.course is None else _is_on_course(self._course, self._heading, self._course_tolerance_deg)

    @property
    def is_engaged(self):
        return self._rudder.hw_clutch_status == 1 and self._course is not None


if __name__ == "__main__":
    import sys
    Config.init()
    log = logging.getLogger("brain")
    if len(sys.argv) != 2:
        log.error(f"Supply course")
        exit(1)
    rudder = None
    imu = None
    brain = None
    try:
        rudder = RudderInterface()
        rudder.start_daemon()
        imu = Imu(bus=1)
        imu.start_daemon()
        brain = Brain(rudder, imu)
        brain.start_daemon()
        log.info("^C to stop")
        while True:
            input_str = input("Enter course (OFF for Disable): ").lower()
            try:
                brain.course = int(input_str)
            except ValueError:
                brain.course = None
            except KeyboardInterrupt:
                break
            except Exception:
                exit(1)
    except Exception as e:
        log.fatal(f"Got exception {e}. Stacktrace:\n{traceback.format_exc()}")
    finally:
        if brain is not None: brain.stop_daemon()
        if rudder is not None: rudder.stop_daemon()
        if imu is not None: imu.stop_daemon()
        log.info("Terminated")
