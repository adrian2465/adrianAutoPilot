import threading
from math import atan2, pi

class imu_interface(object):
    def __init__(self):
        self._monitor_thread = threading.Thread(target=self.monitor)
        self._monitor_thread.daemon = True
        self._check_interval = 1.0/60  # NOTE: IMU data refresh rate is 400kHz on i2c interface (so smallest interval = 1/400000)
        self._is_running = True

    def start(self):
        self._running = True
        self._monitor_thread.start()

    def stop(self):
        self._running = False

    def compass_deg(self):
        mag = self.mag
        return (atan2(mag[0], mag[1]) * (180/pi) + 90 + 360) % 360

    def heel_deg(self):
        mag = self.mag
        return 180 - (atan2(mag[2], mag[1]) * (180/pi) + 90 + 360) % 360

    @property
    def accel(self):
        """Return vector for acceleration along all 3 axes. Units = Gs  (9.8m/s/s = 1.0g)"""
        pass  # Override.

    @property
    def gyro(self):
        """Return vector for angular velocity for all 3 axes. Units = degrees per Second."""
        pass  # Override.

    @property
    def mag(self):
        """Return vector for magnetometer for all 3 axes. Units = microteslas"""
        pass  # Override.

    @property
    def temp(self):
        """Return value for chip (roughly ambient) temperature in degrees Celsius."""
        pass  # Override.

    def monitor(self):
        pass

    @property
    def is_running(self):
        return self._is_running

    @property
    def check_interval(self):
        return self._check_interval

#override
def get_interface(): pass
