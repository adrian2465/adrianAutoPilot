import time
from mpu9250_jmdev.registers import *
from math import atan2, pi
from mpu9250_jmdev.mpu_9250 import MPU9250

mpu = MPU9250(
    address_ak=AK8963_ADDRESS,
    address_mpu_master=MPU9050_ADDRESS_68, # In 0x68 Address
    address_mpu_slave=None,
    bus=1,
    gfs=GFS_1000,
    afs=AFS_8G,
    mfs=AK8963_BIT_16,
    mode=AK8963_MODE_C100HZ)

mpu.configure() # Apply the settings to the registers.
# mpu.calibrate()
# mpu.configure() # Reset registers after calibration

while True:

    print("|.....MPU9250 in 0x68 Address.....|")
    print("Accelerometer", mpu.readAccelerometerMaster())
    print("Gyroscope", mpu.readGyroscopeMaster())

    magnetometer = mpu.readMagnetometerMaster()
    print("Magnetometer", mpu.readMagnetometerMaster())
    x = magnetometer[0]
    y = magnetometer[1]
    angle = atan2(y, x)
    angle = angle * (180 / pi)
    angle = angle + 90
    angle = (angle + 360) % 360
    print("Compass (deg)", angle )
    print("Temperature", mpu.readTemperatureMaster())
    print("\n")

    time.sleep(0.5)
