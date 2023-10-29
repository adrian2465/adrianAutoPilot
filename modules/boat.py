# Author: Adrian Vrouwenvelder  August 2023
from modules.real.rudder_interface import get_interface as get_arduinno_interface
from modules.interfaces.boat_interface import BoatInterface
from modules.real.mpu9250 import get_interface as get_mpu_interface
from modules.common.config import Config
from modules.common.file_logger import Logger

_log = Logger("boat")


class BoatImpl(BoatInterface):

    def __init__(self, cfg):
        super().__init__(cfg)
        self._arduino_interface = get_arduinno_interface()
        self._imu = get_mpu_interface(cfg)

    def heading(self):
        """Boat's current heading."""
        return self._imu.compass_deg()

    def heel(self):
        """Angle of heel in degrees. 0 = level"""
        return self._imu.heel_deg()

    def rudder(self):
        """Returns normalized rudder (-1 for full port, 1 for full starboard, 0 for centered)"""
        return self._arduino_interface.get_rudder_position()

    def is_clutch_engaged(self):
        return self._arduino_interface.clutch() == 1

    def engage_autopilot(self):
        self._arduino_interface.set_clutch(1)

    def disengage_autopilot(self):
        self._arduino_interface.set_motor_speed(0)
        self._arduino_interface.set_clutch(0)

    def motor(self):
        self._arduino_interface.get_motor_speed()

    def set_motor(self, m):
        self._arduino_interface.set_motor_speed(m)

    def start(self):
        self._arduino_interface.start_daemon()  # Create monitor and writer.
        self._imu.start_daemon()

    def stop(self):
        pass

    def get_message(self):
        return self._arduino_interface.get_message()

    @property
    def arduino(self):
        return self._arduino_interface


if __name__ == "__main__":
    from modules.common.file_logger import Logger
    from time import sleep
    cfg = Config("../../configuration/config.yaml")

    _log.info("Monitoring Boat. Hit ^C to terminate")
    boat = BoatImpl(cfg)

    while True:
        _log.info(f"Heading is {boat.heading()}, Heel is {boat.heel()}, Rudder is {boat.rudder()}")
        sleep(1)
