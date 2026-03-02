import smbus2
import time
import datetime
from collections import OrderedDict
from mintsI2c.i2c_as7265x import AS7265X
from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsDefinitions  as mD

def main():
    try:
        bus = smbus2.SMBus(0)
    except Exception as e:
        print(f"I2C Bus Error: {e}")
        return
    sensor = AS7265X(bus, debugIn=False)

    print("Initializing AS7265X Spectral Sensor...")
    if not sensor.initiate():
        print("ERROR: Failed to initialize AS7265X. Check connections.")
        return
    
    wavelength_map = {
        'A': 410, 'B': 435, 'C': 460, 'D': 485, 'E': 510, 'F': 535,
        'G': 560, 'H': 585, 'R': 610, 'I': 645, 'S': 680, 'J': 705,
        'T': 730, 'U': 760, 'V': 810, 'W': 860, 'K': 900, 'L': 940
    }
    
    channel_list = ['A','B','C','D','E','F','G','H','R','I','S','J','T','U','V','W','K','L']

    try:
        while True:
            raw_data = sensor.read()
            dateTime = datetime.datetime.now()

            if raw_data is None:
                print("Read error: No data received")
            else:
                sensorDictionary = OrderedDict([
                    ("dateTime", str(dateTime))
                ])

                for i, channel in enumerate(channel_list):
                    key = f"wave_{wavelength_map[channel]}nm"
                    sensorDictionary[key] = raw_data[i]

                sensorDictionary["temp_avg"] = sensor.getTemperatureAverage()
                mSR.sensorFinisher(dateTime, "AS7265X", sensorDictionary)
            
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping AS7265X Reader...")
        sensor.shut_down()

if __name__ == "__main__":
    print("=== MINTS AS7265X Spectrometer Reader ===")
    main()