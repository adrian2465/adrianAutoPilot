export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
export PYTHONPATH=$BASEDIR/web
cd $PYTHONPATH/modules
#
echo "Running arduinoSerialInterface test suite"
python arduinoSerialInterface.py
