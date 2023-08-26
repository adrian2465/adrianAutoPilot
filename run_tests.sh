#!/bin/bash
export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
export PYTHONPATH=$BASEDIR/web
cd $PYTHONPATH/modules
#
echo "Testing arduino serial interface"
python arduinoSerialInterface.py
#
echo "Testing IMU connectivity"
$BASEDIR/setup_mpu.sh
sudo PYTHONPATH=$PYTHONPATH python mpu9250Interface.py
