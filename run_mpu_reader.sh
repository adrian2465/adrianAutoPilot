export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
export PYTHONPATH=$BASEDIR
cd $PYTHONPATH

echo "Setting up MPU"
sudo modprobe i2c-dev
sudo i2cdetect -y 1

echo "Reading from MPU 9250"
sudo PYTHONPATH=$PYTHONPATH python testing/mpu9250_monitor_to_console.py
