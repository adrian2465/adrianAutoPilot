import time
from mpu9250_jmdev.registers import *
from math import atan2, pi
from mpu9250_jmdev.mpu_9250 import MPU9250

def calibrate(mpu, retry=3):
    start_time = time.time()
    try:
        print(f"{time.time() - start_time:3.3f}:  Calibrating MPU6500 Primary")
        print("To calibrate, you must correctly position the MPU so that gravity is all along the z axis of the accelerometer.")
        mpu.calibrateMPU6500()
        mpu.configure()
        print(f"{time.time() - start_time:3.3f}:  Calibrating AK8963")
        print("For about 15s, rotate MPU around Z axis 360 degrees, repeatedly.")
        mpu.calibrateAK8963()
        print(f"{time.time() - start_time:3.3f}:  Calibration completed successfully. Results:")
        print(f"gyro: bias: {mpu.gbias}")
        print(f"accel: bias: {mpu.abias}")
        print(f"mag: calibration = {mpu.magCalibration}, bias: {mpu.mbias}, scale: {mpu.magScale}")
    except OSError as err:
        if(retry > 1):
            print(f"{time.time() - start_time:3.3f}:  Got error {err} - RETRYING")
            calibrate(mpu, retry - 1)
        else:
            print(f"{time.time() - start_time:3.3f}: ABORTING")
            raise err
    mpu.configure()


if __name__ == "__main__":
    mpu = MPU9250(
        address_ak=AK8963_ADDRESS,
        address_mpu_master=MPU9050_ADDRESS_68, # In 0x68 Address
        address_mpu_slave=None,
        bus=1,
        gfs=GFS_250,
        afs=AFS_2G,
        mfs=AK8963_BIT_16,
        mode=AK8963_MODE_C100HZ)

    calibrate(mpu)

    print("Sampling Gyro, Acceleromter, and Magnetometer after calibration")
    print("Magnetometer should be correct when turned. Accel and Gyro should be zero when still.")
    print("^C to exit")
    while True:
        print("Accelerometer", mpu.readAccelerometerMaster())
        print("Gyroscope", mpu.readGyroscopeMaster())
        magnetometer = mpu.readMagnetometerMaster()
        print("Magnetometer", magnetometer)
        angle = (atan2(magnetometer[1], magnetometer[0]) * (180 / pi) + 90 + 360) % 360
        print("Compass (deg)", angle)
        print("Temperature", mpu.readTemperatureMaster())
        time.sleep(0.5)
