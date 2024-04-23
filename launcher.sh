#!/bin/bash

#sudo rfcomm bind rfcomm0 98:D3:32:30:DC:46
#ls -l
#qjoypad PS3_Rev2 &
#qjoypad /home/pi/Desktop/new_ps3_layout.lyt
#sleep 1
#sleep 3
#cd /home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2
#python3 RPi4MasterScriptDirect.py
#python3 test-speaker.py
#python3 test-sabre.py
#python3 dev_r2d2.py
#sleep 10000

cd /home/pi/Desktop/r2d2-2023-embedded-controller/new-r2d2-code/2023R2
python3 2304-wrktrm.py 

sleep 10000
