#!/bin/bash
export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
echo "Reading from arduino"
cd $BASEDIR/testing
python read_from_arduino.py
