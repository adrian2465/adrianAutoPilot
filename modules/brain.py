# Adrian Vrouwenvelder
# October 2023
import logging
import traceback
from pathlib import Path

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
        self._log = logging.getLogger('Brain General')
        self._rudder = rudder
        self._imu = imu
        self._rudder_turn_rate_ups = 1000 / float(Config.get('rudder_hard_over_time_ms'))
        self._metric_tolerance = float(Config.get('metric_tolerance'))
        self._course_tolerance_deg = float(Config.get('course_tolerance_deg'))
        imu_sampling_interval_ms = float(Config.get('imu_sampling_interval_ms'))
        rudder_reporting_interval_ms = float(Config.get('rudder_reporting_interval_ms'))
        self._max_turn_rate_dps = Config.get('boat_max_turn_rate_dps')
        self._loop_interval_s = min(rudder_reporting_interval_ms, imu_sampling_interval_ms)/1000.0
        self._actuator_manager_thread = threading.Thread(target=self._actuator_manager_daemon)
        self._actuator_manager_thread.daemon = True
        self._is_killed = False
        self._is_initialized = False
        self._course = None
        self._controller = PID()

    def log_lock(self, log, location, expected):
        log.debug(f"course_lock. Location={location}, Expected={'Locked' if expected else 'Unlocked'}. Current state={Brain._course_lock}")

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

    @property
    def control_output(self):
        return self._controller.control_output

    @property
    def course(self):
        """Desired course for autopilot to steer. Set to None to disengage pilot"""
        return self._course

    @course.setter
    def course(self, new_course):
        """Desired course for autopilot to steer. None if pilot is disengaged"""
        new_course = normalize_angle(new_course) if new_course is not None else None
        self.log_lock(self._log, "course() waiting", False)
        with Brain._course_lock:
            self.log_lock(self._log, "course() gotten", True)
            if new_course is not None and self._course is None:  # Switched disabled to enabled
                msg = f"Autopilot enabled with course = {new_course}"
                self._course = new_course
                self._rudder.set_clutch(1)
            elif new_course is not None and self._course is not None:  # Switched enabled to enabled (new course?)
                msg = f"New course: {new_course}"
                self._course = new_course
            elif new_course is None and self._course is None:  # Switched disabled to disabled
                msg = "Autopilot is already disabled. No action."
                pass
            else:  # Switched enabled to disabled
                msg = "Autopilot disabled"
                self._rudder.set_clutch(0)
                self._rudder.set_motor_speed(0)
                self._course = None
        self.log_lock(self._log, "course() released", False)
        self._log.info(msg)

    @property
    def is_on_course(self):
        return self.course is None or _is_on_course(self._course, self._imu.compass_deg, self._course_tolerance_deg)

    @property
    def is_engaged(self):
        # MUCH TOO CHATTY!  self._log.debug(f"is_engaged() => {self._rudder.hw_clutch_status}")
        return self._rudder.hw_clutch_status == 1

    def _get_control(self, log):
        self.log_lock(log,"_get_control() waiting", False)
        with Brain._course_lock:
            self.log_lock(log, "_get_control() gotten", True)
            if self.is_engaged:
                log.debug(f"_get_control: engaged 1")
                log.debug(f"_get_control: Course = {self._course}")
                log.debug(f"_get_control: compass = {normalize_angle(self._imu.compass_deg)}")
                controller = self._controller
                log.debug(f"_get_control: controller = {controller}")
                _rc = controller.compute(self._course, normalize_angle(self._imu.compass_deg))
                log.debug(f"_get_control: engaged 2")
            else:
                log.debug(f"_get_control: NOT engaged")
                _rc = None
            log.debug("_get_control: About to release lock")
        self.log_lock(log, "_get_control() released", False)
        log.debug(f"_get_control({self._course}, {normalize_angle(self._imu.compass_deg)}) ==> {_rc}")
        return _rc

    def _get_controlled_metric(self):
        """This is the item we're attempting to control in our attempts to steer a course. Positive to stbd."""
        # Rudder Position is one such potential value, but suffers from the fact that if the course error is 0, the
        # rudder position (without an offset correction) will also be made to converge on zero; however, in a real
        # environment there will always be weather helm offset and so there will practically always be non-zero rudder
        # when on course. Perhaps a more direct controllable value is turn rate, which be zero when the error is zero,
        # regardless of rudder position.
        _rc = self._imu.turn_rate_dps / self._max_turn_rate_dps
        self._log.debug(f"_get_controlled_metric({self._imu.turn_rate_dps}, {self._max_turn_rate_dps})) ==> {_rc}")
        return _rc

    def _actuator_manager_daemon(self):
        _log = logging.getLogger("Brain Daemon")
        _log.info(f"Looping (interval = {self._loop_interval_s}...")
        while not self._is_killed:
            if self.is_engaged:
                control = self._get_control(_log)
                if control is not None:
                    metric = self._get_controlled_metric()
                    _log.debug(f"Control: {control:6.4f} Metric: {metric:6.4f}")
                    desired_motor = \
                        0 if abs(control - metric) <= self._metric_tolerance else \
                        1 if control > metric else \
                        -1
                    if self._rudder.motor_speed != desired_motor:
                        _log.debug(f"Existing motor speed = {self._rudder.motor_speed}, desired_motor={desired_motor}")
                        self._rudder.set_motor_speed(desired_motor)
            self._is_initialized = True
            time.sleep(self._loop_interval_s)
        _log.info("exited")
        self._is_initialized = False

    @property
    def is_running(self):
        return self._is_initialized
    @property
    def controller(self):
        return self._controller

    @property
    def imu(self):
        return self._imu

    @property
    def rudder(self):
        return self._rudder


if __name__ == "__main__":
    import sys
    Config.init()
    log = logging.getLogger("brain")
    if not Path(Config.usb_device).exists():
        log.error("This CLI cannot be run outside of the Pi")
        exit(1)
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
