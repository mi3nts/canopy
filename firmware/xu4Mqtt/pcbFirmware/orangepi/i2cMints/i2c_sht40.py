import time
import datetime
import math
from collections import OrderedDict
from smbus2 import i2c_msg

SHT40_I2C_ADDR = 0x44  # Default I2C address for SHT40

class SHT40:

    def __init__(self, i2c_dev, debugIn):
        self.i2c_addr = SHT40_I2C_ADDR
        self.i2c      = i2c_dev
        self.debug    = debugIn

    def initiate(self, retriesIn):
        print("============== SHT40 ==============")
        ready = None
        while ready is None and retriesIn > 0:
            try:
                # Test connectivity by sending a soft reset command (0x94)
                msg = i2c_msg.write(self.i2c_addr, [0x94])
                self.i2c.i2c_rdwr(msg)
                time.sleep(0.01)
                ready = True
            except OSError:
                pass
            time.sleep(1)
            retriesIn -= 1

        if not ready:
            time.sleep(1)
            return False
        else:
            print("SHT40 Found")
            time.sleep(1)
            return True

    def calculate_dew_point(self, temp, humid):
        if humid <= 0:
            return -100.0
        dew_point = 243.04 * (math.log(humid / 100.0) + ((17.625 * temp) / (243.04 + temp))) / (17.625 - math.log(humid / 100.0) - ((17.625 * temp) / (243.04 + temp)))
        return dew_point

    def read_raw(self):
        """Perform high-precision measurement on SHT40 using smbus2 i2c_rdwr"""
        # Send command: 0xFD (High precision measurement)
        write_msg = i2c_msg.write(self.i2c_addr, [0xFD])
        self.i2c.i2c_rdwr(write_msg)
        
        # High-precision measurement duration is ~8.3ms
        time.sleep(0.01)

        # Read 6 bytes: [Temp MSB, Temp LSB, Temp CRC, Humid MSB, Humid LSB, Humid CRC]
        read_msg = i2c_msg.read(self.i2c_addr, 6)
        self.i2c.i2c_rdwr(read_msg)
        data = list(read_msg)

        # Raw values to physical values conversion according to Sensirion datasheet formulas
        t_ticks = (data[0] << 8) | data[1]
        rh_ticks = (data[3] << 8) | data[4]

        temperature = -45.0 + 175.0 * (t_ticks / 65535.0)
        humidity = -6.0 + 125.0 * (rh_ticks / 65535.0)

        # Constrain relative humidity within valid 0-100% boundary
        humidity = max(0.0, min(100.0, humidity))

        return temperature, humidity

    def read(self):
        """Returns a list matching the BME280 format: [dateTime, temperature, humidity, dewPoint]"""
        dateTime = datetime.datetime.now()
        try:
            temp, humid = self.read_raw()
            dew_point = self.calculate_dew_point(temp, humid)
            return [dateTime, temp, humid, dew_point]
        except Exception as e:
            if self.debug:
                print(f"Error reading SHT40: {e}")
            time.sleep(1)
            print("SHT40 Measurements not read")
            return []

    def read_dict(self):
        dateTime = datetime.datetime.now()
        try:
            temp, humid = self.read_raw()
            dew_point = self.calculate_dew_point(temp, humid)

            sensor_data = OrderedDict()
            sensor_data["dateTime"]    = dateTime.strftime("%Y-%m-%d %H:%M:%S.%f")
            sensor_data["temperature"] = round(temp, 2)
            sensor_data["humidity"]    = round(humid, 2)
            sensor_data["dewPoint"]    = round(dew_point, 2)
            return sensor_data
        except Exception as e:
            if self.debug:
                print(f"Error reading SHT40 into OrderedDict: {e}")
            return OrderedDict()