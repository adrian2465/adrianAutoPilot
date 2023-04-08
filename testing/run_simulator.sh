#!/bin/bash
rm -f simulation.log
python3 simulator.py ../configuration/config.yaml $1 $2 $3
# png=$(ls -ta *.png | head -n 1)
# open $png
