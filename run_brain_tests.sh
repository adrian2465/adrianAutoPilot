export BASEDIR=/mnt/mmcblk0p2/apps/adrianAutoPilot
export PYTHONPATH=$BASEDIR
cd $PYTHONPATH
sudo PYTHONPATH=$PYTHONPATH python modules/brain.py 300
