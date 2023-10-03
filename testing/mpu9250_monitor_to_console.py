from modules.real.mpu9250 import get_interface
from modules.common.file_logger import Logger
from modules.common.config import Config
from time import sleep

if __name__ == "__main__":

    log = Logger(config_path="mpu9250", dest=None, who="mpu9250")
    cfg = Config("configuration/config.yaml")
    if "log_level" in cfg.mpu: log.set_level(cfg.mpu["log_level"])
    imu = get_interface(cfg)
    imu.start()
    seconds_for_calibration = 10
    try:
        while True:
            print(f'sample_freq={imu.sample_rate_hz} hz')
            print(f'g = {imu.gyro()} dps')
            print(f'a = {imu.accel()} G')
            print(f't = {imu.temp()} C')
            print(f'm = {imu.mag()} uT')
            print(f'Heel = {imu.heel_deg()} deg')
            print(f'Compass = {imu.compass_deg()}')
            sleep(1)

    except KeyboardInterrupt:
        imu.stop()
        print('Bye')
