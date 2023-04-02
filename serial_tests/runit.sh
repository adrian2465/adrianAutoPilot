. /mnt/mmcblk0p2/venv/bin/activate
sudo modprobe i2c-dev
sudo i2cdetect -y 1
sudo python mpu9250-demo-soup-to-nuts.py
