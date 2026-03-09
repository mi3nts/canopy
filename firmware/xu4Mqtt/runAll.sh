#!/bin/bash

sleep 55

kill $(pgrep -f 'python3 gpsReader.py')
sleep 5
python3 ips7100ReaderV1.py &
sleep 5

kill $(pgrep -f 'python3 rsFsxcs.py')
sleep 5
python3 i2cAndUsbGPSReader.py &
sleep 5


kill $(pgrep -f 'python3 inaBasicReader.py')  
sleep 5 
python3 rg15Reader.py &
sleep 5


kill $(pgrep -f 'python3 sen0463.py')  
sleep 5
python3 sen0463.py &
sleep 5

kill $(pgrep -f 'python3 ltr390.py')
sleep 5
python3 ltr390.py &
sleep 5

kill $(pgrep -f 'python3 sjh5aReader.py')
sleep 5
python3 sjh5aReader.py &
sleep 5

#python3 ipReader.py
#sleep 5