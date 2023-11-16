export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
export PYTHONPATH=$BASEDIR
cd $PYTHONPATH
sudo modprobe i2c-dev
sudo PYTHONPATH=$PYTHONPATH python -m flask --app web/autopilot_web_app run -h 0.0.0.0 -p 80
