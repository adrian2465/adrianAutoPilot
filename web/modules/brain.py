## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
## April 2023
import boat
from arduinoInterface import ArduinoInterface
from boat_interface import BoatInterface
from config import Config

import threading
import time
from pid_controller import PID
from file_logger import logger, INFO, DEBUG


class Brain:

    def __init__(self, arduino_interface: ArduinoInterface, cfg: Config, boat: BoatInterface):
        self._boat = boat
        self._arduino_interface = arduino_interface
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
        log.debug(f"Setting target_course to {course}")
        self._target_course = course

    def commanded_rudder(self):  # TODO Commanded Rudder shouldn't really be part of boat, but should be part of brain.
        """Desired rudder angle. Range is 0 <= commanded_rudder <= 1"""
        return self._commanded_rudder

    def set_commanded_rudder(self, commanded_rudder):
        log.debug(f"Setting commanded rudder to {'starboard' if commanded_rudder > 0 else 'port' if commanded_rudder < 0 else 'center'} ({commanded_rudder})")
        self._commanded_rudder = commanded_rudder

    def is_on_course(self):
        return abs(self._target_course - self._boat.heading()) <= self._course_tolerance_deg

    def is_clutch_engaged(self):
        return self._arduino_interface.clutch() == 1

    def engage_autopilot(self):
        self._arduino_interface.set_clutch(1)

    def disengage_autopilot(self):
        self._arduino_interface.set_motor(0)
        self._arduino_interface.set_clutch(0)

    def start(self):
        self._brain_thread.start()
        self._arduino_interface.start()  # Create monitor and writer.

    def stop(self):
        self._stop_requested = True
        self.disengage_autopilot()
        log.info("Brain stop requested")

    def get_recommended_motor_direction(self):
        return 0 if not self.is_clutch_engaged()\
            else 0 if abs(self._commanded_rudder - self._boat.rudder()) <= self._rudder_tolerance \
            else 1 if (self._commanded_rudder > 0 and self._commanded_rudder > self._boat.rudder()) \
            else -1

    def motor_manager_daemon(self):
        # Brain should check on course, heading, and rudder, and compute a new commanded rudder based on that.
        # Brain also talks to the arduino (which is the hydraulic ram actuator) to effectuate changes
        log = logger(dest=None, who="motor_manager_daemon")
        if "log_level" in cfg.brain: log.set_level(cfg.brain["log_level"])
        log.info(f"motor_manager_daemon started.")
        while not self._stop_requested:
            log.debug(f"boat rudder={self._boat.rudder()} commanded rudder={self.commanded_rudder()}  (diff={abs(self._boat.rudder() - self.commanded_rudder())})  tolerance={self._rudder_tolerance} motor={self._arduino_interface.motor()}")
            if self.get_recommended_motor_direction() == 1:
                log.debug(f"Need more starboard rudder")
            elif self.get_recommended_motor_direction() == -1:
                log.debug(f"Need more port rudder")
            else:
                log.debug(f"Need to keep rudder where it is")
                self._arduino_interface.set_motor(0)
            self._arduino_interface.set_motor(self.get_recommended_motor_direction())
            time.sleep(self._boat_sampling_interval/1000)

        log.info("motor_manager_daemon stopped")


def test_motor_direction(cfg):
    test_boat = BoatImpl(cfg)
    brain = Brain(arduino_interface, cfg, test_boat)
    brain._arduino_interface.set_clutch(1)
    brain._commanded_rudder = 0.5
    brain._boat.set_rudder(0.5)
    if brain.get_recommended_motor_direction() != 0:
        raise Exception("Recommended motor direction is not 0 (stbd)")
    brain._commanded_rudder = -0.5
    brain._boat.set_rudder(-0.5)
    if brain.get_recommended_motor_direction() != 0:
        raise Exception("Recommended motor direction is not 0 (port)")
    brain._commanded_rudder = 1.0
    brain._boat.set_rudder(0.5)
    if brain.get_recommended_motor_direction() != 1:
        raise Exception("Recommended motor direction is not starboard")
    brain._commanded_rudder = -1.0
    brain._boat.set_rudder(-0.5)
    if brain.get_recommended_motor_direction() != -1:
        raise Exception("Recommended motor direction is not port")
    brain._commanded_rudder = 1.0
    brain._boat.set_rudder(-0.5)
    if brain.get_recommended_motor_direction() != 1:
        raise Exception("Recommended motor direction is not starboard 2")
    brain._commanded_rudder = -1.0
    brain._boat.set_rudder(0.5)
    if brain.get_recommended_motor_direction() != -1:
        raise Exception("Recommended motor direction is not port 2")
    brain._arduino_interface.set_clutch(0)
    brain._commanded_rudder = 1
    brain._boat.set_rudder(0.5)
    if brain.get_recommended_motor_direction() != 0:
        raise Exception("Recommended motor direction is not 0 when clutch is off")
    log.info("test_motor_direction passed")


if __name__ == "__main__":
    from boat_simulator import BoatImpl
    from arduinoFileInterface import get_interface as get_arduino_interface
    cfg = Config("../../configuration/config.yaml")
    log = logger(dest=None, who="brain")
    if "log_level" in cfg.boat: log.set_level(cfg.boat["log_level"])
    arduino_interface = get_arduino_interface()
    log.debug(f"arduinoInterface in brain is {arduino_interface}")
    test_motor_direction(cfg)

    test_boat = BoatImpl(cfg)
    brain = Brain(arduino_interface, cfg, test_boat)
    brain.set_commanded_rudder(0)
    course = 10
    brain.set_target_course(course)
    brain._boat_sampling_interval = 1000

    brain.start()

    try:
        controller = brain._controller
        gains_file_suffix = controller.get_gains_as_csv().replace(",", "_")
        with open(f"../../output/brain_simulator_output_crs{course:03d}_hdg{test_boat.heading():03d}_p{gains_file_suffix}.csv", 'a') as outfile:
            # outfile.write("elapsed_time, p_gain, i_gain, d_gain, course, heading, rudder, motor_direction, on/off course\n")
            log.info("ctrl-C to stop")
            brain.engage_autopilot()
            interval = 0.1
            start_time = time.time()
            while True:
                brain.set_commanded_rudder(controller.compute_commanded_rudder(course, test_boat.heading()))
                motor_direction = brain.get_recommended_motor_direction()
                test_boat.update_rudder_and_heading(motor_direction)
                log.info(f"Current course={course:5.1f} {test_boat} commanded_rudder={brain.commanded_rudder()} recommended_motor_direction={motor_direction} {'ON course' if brain.is_on_course() else 'OFF course'}")
                # outfile.write(f"{time.time() - start_time:5.1f}, {controller.get_gains_as_csv()}, {course:5.1f}, {test_boat.heading():5.1f}, {brain.commanded_rudder():4.2f}, {motor_direction}, {'ON course' if brain.is_on_course() else 'OFF course'}\n")
                time.sleep(interval)
                if motor_direction == 0 and brain.is_on_course():
                    break
            log.info(f"Elapsed time {time.time()-start_time:0.1f}s")

    except KeyboardInterrupt:
        brain.disengage_autopilot()
        brain.stop()
        log.info('Bye')
