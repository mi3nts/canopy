#!/bin/bash

sleep 55

kill $(pgrep -f 'ips7100Reader.py')
sleep 5
python3 ips7100Reader.py &
sleep 5

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
