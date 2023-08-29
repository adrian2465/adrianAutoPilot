# Author: Adrian Vrouwenvelder  August 2023

from boat_interface import BoatInterface
from arduinoInterface import ArduinoInterface
from modules.mpu9250Interface import get_interface as get_mpu_interface
from config import Config


class BoatImpl(BoatInterface):

    def __init__(self, config):
        super().__init__(config)
        self._actuator = ArduinoInterface()
        self._imu = get_mpu_interface(config)
        self._imu.start()

    def heading(self):
        """Boat's current heading."""
        return self._imu.compass_deg()

    def heel(self):
        """Angle of heel in degrees. 0 = level"""
        return self._imu.heel_deg()

    def rudder(self):
        """Returns normalized rudder (-1 for full port, 1 for full starboard, 0 for centered)"""
        return self._actuator.rudder()


if __name__ == "__main__":
    from file_logger import logger, DEBUG
    from time import sleep
    log = logger(dest=None)
    log.set_level(DEBUG)

    log.info("Monitoring Boat. Hit ^C to terminate")
    boat = BoatImpl(Config("../../configuration/config.yaml"))

    while True:
        log.info(f"Heading is {boat.heading()}, Heel is {boat.heel()}, Rudder is {boat.rudder()}")
        sleep(1)
