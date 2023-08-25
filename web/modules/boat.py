# Author: Adrian Vrouwenvelder  August 2023

from boat_interface import BoatInterface
from arduinoInterface import ArduinoInterface
from modules.mpu9250Interface import get_interface as get_mpu_interface
from config import Config


class BoatImpl(BoatInterface):

    def __init__(self, config):
        super().__init__(config)
        self._imu_interface = get_mpu_interface(config)
        self._arduinoInterface = ArduinoInterface()
        self._imu_interface.start()

    def get_heading(self):
        """Boat's current heading."""
        return self._imu_interface.compass_deg()

    def get_heel(self):
        """Angle of heel in degrees. 0 = level"""
        return self._sensor.heel_angle_deg()

    def get_rudder(self):
        """Returns normalized rudder (-1 for full port, 1 for full starboard, 0 for centered)"""
        return self._arduinoInterface.get_rudder()


if __name__ == "__main__":
    from file_logger import logger, DEBUG
    from time import sleep
    log = logger(dest=None)
    log.set_level(DEBUG)

    log.info("Hit ^C to terminate")
    boat = BoatImpl(Config("../../configuration/config.yaml"))

    while True:
        log.info(f"Heading is {boat.get_heading()}, Heel is {boat.get_heel()}, Rudder is {boat.get_rudder()}")
        sleep(1)
