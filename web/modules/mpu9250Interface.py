from __future__ import print_function
from __future__ import division
import smbus2 as smbus
from time import sleep
import ctypes  # for signed int
from modules.imuInterface import imu_interface

moving_average_size = 5  # Number of samples to combine for an average
# Enabling the i2c interface for reading the mpu9250
# Manually create the i2c device: $ sudo modprobe i2c-dev
# Now you should have /dev/i2c-1
# If you now run: $ sudo i2cdetect -y 1  # Found in i2c-tools
# you will get a hexdump with one or two numbers in it. These are the IMU addresses:
# * MPU9250_ADDRESS = 0x68
# * AK8963_ADDRESS = 0x0C
# 0x0c may not appear until after you run this code, due to some pin enablement that happens.
#
# This code should be run as root.
################################
# MPU9250
################################
MPU9250_ADDRESS = 0x68
AK8963_ADDRESS = 0x0C
DEVICE_ID = 0x71
WHO_AM_I = 0x75
PWR_MGMT_1 = 0x6B
INT_PIN_CFG = 0x37
INT_ENABLE = 0x38
# --- Accel ------------------
ACCELEROMETER_DATA_REGISTER = 0x3B
ACCEL_CONFIG = 0x1C
ACCEL_CONFIG2 = 0x1D
ACCEL_2G = 0x00
ACCEL_4G = (0x01 << 3)
ACCEL_8G = (0x02 << 3)
ACCEL_16G = (0x03 << 3)
# --- Temp --------------------
TEMP_DATA = 0x41
# --- Gyro --------------------
GYRO_DATA_REGISTER = 0x43
GYRO_CONFIG = 0x1B
GYRO_250DPS = 0x00
GYRO_500DPS = (0x01 << 3)
GYRO_1000DPS = (0x02 << 3)
GYRO_2000DPS = (0x03 << 3)

# --- AK8963 ------------------
MAGNETOMETER_DATA_REGISTER = 0x03
AK8963_DEVICE_ID = 0x48
AK8963_WHO_AM_I = 0x00
AK8963_8HZ = 0x02
AK8963_100HZ = 0x06
AK8963_14BIT = 0x00
AK8963_16BIT = (0x01 << 4)
AK8963_CNTL1 = 0x0A
AK8963_CNTL2 = 0x0B
AK8963_ASAX = 0x10
AK8963_ST1 = 0x02
AK8963_ST2 = 0x09
AK8963_ASTC = 0x0C
ASTC_SELF = 0x01 << 6



def _moving_average_vector(average_vector, val_vector):
    rc_vector = [0, 0, 0]
    for i in range(0, 3):
       rc_vector[i] = (val_vector[i]  + average_vector[i] * (moving_average_size - 1)) / moving_average_size
    return rc_vector

def _moving_average_scalar(average, val):
    return (val + average * (moving_average_size - 1)) / moving_average_size



