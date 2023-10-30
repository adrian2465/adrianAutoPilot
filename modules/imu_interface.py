from __future__ import print_function
from __future__ import division

import os
import logging
import threading
import traceback
from math import atan2, pi

import smbus2 as smbus
from time import sleep

from modules.common import hardware_math
from modules.common.config import Config
from modules.common.weighted_average_vector import WeightedAverageVector
from modules.common.angle_math import apply_operation, vector_from


class Imu:
    # Interface for MPU9250 (Accelerometer, gyroscope, thermometer) and AK8963 (Magnetometer).
    # Enabling the i2c interface for reading the mpu9250
    # Manually create the i2c device:
    # $ sudo modprobe i2c-dev
    # Now you should have /dev/i2c-1
    # If you now run:
    # $ sudo i2cdetect -y 1  Found in i2c-tools\n
    # you will get a hexdump with one or two numbers in it. These are the IMU addresses:
    # 0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
    # 00:                         -- -- -- -- 0c -- -- --
    # 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    # 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    # 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    # 40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    # 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    # 60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
    # 70: -- -- -- -- -- -- -- --
    # #
    # I.E.:
    # * MPU9250_ADDRESS = 0x68
    # * AK8963_ADDRESS = 0x0C
    # #
    # 0x0c will not appear until you enable it (this code enables it).
    # #
    # This code should be run as root to access bus(1). See run_tests.sh
    ############################################################
    # --- MPU9250 -----------------
    # NOTE: Accelerometer and Gyroscope are in big endian format
    MPU9250_ADDRESS = 0x68
    MPU9250_WHO_AM_I_REG = 0x75
    MPU9250_DEVICE_ID = 0x71  # Expected value of WHO_AM_I
    PWR_MGMT_1_REG = 0x6B
    INT_PIN_CFG_REG = 0x37
    INT_ENABLE_REG = 0x38

    # --- Accelerometer ------------------
    ACCEL_DATA_REG = 0x3B  # ACCEL_XOUT_H (6 bytes: XH, XL, YH, YL, ZH, ZL in that order)

    ACCEL_OFFSET = 0
    ACCEL_CONFIG_REG = 0x1C
    ACCEL_CONFIG2_REG = 0x1D
    ACCEL_CONFIG_2G = 0x00  # NOTE: Align with ACCEL_CONVERSION
    ACCEL_CONFIG_4G = 0x08  # Bit 3 0000 1000. NOTE: Align with ACCEL_CONVERSION
    ACCEL_CONFIG_8G = 0x10  # Bit 4 0001 0000. NOTE: Align with ACCEL_CONVERSION
    ACCEL_CONFIG_16G = ACCEL_CONFIG_4G | ACCEL_CONFIG_8G  # Bits 3 and 4 0001 1000. NOTE: Align with ACCEL_CONVERSION
    ACCEL_RANGE_CONV = 2.0 / 32767  # Use 4.0 for _4G, 8.0 for _8G, etc.

    # --- Temperature Sensor --------------------
    TEMP_DATA_REG = 0x41  # TEMP_OUT_H followed by TEMP_OUT_L
    TEMP_OFFSET = 6

    # --- Gyroscope Sensor --------------------
    GYRO_DATA_REG = 0x43  # GYRO_XOUT_H (6 bytes: XH, XL, YH, YL, ZH, ZL in that order)

    GYRO_OFFSET = 8
    GYRO_CONFIG_REG = 0x1B
    GYRO_CONFIG_250DPS = 0x00  # NOTE: Align with GYRO_CONVERSION
    GYRO_CONFIG_500DPS = 0x08  # Bit 3 0000 1000. NOTE: Align with GYRO_CONVERSION
    GYRO_CONFIG_1000DPS = 0x10  # Bit 4 0001 0000. NOTE: Align with GYRO_CONVERSION
    GYRO_CONFIG_2000DPS = GYRO_CONFIG_500DPS | GYRO_CONFIG_1000DPS  # Bits 3 and 4 0001 1000. NOTE: Align with GYRO_CONV
    GYRO_RANGE_CONV = 250 / 32767  # Use 500 for 500DPS, etc.

    ############################################################
    # --- AK8963 ------------------
    # NOTE: Magnetometer data is stored in two’s complement and Little Endian format.
    # Measurement range of each axis is from -32760 ~ 32760 decimal in 16-bit output.
    AK8963_ADDRESS = 0x0C
    AK8963_WHO_AM_I_REG = 0x00  # WIA
    AK8963_DEVICE_ID = 0x48  # Expected value of WHO_AM_I (WIA)

    # --- Magnetometer Sensor
    MAG_DATA_REG = 0x03  # HXL 6 bytes (XL, XH, YL, YH, ZL, ZH in that order -- LITTLE ENDIAN!)

    MAG_SELF_TEST_REG = 0x0C  # ASTC
    MAG_SELF_TEST_OK = 0x40  # Expected value of ASTC
    MAG_SENSITIVITY_REG = 0x10  # ASAX followed by ASAY, ASAZ.
    MAG_CNTL1_REG = 0x0A
    MAG_CNTL1_8HZ = 0x02  # Continuous Measurement Mode 1 = 8
    MAG_CNTL1_100HZ = 0x06  # Continuous Measurement Mode 2
    MAG_CNTL1_14BIT = 0x00
    MAG_CNTL1_16BIT = 0x10  # 0001 0000  (bit 4)
    # MAG_CNTL2_REG = 0x0B  # SPEC SAYS DO NOT USE
    # ST1 register consists of two bits: DOR (bit 1) and DRDY (bit 0)
    # DRDY: Data Ready (bit 0)
    # "0": Normal
    # "1": Data is ready
    # DRDY bit turns to “1” when data is ready in single measurement mode or self-test mode.
    # It returns to “0” when any one of ST2 register or measurement data register (HXL to HZH) is read.
    MAG_ST1_REG = 0x02
    MAG_ST1_DOR = 0x02
    MAG_ST1_DRDY = 0x01

    MAG_ST2_REG = 0x09
    MAG_ST2_MAG_OVERFLOW = 0x08
    MAG_RANGE_CONV = 4912 / 32760  # Per documentation, range is from -4912 to 4912 uT (microTeslas)
    ROOM_TEMP_OFFSET = 21.0
    TEMP_SENSITIVITY = 333.87
    X, Y, Z = 0, 1, 2

    def __init__(self, bus):
        """
        Initialize the IMU (MPU 9250)
        """
        cfg = Config.getConfig()
        self._log = logging.getLogger("IMU")
        self._smbus = None  # In case we fail in init_smbus and need to call __del__
        self._smbus = self._init_smbus(bus)
        self._mag = None
        self._gyro = None
        self._accel = None
        self._temp = None
        self._gyro_bias = cfg['imu_gyro_bias']
        self._accel_bias = cfg['imu_accel_bias']
        self._temp_bias = cfg['imu_temperature_bias']
        self._mag_bias = cfg['imu_magnetometer_bias']
        self._mag_scale = cfg['imu_magnetometer_scale']
        self._mag_calib = cfg['imu_magnetometer_calib']
        self._moving_average_window_size_gyro = cfg['imu_gyro_moving_average_window_size']
        self._moving_average_window_size_accel = cfg['imu_accel_moving_average_window_size']
        self._moving_average_window_size_temp = cfg['imu_temperature_moving_average_window_size']
        self._moving_average_window_size_mag = cfg['imu_magnetometer_moving_average_window_size']
        self._monitor_thread = threading.Thread(target=self._monitor_daemon)
        self._monitor_thread.daemon = True
        self._is_initialized = False
        self._is_killed = False

    def _init_smbus(self, bus):
        if os.getuid() != 0:
            self._log.fatal("You must be root to use this class.")
            exit(1)
        try:
            _smbus = smbus.SMBus(bus)
        except FileNotFoundError as e2:
            self._log.fatal(f"Cannot create MPU interface. Reason = {e2}. Make sure you're running on RPi0")
            _smbus = None
            exit(1)
        if _smbus.read_byte_data(Imu.MPU9250_ADDRESS,
                                 Imu.MPU9250_WHO_AM_I_REG) is not Imu.MPU9250_DEVICE_ID:
            self._log.fatal('init failed to find MPU9250')
            exit(1)
        _smbus.write_byte_data(Imu.MPU9250_ADDRESS, Imu.PWR_MGMT_1_REG, 0x00)  # turn MPU mode off
        sleep(0.2)
        _smbus.write_byte_data(Imu.MPU9250_ADDRESS, Imu.PWR_MGMT_1_REG, 0x01)  # auto select clock source
        _smbus.write_byte_data(Imu.MPU9250_ADDRESS, Imu.ACCEL_CONFIG_REG, Imu.ACCEL_CONFIG_2G)
        _smbus.write_byte_data(Imu.MPU9250_ADDRESS, Imu.GYRO_CONFIG_REG, Imu.GYRO_CONFIG_250DPS)
        # You have to enable the other chips to join the I2C network
        # then you should see 0x68 and 0x0c from:
        # sudo i2cdetect -y 1
        _smbus.write_byte_data(Imu.MPU9250_ADDRESS, Imu.INT_PIN_CFG_REG, 0x22)
        _smbus.write_byte_data(Imu.MPU9250_ADDRESS, Imu.INT_ENABLE_REG, 0x01)
        sleep(0.1)
        if _smbus.read_byte_data(Imu.AK8963_ADDRESS,
                                 Imu.AK8963_WHO_AM_I_REG) is not Imu.AK8963_DEVICE_ID:
            self._log.fatal('init failed to find AK8963')
            exit(1)
        _smbus.write_byte_data(Imu.AK8963_ADDRESS, Imu.MAG_CNTL1_REG,
                               Imu.MAG_CNTL1_16BIT | Imu.MAG_CNTL1_8HZ)  # cont mode 1
        _smbus.write_byte_data(Imu.AK8963_ADDRESS, Imu.MAG_SELF_TEST_REG, 0)
        return _smbus

    def __del__(self):
        if self._smbus is None:
            return
        self._smbus.write_byte_data(Imu.MPU9250_ADDRESS, Imu.PWR_MGMT_1_REG, 0x00)  # turn MPU mode off
        self._smbus.close()
        self._log.debug("SMBus closed.")

    def _monitor_daemon(self):
        self._log.debug("MPU9250 monitor daemon started")
        self._gyro = WeightedAverageVector(self._moving_average_window_size_gyro)
        self._accel = WeightedAverageVector(self._moving_average_window_size_accel)
        self._mag = WeightedAverageVector(self._moving_average_window_size_mag)
        self._temp = WeightedAverageVector(self._moving_average_window_size_temp)
        while not self._is_killed:
            # Read Gyroscope, Accelerometer and Thermometer from MPU9250
            data = self._smbus.read_i2c_block_data(Imu.MPU9250_ADDRESS, Imu.ACCEL_DATA_REG, 14)
            self._gyro.add(vector_from(data, Imu.GYRO_OFFSET, Imu.GYRO_RANGE_CONV,
                                       endian_transformer_fn=hardware_math.c_short_from_big_endian))
            self._accel.add(vector_from(data, Imu.ACCEL_OFFSET, Imu.ACCEL_RANGE_CONV,
                                        endian_transformer_fn=hardware_math.c_short_from_big_endian))
            self._temp.add([(hardware_math.c_short_from_big_endian(data[Imu.TEMP_OFFSET],
                                                                   data[Imu.TEMP_OFFSET + 1]) -
                             Imu.ROOM_TEMP_OFFSET) / Imu.TEMP_SENSITIVITY + 21.0])
            # Read Magnetometer from AK8963
            data = self._smbus.read_i2c_block_data(Imu.AK8963_ADDRESS, Imu.MAG_DATA_REG, 7)
            if not Imu.MAG_ST2_MAG_OVERFLOW & data[6]:  # data[6] is MAG_ST2_REGISTER. Ignore magnetic overflows.
                self._mag.add(vector_from(data, 0, Imu.MAG_RANGE_CONV,
                                          endian_transformer_fn=hardware_math.c_short_from_little_endian))
            self._is_initialized = True
        self._is_initialized = False
        self._log.debug("MPU9250 monitor daemon exited")

    def accel(self):
        return apply_operation(lambda v, b: v - b, self._accel.value, self._accel_bias)

    def gyro(self):
        return apply_operation(lambda v, b: v - b, self._gyro.value, self._gyro_bias)

    def mag(self):
        # (mag_val * mag_calib - mag_bias) * mag_scale
        return apply_operation(lambda vc_b, s: vc_b * s, apply_operation(lambda vc, b: vc - b,
                                                                         apply_operation(lambda a, c: a * c,
                                                                                         self._mag.value,
                                                                                         self._mag_calib),
                                                                         self._mag_bias), self._mag_scale)

    def temp(self):
        return self._temp.value[0] - self._temp_bias

    def compass_deg(self):
        mag = self.mag()
        return (atan2(mag[0], mag[1]) * (180 / pi) + 90 + 360) % 360

    def heel_deg(self):
        accel = self.accel()
        return 180 - (atan2(accel[2], accel[0]) * (180 / pi) + 90 + 360) % 360

    def turn_rate_dps(self):
        return self.gyro()[2]

    def start_daemon(self):
        self._log.debug("Starting MPU9250 daemon...")
        self._monitor_thread.start()
        self._log.debug("Waiting for MPU9250 daemon to initialize...")
        while not self._is_initialized: sleep(0.1)
        self._log.info("MPU9250 is ready for queries")

    def stop_daemon(self):
        self._log.debug("Killing MPU9250 daemon...")
        self._is_killed = True
        while self._is_initialized:
            sleep(0.1)  # wait for daemon to die.
        self._log.info("MPU9250 daemon terminated")
        self._accel = None
        self._gyro = None
        self._temp = None
        self._mag = None

    def is_running(self):
        return self._is_initialized


if __name__ == "__main__":
    import sys
    Config.init()
    log = logging.getLogger("mpu9250")
    imu = Imu(bus=1)
    imu.start_daemon()
    sleep_time = 1 if len(sys.argv) == 1 else int(sys.argv[1])
    stopped = False
    if not log.isEnabledFor(logging.DEBUG):
        log.info("NOTE: Enable DEBUG to view raw values for gyroscope, accelerometer, and magnetometer")
    try:
        while not stopped:
            try:
                log.info(f'Compass = {imu.compass_deg():6.2f} deg, '
                         f'Heel = {imu.heel_deg():6.2f} deg, '
                         f'Temp = {imu.temp():3.0f} C')
                log.debug(f'- gyro = {imu.gyro()} dps')
                log.debug(f'- accel = {imu.accel()} G')
                log.debug(f'- mag = {imu.mag()} uT')
                sleep(sleep_time)
            except KeyboardInterrupt:
                stopped = True
    except Exception as e:
        log.fatal(f"Got exception {e}. Stacktrace:\n{traceback.format_exc()}")
        log.fatal(f"")
        exit(1)
    finally:
        imu.stop_daemon()
    log.info('Bye')
    exit(0)
