import datetime
import time
import board
import adafruit_ltr390
from collections import OrderedDict

from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsDefinitions as mD

def main():
    i2c = board.I2C()
    ltr = adafruit_ltr390.LTR390(i2c)

    while True:
        dateTime = datetime.datetime.now()
        UV = ltr.uvs
        Ambient = ltr.light
        UVI = ltr.uvi
        lux = ltr.lux
        sensorDictionary = OrderedDict([
            ("dateTime", str(dateTime)),
            ("UV", UV),
            ("Ambient", Ambient),
            ("UVI", UVI),
            ("Lux", lux)
        ])

        mSR.sensorFinisher(dateTime, "LTR390V2", sensorDictionary)
        time.sleep(1.0)

if __name__ == "__main__":
    print("========= MINTS LTR SENSOR READER ============")
    main()