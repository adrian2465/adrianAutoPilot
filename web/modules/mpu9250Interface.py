from __future__ import print_function
from __future__ import division
import smbus2 as smbus
from time import sleep, time
from ctypes import c_short  # for signed int. c_short is 16 bits, signed (-32768 to 32767)
from modules.imuInterface import imu_interface
from vectormath import moving_average_vector, moving_average_scalar, subtr, mult, vector_from_data

def v_op(fun, vector1, vector2):
    if len(vector1) != len(vector2):
        raise Exception(f"{vector1} and {vector2} are not the same length")
    result_vector = [0] * len(vector1)
    for i, d in enumerate(vector1):
        result_vector[i] = fun(d, vector2[i])
    return result_vector

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
# This code should be run as root to access bus(1)

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


def c_short_big_endian(msb, lsb):
    return c_short(lsb | (msb << 8)).value


def c_short_little_endian(msb, lsb):
    return c_short(msb | (lsb << 8)).value


class mpu9250_interface(imu_interface):
    def __init__(self, config, bus):
        """
        Initialize the IMU
        """
        super().__init__()
        self._mag = None
        self._gyro = None
        self._temp = None
        self._accel = None
        self.bus = smbus.SMBus(bus)

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

        self._mag_avg = [0] * 3
        self._gyro_avg = [0] * 3
        self._accel_avg = [0] * 3
        self._temp_avg = 0
        self._turn_rate_dps = 0

        mpu = config.mpu
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
        self.bus.write_byte_data(MPU9250_ADDRESS, PWR_MGMT_1_REG, 0x00)  # turn MPU mode off
        self.bus.close()
        print("INFO: Bus closed. MPU off.")

    def monitor(self):
        print("INFO: imu9250 monitor running")
        iterations = 0
        start_time_s = time()
        first_gyro_reading = True
        first_accel_reading = True
        first_temp_reading = True
        first_mag_reading = True
        while (self.is_running):
            iterations += 1
            data = self.bus.read_i2c_block_data(MPU9250_ADDRESS, ACCEL_DATA_REG, 14)  # Read Accel, Temp, and Gyro
            self._gyro = vector_from_data(data, GYRO_OFFSET, GYRO_RANGE_CONV, c_short_fn=c_short_big_endian)
            self._gyro_avg = self._gyro if first_gyro_reading else moving_average_vector(self._gyro_avg, self._gyro, self.moving_average_window_size_gyro)
            first_gyro_reading = False
            self._accel = vector_from_data(data, ACCEL_OFFSET, ACCEL_RANGE_CONV, c_short_fn=c_short_big_endian)
            self._accel_avg = self._accel if first_accel_reading else moving_average_vector(self._accel_avg, self._accel, self.moving_average_window_size_accel)
            first_accel_reading = False
            self._temp = (c_short_big_endian(data[TEMP_OFFSET], data[TEMP_OFFSET + 1]) - ROOM_TEMP_OFFSET) / TEMP_SENSITIVITY + 21.0
            self._temp_avg = self._temp if first_temp_reading else moving_average_scalar(self._temp_avg, self._temp, self.moving_average_window_size_temp)
            first_temp_reading = False
            data = self.bus.read_i2c_block_data(AK8963_ADDRESS, MAG_DATA_REG, 7)  # Read Magnetometer and ST2
            if not MAG_ST2_MAG_OVERFLOW & data[6]:  # data[6] is MAG_ST2_REGISTER. Ignore magnetic overflows.
                self._mag = vector_from_data(data, 0, MAG_RANGE_CONV, c_short_fn=c_short_little_endian)
                self._mag_avg = self._mag if first_mag_reading else moving_average_vector(self._mag_avg, self._mag, self.moving_average_window_size_mag)
                first_mag_reading = False
            self.sample_rate_hz = iterations / (time() - start_time_s)
            if iterations > 1000:
                # Occasionally reset start time and iterations to avoid sample_rate_hz getting too heavily based on the past.
                iterations = 0
                start_time_s = time()
        print("INFO: imu9250 monitor exited")

    @property
    def accel(self):
        return v_op(subtr, self._accel_avg, self.accel_bias)

    @property
    def gyro(self):
        return v_op(subtr, self._gyro_avg, self.gyro_bias)

    @property
    def mag(self):
        # (mag_avg * mag_calib - mag_bias) * mag_scale
        return v_op(mult, v_op(subtr, v_op(mult, self._mag_avg, self.mag_calib), self.mag_bias), self.mag_scale)

    @property
    def temp(self):
        return subtr(self._temp_avg, self.temp_bias)

def get_interface(config, bus=1):
    return mpu9250_interface(config=config, bus=bus)



if __name__ == "__main__":
    imu = get_interface()
    imu.start()
    seconds_for_calibration = 10
    try:
        while True:
            print(f'sample_freq={imu.sample_rate_hz} hz')
            print(f'g = {imu.gyro} dps')
            print(f'a = {imu.accel} G')
            print(f't = {imu.temp} C')
            print(f'm = {imu.mag} uT')
            print(f'Heel = {imu.heel_deg()} deg')
            print(f'Compass = {imu.compass_deg()}')
            sleep(1)


    except KeyboardInterrupt:
        imu.stop()
        print('Bye')
