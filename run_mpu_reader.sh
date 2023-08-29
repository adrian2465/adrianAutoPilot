#!/bin/bash
export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
export PYTHONPATH=$BASEDIR/web
cd $PYTHONPATH/modules
#
echo "Reading from MPU 9250"
$BASEDIR/setup_mpu.sh
sudo PYTHONPATH=$PYTHONPATH python mpu9250Interface.py
