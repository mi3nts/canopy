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

    def _transfer(self, command, bytes_to_read):
        initial_1 = self.spi.xfer2([command])[0]
        time.sleep(0.01) 
        initial_2 = self.spi.xfer2([command])[0]

        valid = (initial_1 == 0x31 and initial_2 == 0xF3)

        data = []
        for _ in range(bytes_to_read):
            time.sleep(0.00001) 
            data.append(self.spi.xfer2([command])[0])

        return valid, data
    
    def set_fan_laser(self, on=True):
        valid, _ = self._transfer(0x03, 1) 
        if on:
            self._transfer(0x03, 1) 
            self._transfer(0x05, 1) 
        else:
            self._transfer(0x02, 1)
            self._transfer(0x04, 1)
        return valid

    def read_histogram(self):
        """Reads the entire 86-byte histogram and unpacks all fields"""
        valid, data = self._transfer(0x30, 86)
        if not valid:
            return None

        raw = bytes(data)
        parsed = struct.unpack('<24H4HHHfffff4HBBH', raw)
        
        return valid, parsed

    def close(self):
        self.spi.close()
    
if __name__ == "__main__":
    opc = OPCN3(bus=0, device=0)
    print("=== MINTS OPC-N3 Reader ===")
    
    try:
        opc.set_fan_laser(True)
        time.sleep(2)
        opc.read_histogram() # Dummy read
        time.sleep(1)

        while True:
            result = opc.read_histogram()
            if result:
                valid_bool, d = result
                dateTime = datetime.datetime.now()

                sensorDictionary = OrderedDict([
                    ("dateTime", str(dateTime)),
                    ("valid", "1" if valid_bool else "0"),
                ])
                
                for i in range(24):
                    sensorDictionary[f"binCount{i}"] = d[i]
                
                sensorDictionary.update([
                    ("bin1TimeToCross",      d[24]),
                    ("bin3TimeToCross",      d[25]),
                    ("bin5TimeToCross",      d[26]),
                    ("bin7TimeToCross",      d[27]),
                    ("samplingPeriod",       d[28]),
                    ("sampleFlowRate",       d[29]),
                    ("temperature",          str(d[30] * 1000)), 
                    ("humidity",             str(d[31] * 500)),
                    ("pm1",                  d[32]),
                    ("pm2_5",                d[33]),
                    ("pm10",                 d[34]),
                    ("rejectCountGlitch",    d[35]),
                    ("rejectCountLongTOF",   d[36]),
                    ("rejectCountRatio",     d[37]),
                    ("rejectCountOutOfRange",d[38]),
                    ("fanRevCount",          d[39]),
                    ("laserStatus",          d[40]),
                    ("checkSum",             d[41])
                ])

                print(f"PM2.5: {sensorDictionary['pm2_5']:.2f} | Temp: {d[30]:.1f}C")
                mSR.sensorFinisher(dateTime, "OPCN3", sensorDictionary)

            time.sleep(1)

    except KeyboardInterrupt:
        opc.set_fan_laser(False)
        opc.close()