import time
import smbus2
import datetime
from i2cMints.i2c_sht40 import SHT40

from mintsXU4 import mintsSensorReader as mSR

debug = False
bus = smbus2.SMBus(3) # attaches to bus 3 on OrangePi DREAM board

sht40 = SHT40(bus, debug)
if sht40.initiate(30):
    while True:
        dateTime = datetime.datetime.now()

        data_dict = sht40.read_dict()
        print("Output:", data_dict)

        mSR.sensorFinisher(dateTime, "SHT40", data_dict)

        time.sleep(2)