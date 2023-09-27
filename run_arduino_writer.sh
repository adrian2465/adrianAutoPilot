export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
echo "Sending Commands to Arduino (interactively)"
cd $BASEDIR/testing
python send_to_arduino.py
