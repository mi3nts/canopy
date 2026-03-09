#!/bin/bash

sleep 55
export LD_PRELOAD=/home/teamlary/.local/lib/python3.8/site-packages/scikit_learn.libs/libgomp-d22c30c5.so.1.0.0
sleep 5

kill $(pgrep -f 'python3 audioDeleter.py')
sleep 5
python3 audioDeleter.py &
sleep 30

kill $(pgrep -f 'python3 audioReader.py')
sleep 5
/home/teamlary/gitHubRepos/canopy/firmware/xu4Mqtt/birdSongs/bin/python3 audioReader.py &
sleep 5