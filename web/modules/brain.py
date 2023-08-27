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
        self._rudder_tolerance = int(cfg.boat["rudder_tolerance"])

    def start(self):
        self._brain_thread.start()
        self._arduino_interface.start()  # Create monitor and writer.

    def stop(self):
        self._stop_requested = True
        log.info("Brain stop requested")

    def daemon(self):
        # Brain should check on course, heading, and rudder, and compute a new commanded rudder based on that.
        # Brain also talks to the arduino (which is the hydraulic ram actuator) to effectuate changes
        log.info("Brain started")
        while not self._stop_requested:
            self._controller.set_commanded_rudder(self._boat)
            desired_pump_motor_speed = 1 if self._boat.commanded_rudder() > 0 else -1
            desired_and_actual_pump_motor_same_direction = desired_pump_motor_speed == self._arduino_interface.motor_speed()
            if self._arduino_interface.clutch() == 0 \
                    or abs(self._boat.rudder() - self._boat.commanded_rudder()) <= self._rudder_tolerance:
                # Stop motor if it's running but either the clutch is off or the rudder is where we want it.
                # The motor should be stopped if the clutch is off.
                if self._arduino_interface.motor_speed() != 0:
                    log.debug(f"Motor is being stopped due to {'clutch off' if self._arduino_interface.clutch() == 0 else 'rudder on station'}")
                    self._arduino_interface.set_motor_speed(0)
            else:
                # Clutch is on and boat is off course. Set pump motor direction according to need
                if self._arduino_interface.motor_speed() != 0:
                    # Pump motor is already running.
                    if desired_and_actual_pump_motor_same_direction:
                        log.debug("Motor is already spinning in right direction")  # Motor is already running in the right direction, so leave it alone.
                    else:
                        # Motor is running, but in the wrong direction. Stop it. Start it again next loop.
                        log.debug("Motor is spinning, but in wrong direction. Changing...")
                        self._arduino_interface.set_motor_speed(0)
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
    test_boat.set_target_course(10)
    arduino_interface = get_arduino_interface()
    log.debug(f"arduinoInterface in brain is {arduino_interface}")
    brain = Brain(arduino_interface, config, test_boat)
    brain._boat_sampling_interval = 1000
    brain.start()
    ## LEFT OFF HERE 20230827-1243. See 'receive_status_from_arduino.sh'
    ## Next to do, interface the brain test code with the simulated boat rudder to make course correction, and then
    ## provide a way to enter the heading into the brain to let it know when it's done (again, simulated boat).
    ## At that point, it should be possible to poke different values into the brain in for course course updates and
    ## have it respond accordingly.  Or, have it drift off course with heading, and watch it respond.

    try:
        log.info("ctrl-C to stop")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        brain.stop()
        log.info('Bye')
