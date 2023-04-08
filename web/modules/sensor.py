# Author: Adrian Vrouwenvelder
from modules.mpu9250Interface import get_interface
# from imuTestInterface import get_interface

class Sensor:

    def __init__(self):
        self._imu_interface = get_interface()
        self._imu_interface.start()

    def get_heading(self):
        return self._imu_interface.compass_deg()

    def get_heel_angle(self):
        return self._imu_interface.heel_deg()

    def get_pitch_variation_degrees(self): pass  # TODO implement

    def get_yaw_variation_degrees(self): pass # TODO Implement

    def get_accel_variation_gs(self): pass  # TODO Implement

    def get_temp_celsius(self):
        return self._imu_interface.temp

    def get_temp_fahrenheit(self):
        self.get_temp_celsius * 9 / 5 + 32
