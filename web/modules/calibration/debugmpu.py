from time import sleep, time

from config import Config
from modules.mpu9250Interface import get_interface


def current_milli_time():
    return round(time() * 1000)


if __name__ == "__main__":

    imu = get_interface(Config("../../../configuration/config.yaml"))
    imu.start()
    try:
        start_time = current_milli_time()
        print ("time, gx, gy, gz, mx, my, mz, ax, ay, az, comp")
        while True:
            a = imu.accel()
            g = imu.gyro()
            m = imu.mag()
            print(f'{current_milli_time() - start_time}, '
                  f'{g[0]: .3f},{g[1]: .3f},{g[2]: .3f},'
                  f'{m[0]: .3f},{m[1]: .3f},{m[2]: .3f},'
                  f'{a[0]: .3f},{a[1]: .3f},{a[2]: .3f},'
                  f'{imu.compass_deg(): .3f} ')
            sleep(0.01)
    except KeyboardInterrupt:
        imu.stop()
        print('imu9250 main loop terminated')