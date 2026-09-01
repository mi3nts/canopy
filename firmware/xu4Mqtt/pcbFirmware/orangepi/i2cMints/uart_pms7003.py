import datetime
import serial
import time
from collections import OrderedDict

class PMS7003:

    def __init__(self, serial_port, baud_rate=9600, debug=False):
        self.port = serial_port
        self.baud = baud_rate
        self.debug = debug
        self.ser = None

    def initiate(self, retries=10):
        print(f"============== PMS7003 ({self.port}) ==============")
        while retries > 0:
            try:
                self.ser = serial.Serial(self.port, baudrate=self.baud, timeout=2)
                if self.ser.is_open:
                    print(f"PMS7003 connected successfully on {self.port}")
                    return True
            except Exception as e:
                if self.debug:
                    print(f"PMS7003 init attempt failed: {e}")
                time.sleep(1)
                retries -= 1

        print(f"[ERROR] Could not open serial port {self.port} for PMS7003")
        return False

    def read(self):
        dateTime = datetime.datetime.now()

        if self.ser is None or not self.ser.is_open:
            print("[ERROR] PMS7003 serial port is not open")
            return OrderedDict()

        try:
            # Look for 32-byte frame header 0x42 0x4D
            while True:
                header = self.ser.read(2)
                if len(header) < 2:
                    return OrderedDict()
                if header[0] == 0x42 and header[1] == 0x4D:
                    break

            data = self.ser.read(30)
            if len(data) < 30:
                return OrderedDict()

            # Verify checksum
            checksum = 0x42 + 0x4D + sum(data[:28])
            expected_checksum = (data[28] << 8) | data[29]

            if checksum != expected_checksum:
                if self.debug:
                    print("[WARNING] PMS7003 checksum mismatch")
                return OrderedDict()

            # Parse Standard (CF=1) and Atmospheric PM values
            pm1_0_std  = (data[2]  << 8) | data[3]
            pm2_5_std  = (data[4]  << 8) | data[5]
            pm10_0_std = (data[6]  << 8) | data[7]

            pm1_0_atm  = (data[8]  << 8) | data[9]
            pm2_5_atm  = (data[10] << 8) | data[11]
            pm10_0_atm = (data[12] << 8) | data[13]

            # Particle counts per 0.1L air
            p_0_3 = (data[14] << 8) | data[15]
            p_0_5 = (data[16] << 8) | data[17]
            p_1_0 = (data[18] << 8) | data[19]
            p_2_5 = (data[20] << 8) | data[21]
            p_5_0 = (data[22] << 8) | data[23]
            p_10  = (data[24] << 8) | data[25]

            sensor_data = OrderedDict([
                ("dateTime"      , str(dateTime)),
                ("pm1_0_standard", float(pm1_0_std)),
                ("pm2_5_standard", float(pm2_5_std)),
                ("pm10_0_standard", float(pm10_0_std)),
                ("pm1_0_atm"     , float(pm1_0_atm)),
                ("pm2_5_atm"     , float(pm2_5_atm)),
                ("pm10_0_atm"    , float(pm10_0_atm)),
                ("p_0_3"         , float(p_0_3)),
                ("p_0_5"         , float(p_0_5)),
                ("p_1_0"         , float(p_1_0)),
                ("p_2_5"         , float(p_2_5)),
                ("p_5_0"         , float(p_5_0)),
                ("p_10_0"        , float(p_10))
            ])

            return sensor_data

        except Exception as e:
            if self.debug:
                print(f"[ERROR] PMS7003 read exception: {e}")
            return OrderedDict()