class mpu9250_interface(imu_interface):
    def __init__(self, bus):
        """
        Setup the IMU

        reg 0x25: SAMPLE_RATE= Internal_Sample_Rate / (1 + SMPLRT_DIV)
        reg 0x29: [2:0] A_DLPFCFG Accelerometer low pass filter setting
            ACCEL_FCHOICE 1
            A_DLPF_CFG 4
            gives BW of 20 Hz
        reg 0x35: FIFO disabled default - not sure i want this ... just give me current reading

        might include an interface where you can change these with a dictionary:
            setup = {
                ACCEL_CONFIG: ACCEL_4G,
                GYRO_CONFIG: AK8963_14BIT | AK8963_100HZ
            }
        """
        super().__init__()
        self.bus = smbus.SMBus(bus)

        # let's double check we have the correct device address
        ret = self._read_byte(MPU9250_ADDRESS, WHO_AM_I)
        if ret is not DEVICE_ID:
            raise Exception('MPU9250: init failed to find device')

        self._write_byte(MPU9250_ADDRESS, PWR_MGMT_1, 0x00)  # turn sleep mode off
        sleep(0.2)
        self.bus.write_byte_data(MPU9250_ADDRESS, PWR_MGMT_1, 0x01)  # auto select clock source
        self._write_byte(MPU9250_ADDRESS, ACCEL_CONFIG, ACCEL_2G)
        self.accel_coef = 2.0 / 32767  # ACCEL_2G
        self._write_byte(MPU9250_ADDRESS, GYRO_CONFIG, GYRO_250DPS)
        self.gyro_coef = 250.0 / 32767  # GYRO_250DPS

        # You have to enable the other chips to join the I2C network
        # then you should see 0x68 and 0x0c from:
        # sudo i2cdetect -y 1
        self._write_byte(MPU9250_ADDRESS, INT_PIN_CFG, 0x22)
        self._write_byte(MPU9250_ADDRESS, INT_ENABLE, 0x01)
        self.mag_coef = 4800.0 / 32767  # MAGNET range +-4800
        sleep(0.1)

        ret = self._read_byte(AK8963_ADDRESS, AK8963_WHO_AM_I)
        if ret is not AK8963_DEVICE_ID:
            raise Exception('AK8963: init failed to find device')
        self._write_byte(AK8963_ADDRESS, AK8963_CNTL1, (AK8963_16BIT | AK8963_8HZ))  # cont mode 1
        self._write_byte(AK8963_ADDRESS, AK8963_ASTC, 0)

        self._mag_avg = [0, 0, 0]
        self._gyro_avg = [0, 0, 0]
        self._accel_avg = [0, 0, 0]
        self._temp_avg = 0

    def __del__(self):
        self.bus.close()

    def _write_byte(self, address, register, value):
        self.bus.write_byte_data(address, register, value)

    def _read_byte(self, address, register):
        return self.bus.read_byte_data(address, register)

    def _cshort_big_endian(self, msb, lsb):
        return ctypes.c_short(lsb | (msb << 8)).value

    def _cshort_little_endian(self, msb, lsb):
        return ctypes.c_short(msb | (lsb << 8)).value

    def _read_word(self, address, register):
        data = self.bus.read_i2c_block_data(address, register, 2)
        return self._cshort_big_endian(data[0], data[1])

    def _read_vector(self, address, register, scale, to_cshort):
        """
        Reads x, y, and z axes at once and turns them into a tuple.
        """
        # data is MSB, LSB, MSB, LSB ...
        data = self.bus.read_i2c_block_data(address, register, 6)
        return [to_cshort(data[0], data[1]) * scale,
                to_cshort(data[2], data[3]) * scale,
                to_cshort(data[4], data[5]) * scale]

    @property
    def _accel(self):
        return self._read_vector(MPU9250_ADDRESS, ACCELEROMETER_DATA_REGISTER, self.accel_coef, self._cshort_big_endian)

    @property
    def _gyro(self):
        return self._read_vector(MPU9250_ADDRESS, GYRO_DATA_REGISTER, self.gyro_coef, self._cshort_big_endian)

    @property
    def _temp(self):
        """
        Returns chip temperature in C

        pg 33 reg datasheet:
        pg 12 mpu datasheet:
        Temp_room 21
        Temp_Sensitivity 333.87
        Temp_degC = ((Temp_out - Temp_room)/Temp_Sensitivity) + 21 degC
        """
        return ((self._read_word(MPU9250_ADDRESS, TEMP_DATA) - 21.0) / 333.87) + 21.0  # these are from the datasheets

    @property
    def _mag(self):
        data = self._read_vector(AK8963_ADDRESS, MAGNETOMETER_DATA_REGISTER, self.mag_coef, self._cshort_little_endian)
        self._read_byte(AK8963_ADDRESS, AK8963_ST2)  # TODO: Validate this remark: "needed step for reading magnetic data"
        return data

    def _poll(self):
        self._mag_avg = _moving_average_vector(self.mag, self._mag)
        self._gyro_avg = _moving_average_vector(self.gyro, self._gyro)
        self._accel_avg = _moving_average_vector(self.accel, self._accel)
        self._temp_avg = _moving_average_scalar(self.temp, self._temp)

    def monitor(self):
        print("imu9250 monitor started")
        while (self.is_running):
            sleep(self.get_check_interval)
            self._poll()
        print("imu9250 monitor terminated")

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


if __name__ == "__main__":

    imu = get_interface()
    imu.start()
    try:
        while True:
            a = imu.accel
            g = imu.gyro
            m = imu.mag
            print(f'comp={imu.compass_deg: .3f} '
                  f'temp={imu.temp: .1f} '
                  f'a=[{a[0]: .3f},{a[1]: .3f},{a[2]: .3f}] '
                  f'g=[{g[0]: .3f},{g[1]: .3f},{g[2]: .3f}] '
                  f'm=[{m[0]: .3f},{m[1]: .3f},{m[2]: .3f}]'
                  f'\n')
            sleep(1)
    except KeyboardInterrupt:
        imu.stop()
        print('imu9250 main loop terminated')
