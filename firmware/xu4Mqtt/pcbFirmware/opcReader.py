import spidev
import time
import struct
import datetime
from collections import OrderedDict
from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsDefinitions  as mD

class OPCN3:
    def __init__(self, bus=0, device=0):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = 500000 
        self.spi.mode = 0b01
        self.validator = [0x31, 0xF3]

    def _transfer(self, command, bytes_to_read):
        """Helper to initiate transfer"""

        initial_1 = self.spi.xfer2([command])[0]
        time.sleep(0.01) 
        initial_2 = self.spi.xfer2([command])[0]

        # wait for sensor to be ready
        valid = (initial_1 == 0x31 and initial_2 == 0xF3)

        data = []
        for _ in range(bytes_to_read):
            time.sleep(0.00001) # 10us delay
            data.append(self.spi.xfer2([command])[0])

        return valid, data
    
    def set_fan_laser(self, on=True):
        """Turns fan/laser on/off"""
        valid, _ = self._transfer(0x03, 1) 
        if on:
            self._transfer(0x03, 1) 
            self._transfer(0x05, 1) 
        else:
            self._transfer(0x02, 1)
            self._transfer(0x04, 1)
        return valid

    def read_histogram(self):
        """Reads the entire 86-byte histogram"""
        valid, data = self._transfer(0x30, 86)
        if not valid:
            return None

        raw = bytes(data) # convert byte list to raw bytes for unpacking
        # Alphasense uses 16-bit unsigned integers for bins (first 24 bins = 48 bytes)
        bins = struct.unpack('<24H', raw[0:48])
        pm_values = struct.unpack('<fff', raw[60:72]) # bytes 60 - 72 represent pm1, 2.5, 10
        
        return {
            "bins": bins,
            "pm1": pm_values[0],
            "pm2.5": pm_values[1],
            "pm10": pm_values[2]
        }
    
if __name__ == "__main__":
    opc = OPCN3(bus=0, device=0)
    print("=== MINTS OPC-N3 Reader ===")
    
    try:
        print("Initializing sensor...")
        opc.set_fan_laser(True)
        time.sleep(2) # wait for fan/laser
        opc.read_histogram() # perform one initial read as the first read returns garbage
        time.sleep(1)

        while True:
            data = opc.read_histogram()
            if data:
                pm1 = round(data['pm1'], 3)
                pm2_5 = round(data['pm2.5'],3)
                pm10 = round(data['pm10'],3)
                print(f"Bins: {data['bins']} | PM1: {pm1} | PM2.5: {data['pm2.5']:.2f} | PM10: {data['pm10']:.2f}")
                dateTime = datetime.datetime.now()
                sensorDictionary = OrderedDict([
                ("dateTime",            str(dateTime)),
                ("PM1",         pm1)])
                mSR.sensorFinisher(dateTime, "RS-FSXCS-N01-3", sensorDictionary)

            else:
                print("Waiting for sensor response...")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping sensor...\n")
        opc.set_fan_laser(False)
        opc.close()