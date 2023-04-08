if [ $(whoami) != "root" ]
then
   echo "Must be root"
   exit 1
fi
sudo modprobe i2c-dev
cd ..
export PYTHONPATH=/mnt/mmcblk0p2/apps/adrianAutoPilot/web
python web/modules/mpu9250Interface.py
