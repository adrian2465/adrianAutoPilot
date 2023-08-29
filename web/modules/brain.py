## Adrian Vrouwenvelder
## December 1, 2022
## March 2023
## April 2023
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
        self._brain_thread = threading.Thread(target=self.daemon)
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
        self._target_course = course

    def commanded_rudder(self):  # TODO Commanded Rudder shouldn't really be part of boat, but should be part of brain.
        """Desired rudder angle. Range is 0 <= commanded_rudder <= 1"""
        return self._commanded_rudder

    def set_commanded_rudder(self, commanded_rudder):
        self._commanded_rudder = commanded_rudder

    def is_on_course(self):
        return abs(self._target_course - self.heading()) <= self._course_tolerance_deg

    def start(self):
        self._brain_thread.start()
        self._arduino_interface.start()  # Create monitor and writer.

    def stop(self):
        self._stop_requested = True
        log.info("Brain stop requested")

    def daemon(self):
        # Brain should check on course, heading, and rudder, and compute a new commanded rudder based on that.
        # Brain also talks to the arduino (which is the hydraulic ram actuator) to effectuate changes
        log.info(f"Brain started.")
        while not self._stop_requested:
            log.debug(f"boat rudder = {self._boat.rudder()} commanded rudder = {self.commanded_rudder()}  delta = {abs(self._boat.rudder() - self.commanded_rudder())}  tolerance = {self._rudder_tolerance}")
            desired_pump_motor_speed = 1 if self.commanded_rudder() > 0 else -1
            desired_and_actual_pump_motor_same_direction = desired_pump_motor_speed == self._arduino_interface.motor_speed()
            if self._arduino_interface.clutch() == 0:
                log.debug("Motor should be stopped....")
                # Stop motor if it's running but either the clutch is off or the rudder is where we want it.
                # The motor should be stopped if the clutch is off.
                if self._arduino_interface.motor_speed() != 0:
                    log.debug(f"Motor is being stopped due to clutch off")
                    self._arduino_interface.set_motor_speed(0)
            else:
                self.set_commanded_rudder(self._controller.compute_commanded_rudder(self.target_course(), self._boat.heading()))
                # Clutch is on and boat is off course. Set pump motor direction according to need
                if self._arduino_interface.motor_speed() != 0:
                    # Pump motor is already running.
                    if abs(self._boat.rudder() - self.commanded_rudder()) <= self._rudder_tolerance:
                        log.debug(f"Actual and commanded rudder are within tolerance. Stopping motor.")
                        self._arduino_interface.set_motor_speed(0)
                    elif desired_and_actual_pump_motor_same_direction:
                        log.debug("Motor is already spinning in right direction")  # Motor is already running in the right direction, so leave it alone.
                    else:
                        # Motor is running, but in the wrong direction. Stop it. Start it again next loop.
                        log.debug("Motor is spinning, but in wrong direction. Stopping it to reverse direction...")
                        self._arduino_interface.set_motor_speed(0)
                else:
                    if abs(self._boat.rudder() - self.commanded_rudder()) <= self._rudder_tolerance:
                        log.debug(f"Actual and commanded rudder are within tolerance. Motor stopped and staying stopped.")
                    else:
                        # Motor is stopped, but needs to be running.
                        log.debug(f"arduinoInterface = {self._arduino_interface}")
                        log.debug(f"Motor (currently at {self._arduino_interface.motor_speed()}) is being set to spin in direction {desired_pump_motor_speed}")
                    self._arduino_interface.set_motor_speed(desired_pump_motor_speed)
            time.sleep(self._boat_sampling_interval/1000)

        log.info("Brain stopped")


if __name__ == "__main__":
    from boat_simulator import BoatImpl
    from arduinoFileInterface import get_interface as get_arduino_interface
    log = logger(dest=None)
    log.set_level(DEBUG)
    config = Config("../../configuration/config.yaml")
    test_boat = BoatImpl(config)
    target_course = 10

    arduino_interface = get_arduino_interface()
    log.debug(f"arduinoInterface in brain is {arduino_interface}")
    brain = Brain(arduino_interface, config, test_boat)
    brain.set_commanded_rudder(0)
    brain.set_target_course(10)
    brain._boat_sampling_interval = 1000
    brain.start()

    ## LEFT OFF HERE 20230828-0832:
    ## 0. Running this code never settles on a course.  It oscillates. Is it gain?  Or a bug?  
    ## 1. I believe this test code obviates the need for pid_controller's run code. That code could perhaps be tested against online datasets (gains, outputs, etc)
    ## without any boat reference at all.

    try:
        log.info("ctrl-C to stop")
        interval = 0.5
        while True:
            test_boat.update_rudder_and_heading(interval, 1 if brain.commanded_rudder() > 0 else -1 if brain.commanded_rudder() < 0 else 0)
            time.sleep(interval)

    except KeyboardInterrupt:
        brain.stop()
        log.info('Bye')
