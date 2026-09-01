#!/usr/bin/python
import sys
import time
import os
from collections import OrderedDict
from i2cMints.pms7003 import PMS7003
from mintsXU4 import mintsSensorReader as mSR

debug        = False
portIn       = "/dev/ttyS1"  
sensorName   = "PMS7003"
loopInterval = 5

def main():
    pms = PMS7003(serial_port=portIn, debug=debug)
    valid = pms.initiate(retries=10)

    startTime = time.time()

    while True:
        try:
            if valid:
                sensor_data = pms.read()
                if sensor_data:
                    print(f"======= {sensorName} ========")
                    print(sensor_data)
                    
                    mSR.sensorFinisher(sensor_data["dateTime"], sensorName, sensor_data)

            time.sleep(1)
            startTime = mSR.delayMints(time.time() - startTime, loopInterval)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("=============")
    print("    MINTS    ")
    print("=============")
    print(f"Monitoring {sensorName} on port {portIn}")
    main()