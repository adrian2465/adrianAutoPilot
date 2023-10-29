# /bin/bash
ADDR="192.168.86.31" # 31 FOR 3.1[41592] (PI)
echo "Deploying to address $ADDR"
cd /Users/avrouwenve/Private/adrianAutoPilot
if [ "$1" == "" ]
then
   export timestamp=$(date +%Y%m%d%H%M%S)
   echo "Using timestamp $timestamp"
   target=deployment_$timestamp.tar
   tar --exclude "__pycache__" --exclude log --exclude archive -cf $target configuration modules run_*.sh testing web log
   scp $target tc@$ADDR:/mnt/mmcblk0p2/apps/adrianAutoPilot/$target
else
   target=$1
   echo "Will try to deploy existing remote $target"
fi
ssh tc@$ADDR "(cd /mnt/mmcblk0p2/apps/adrianAutoPilot && touch configuration modules testing web && sudo chmod -R ugo+w modules testing web && rm -fr configuration modules testing web Documents *.sh && tar -xvf $target && rm -f $target && echo Deployment of $target to tc@$ADDR complete. )|| echo Deployment of $target to tc@$ADDR FAILED!"

