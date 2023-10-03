export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
export PYTHONPATH=$BASEDIR
cd $PYTHONPATH
#
echo "Running arduinoSerialInterface test suite"
python testing/arduino_tests.py
