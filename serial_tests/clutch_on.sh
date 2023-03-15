#!/bin/sh
dev='ttyUSB0'
fqdev="/dev/$dev"
stty -F $fqdev 9600
echo 'c1' > $fqdev
