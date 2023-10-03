MOUNT=/mnt/mmcblk0p2
source $MOUNT/venv/bin/activate
cd $MOUNT/apps/adrianAutoPilot
sudo modprobe i2c-dev
sudo flask --app web/autopilot_web_app run -h 0.0.0.0 -p 80
