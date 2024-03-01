# Should be deployed to /home/tc
LOG=/home/tc/run_webserver.log
touch $LOG
chown tc:staff $LOG
echo "$(date) Waiting for mydrive..." >> $LOG 2>&1
mydrive_uuid="a36eaf4a-7bdc-4836-83cd-8001db75865a"
mydrive=""
while [ -z "$mydrive" ]
do
   sleep 1
   mydrive=`blkid -U $mydrive_uuid`
done
echo "$(date)  Found mydrive $mydrive for UUID $mydrive_uuid. Starting webserver." >> $LOG 2>&1
export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
export PYTHONPATH=$BASEDIR
cd $PYTHONPATH
echo "$(date) pwd = $(pwd)" >> $LOG 2>&1
echo "$(date) whoami = $(whoami)" >> $LOG 2>&1
sudo modprobe i2c-dev >> $LOG 2>&1
. /mnt/mmcblk0p2/venv/bin/activate >> $LOG 2>&1
sudo python -m flask --app web/autopilot_web_app run -h 0.0.0.0 -p 80 >> $LOG 2>&1
# sudo python -m flask --app web/autopilot_web_app run -h 0.0.0.0 -p 80 
