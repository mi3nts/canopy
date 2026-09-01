#!/usr/bin/python
# ***************************************************************************
#   I2CPythonMints
#   ---------------------------------
#   Written by: Lakitha Omal Harindha Wijeratne
#   - for -
#   MINTS :  Multi-scale Integrated Sensing and Simulation
#     & 
#   TRECIS: Texas Research and Education Cyberinfrastructure Services
#
#   ---------------------------------
#   Date: July 7th, 2022
#   ---------------------------------
#   This module is written for generic implimentation of MINTS projects
#   --------------------------------------------------------------------------
#   https://github.com/mi3nts
#   https://trecis.cyberinfrastructure.org/
#   http://utdmints.info/
#  ***************************************************************************



import sys
import time
import os
import smbus2
import datetime

from i2cMints.i2c_ips7100 import IPS7100
from mintsXU4 import mintsSensorReader as mSR
from mintsPMCorrections import corrections as corr
from collections import OrderedDict

debug        = False 
bus          = smbus2.SMBus(3)
sensor       = "IPS7100"

# IPS7100
ips7100      = IPS7100(bus,debug)

checkTrials  = 0
loopInterval = 1 

def main(loopInterval):
    ips7100_valid   = ips7100.initiate(30)
    
    startTime    = time.time()

    while True:
       try:
            print("======= IPS7100 ========")
            if ips7100_valid:
                raw_data = ips7100.read()
                dateTime = str(datetime.datetime.now())
                mSR.IPS7100WriteI2c(raw_data)
                pm_dict = OrderedDict([
                    ("dateTime" , dateTime),
                    ("pc0_1"    , raw_data[1]), 
                    ("pc0_3"    , raw_data[2]),
                    ("pc0_5"    , raw_data[3]),
                    ("pc1_0"    , raw_data[4]),
                    ("pc2_5"    , raw_data[5]),
                    ("pc5_0"    , raw_data[6]), 
                    ("pc10_0"   , raw_data[7]),
                    ("pm0_1"    , raw_data[8]),
                    ("pm0_3"    , raw_data[9]),
                    ("pm0_5"    , raw_data[10]), 
                    ("pm1_0"    , raw_data[11]),
                    ("pm2_5"    , raw_data[12]),
                    ("pm5_0"    , raw_data[13]),         
                    ("pm10_0"   , raw_data[14])
                ])
                print("types:", type(dateTime), type(pm_dict.get('pc0_1')))
                corr.doPrediction(sensor, pm_dict, datetime.datetime.now())
            time.sleep(.5)    
            startTime = mSR.delayMints(time.time() - startTime,loopInterval)
            
       except Exception as e:
            print(e)
            time.sleep(10)


if __name__ == "__main__":
    print("=============")
    print("    MINTS    ")
    print("=============")
    print("Monitoring Climate data for Minty Cube")
    main(loopInterval)
