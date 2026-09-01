#!/bin/bash

# /home/teamlary/canopy/firmware/xu4Mqtt/pcbFirmware/orangepi/.venv/bin/activate

sleep 55

# First time setup
if [ ! -d "./.venv" ]; then
    ./install.sh || exit 1
fi

kill $(pgrep -f 'python3 bme280Reader.py')
sleep 5
python3 bme280Reader.py &
sleep 5


kill $(pgrep -f 'python3 cozIRReader.py')  
sleep 5
python3 cozIRReader.py &
sleep 5

kill $(pgrep -f 'python3 opcReader.py')  
sleep 5
python3 opcReader.py &
sleep 5

kill $(pgrep -f 'ips7100Reader.py')
sleep 5
python3 ips7100Reader.py &
sleep 5

# sht reader pending testing for rpi dream boards
# kill $(pgrep -f 'sht40Reader.py')
# sleep 5
# python3 sht40Reader.py &
# sleep 5