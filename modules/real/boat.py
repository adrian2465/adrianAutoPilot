# Author: Adrian Vrouwenvelder  August 2023

from modules.interfaces.boat_interface import BoatInterface
from modules.interfaces.arduino_interface import ArduinoInterface
from modules.real.mpu9250 import get_interface as get_mpu_interface
from modules.common.config import Config
from modules.common.file_logger import Logger

_log = Logger("boat")


class BoatImpl(BoatInterface):

    def __init__(self, cfg):
        super().__init__(cfg)
        self._actuator = ArduinoInterface()
        self._imu = get_mpu_interface(cfg)
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
    from modules.common.file_logger import Logger
    from time import sleep
    cfg = Config("../../configuration/config.yaml")

    _log.info("Monitoring Boat. Hit ^C to terminate")
    boat = BoatImpl(cfg)

    while True:
        _log.info(f"Heading is {boat.heading()}, Heel is {boat.heel()}, Rudder is {boat.rudder()}")
        sleep(1)
