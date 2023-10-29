from __future__ import print_function
from __future__ import division
import smbus2 as smbus
from time import sleep, time

from modules.common import angle_math
from modules.interfaces.imu_interface import ImuInterface
from modules.common.angle_math import apply_operation, vector_from, WeightedAverageVector

_log = Logger("mpu9250")

# Enabling the i2c interface for reading the mpu9250
# Manually create the i2c device:
# $ sudo modprobe i2c-dev
# Now you should have /dev/i2c-1
# If you now run:
# $ sudo i2cdetect -y 1  # Found in i2c-tools
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
#
# I.E.:
# * MPU9250_ADDRESS = 0x68
# * AK8963_ADDRESS = 0x0C
#
# 0x0c will not appear until you enable it (this code enables it).
#
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
GYRO_CONFIG_2000DPS = GYRO_CONFIG_500DPS | GYRO_CONFIG_1000DPS  # Bits 3 and 4 0001 1000. NOTE: Align with GYRO_CONVERSION
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




class Mpu9250(ImuInterface):
    def __init__(self, cfg, bus):
        """
        Initialize the IMU
        """
        super().__init__()
        self._mag = None
        self._gyro = None
        self._temp = None
        self._accel = None
        try:
            self.bus = smbus.SMBus(bus)
        except FileNotFoundError as e:
            _log.error(f"Cannot create MPU interface. Reason = {e}. Make sure you're running on RPi0")
            self.bus = None
            exit(1)

        if self.bus.read_byte_data(MPU9250_ADDRESS, MPU9250_WHO_AM_I_REG) is not MPU9250_DEVICE_ID:
            raise Exception('SEVERE: MPU9250: init failed to find device')

        self.bus.write_byte_data(MPU9250_ADDRESS, PWR_MGMT_1_REG, 0x00)  # turn MPU mode off
        sleep(0.2)
        self.bus.write_byte_data(MPU9250_ADDRESS, PWR_MGMT_1_REG, 0x01)  # auto select clock source
        self.bus.write_byte_data(MPU9250_ADDRESS, ACCEL_CONFIG_REG, ACCEL_CONFIG_2G)
        self.bus.write_byte_data(MPU9250_ADDRESS, GYRO_CONFIG_REG, GYRO_CONFIG_250DPS)

        # You have to enable the other chips to join the I2C network
        # then you should see 0x68 and 0x0c from:
        # sudo i2cdetect -y 1
        self.bus.write_byte_data(MPU9250_ADDRESS, INT_PIN_CFG_REG, 0x22)
        self.bus.write_byte_data(MPU9250_ADDRESS, INT_ENABLE_REG, 0x01)
        sleep(0.1)

        if self.bus.read_byte_data(AK8963_ADDRESS, AK8963_WHO_AM_I_REG) is not AK8963_DEVICE_ID:
            raise Exception('SEVERE: AK8963: init failed to find device')
        self.bus.write_byte_data(AK8963_ADDRESS, MAG_CNTL1_REG, (MAG_CNTL1_16BIT | MAG_CNTL1_8HZ))  # cont mode 1
        self.bus.write_byte_data(AK8963_ADDRESS, MAG_SELF_TEST_REG, 0)

        self._mag = [0] * 3
        self._gyro = [0] * 3
        self._accel = [0] * 3
        self._temp = 0
        self._turn_rate_dps = 0

        # LEFT OFF HERE - All this is changed due to config changes.
        mpu = cfg.mpu
        gyro = mpu['gyro']
        accel = mpu['accel']
        temp = mpu['temp']
        mag = mpu['mag']
        self.gyro_bias = gyro['bias']
        self.accel_bias = accel['bias']
        self.temp_bias = temp['bias']
        self.mag_bias = mag['bias']
        self.mag_scale = mag['scale']
        self.mag_calib = mag['calib']
        self.moving_average_window_size_gyro = gyro['moving_average_window_size']
        self.moving_average_window_size_accel = accel['moving_average_window_size']
        self.moving_average_window_size_temp = temp['moving_average_window_size']
        self.moving_average_window_size_mag = mag['moving_average_window_size']
        self.sample_rate_hz = 0

    def __del__(self):
        if self.bus is None:
            return
        self.bus.write_byte_data(MPU9250_ADDRESS, PWR_MGMT_1_REG, 0x00)  # turn MPU mode off
        self.bus.close()
        print("INFO: Bus closed. MPU off.")

    def monitor(self):
        print("INFO: imu9250 monitor running")
        iterations = 0
        start_time_s = time()
        self._gyro = WeightedAverageVector(self.moving_average_window_size_gyro)
        self._accel = WeightedAverageVector(self.moving_average_window_size_accel)
        self._mag = WeightedAverageVector(self.moving_average_window_size_mag)
        self._temp = WeightedAverageVector(self.moving_average_window_size_temp)
        while self.is_running():
            iterations += 1
            data = self.bus.read_i2c_block_data(MPU9250_ADDRESS, ACCEL_DATA_REG, 14)  # Read Accel, Temp, and Gyro
            self._gyro.add(vector_from(data, GYRO_OFFSET, GYRO_RANGE_CONV, endian_transformer_fn=math.c_short_to_big_endian))
            self._accel.add(vector_from(data, ACCEL_OFFSET, ACCEL_RANGE_CONV, endian_transformer_fn=math.c_short_to_big_endian))
            self._temp.add([(math.c_short_to_big_endian(data[TEMP_OFFSET], data[TEMP_OFFSET + 1]) -
                             ROOM_TEMP_OFFSET) / TEMP_SENSITIVITY + 21.0])
            data = self.bus.read_i2c_block_data(AK8963_ADDRESS, MAG_DATA_REG, 7)  # Read Magnetometer and ST2
            if not MAG_ST2_MAG_OVERFLOW & data[6]:  # data[6] is MAG_ST2_REGISTER. Ignore magnetic overflows.
                self._mag.add(vector_from(data, 0, MAG_RANGE_CONV, endian_transformer_fn=math.c_short_to_little_endian))
            self.sample_rate_hz = iterations / (time() - start_time_s)
            if iterations > 1000:
                # Occasionally reset start time and iterations to avoid sample_rate_hz getting too heavily based on the past.
                iterations = 0
                start_time_s = time()
        print("INFO: imu9250 monitor exited")

    def accel(self):
        return apply_operation(lambda x, y: x - y,
                               self._accel.value,
                               self.accel_bias)

    def gyro(self):
        return apply_operation(lambda x, y: x - y,
                               self._gyro.value,
                               self.gyro_bias)

    def mag(self):
        # (mag_avg * mag_calib - mag_bias) * mag_scale
        return apply_operation(lambda x, y: x * y,
                               apply_operation(lambda x, y: x - y,
                                               apply_operation(lambda x, y: x * y,
                                                               self._mag.value,
                                                               self.mag_calib),
                                               self.mag_bias),
                               self.mag_scale)

    def temp(self):
        return self._temp.value[0] - self.temp_bias


def get_interface(cfg, bus=1):
    return Mpu9250(cfg=cfg, bus=bus)
