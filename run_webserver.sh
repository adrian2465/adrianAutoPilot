MOUNT=/mnt/mmcblk0p2
source $MOUNT/venv/bin/activate
cd $MOUNT/apps/adrianAutoPilot/web
sudo modprobe i2c-dev
sudo PYTHONPATH=$MOUNT/apps/adrianAutoPilot python  -m flask --app autopilot_web_app run -h 0.0.0.0 -p 80