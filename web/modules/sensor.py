# Author: Adrian Vrouwenvelder

from modules.mpu9250Interface import get_interface as get_mpu_interface


class Sensor:

    def __init__(self, config):
        self._imu_interface = get_mpu_interface(config)
        self._imu_interface.start()

    @property
    def heading(self):
        return self._imu_interface.compass_deg()

    @property
    def heel_angle_deg(self):
        return self._imu_interface.heel_deg()

    @property
    def turn_rate_dps(self): pass

    @property
    def temp_celsius(self):
        return self._imu_interface.temp

