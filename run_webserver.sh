MOUNT=/mnt/mmcblk0p2
source $MOUNT/venv/bin/activate
cd $MOUNT/apps/adrianAutoPilot
sudo flask --app web/autopilotWebApp run -h 0.0.0.0 -p 80
