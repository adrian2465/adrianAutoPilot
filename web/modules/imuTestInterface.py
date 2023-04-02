from __future__ import print_function
from __future__ import division
import smbus2 as smbus
from time import sleep
import numpy as np
import ctypes  # for signed int
from imuInterface import imu_interface

moving_average_size = 5  # Number of samples to combine for an average

def _moving_average(average, val):
    return val / moving_average_size + average * (moving_average_size - 1) / moving_average_size


class mpu9250_interface(imu_interface):
    def __init__(self, bus):
        super().__init__()
        self._mag_avg = np.zeros(3)
        self._gyro_avg = np.zeros(3)
        self._accel_avg = np.zeros(3)
        self._temp_avg = 0

    @property
    def _accel(self):
        return np.array([0, 0, 1])

    @property
    def _gyro(self):
        return np.array([0, 0, 0])

    @property
    def _temp(self):
        return 21

    @property
    def _mag(self):
        return np.array([.5, .5, .5])

    def _poll(self):
        self._mag_avg = _moving_average(self.mag, self._mag)
        self._gyro_avg = _moving_average(self.gyro, self._gyro)
        self._accel_avg = _moving_average(self.accel, self._accel)
        self._temp_avg = _moving_average(self.temp, self._temp)

    def monitor(self):
        print("test interface started")
        while (self.is_running):
            sleep(self.get_check_interval)
            self._poll()
        print("test interface terminated")

    @property
    def accel(self):
        return self._accel_avg

    @property
    def gyro(self):
        return self._gyro_avg

    @property
    def mag(self):
        return self._mag_avg

    @property
    def temp(self):
        return self._temp_avg

def get_interface(bus=1):
    return mpu9250_interface(bus=bus)
