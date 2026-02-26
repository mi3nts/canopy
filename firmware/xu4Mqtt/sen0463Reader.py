import serial
import time
import datetime
import re 
from collections import OrderedDict
from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsDefinitions  as mD

ARDUINO_PORT = '/dev/ttyACM0'  
BAUD_RATE = 115200

def extractNumbers(line, isFloat = False):
    if isFloat:
        numbers = re.findall(r'\d+\.\d+', line)
        numbers = ''.join(numbers)
        return float(numbers)
    else:
        numbers = re.findall(r'\d+', line)
        numbers = ''.join(numbers)
        return int(numbers)


def main():
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1) 
        time.sleep(2) 

        print(f"Connected to {ARDUINO_PORT} at {BAUD_RATE} baud.")

        cpm: int = None
        nSvh: int = None
        uSvh: float = None
        
        while True:
            line = ser.readline()

            if not line:
                continue
            
            if line:
                decoded_line = line.decode('utf-8').strip()
                if "CPM" in decoded_line:
                    cpm = int(extractNumbers(decoded_line))
                    print("CPM: ", cpm)
                elif "nSv/h: " in decoded_line:
                    nSvh = int(extractNumbers(decoded_line))
                    print("nSvh: ", nSvh)
                elif "uSv/h" in decoded_line:
                    uSvh = float(extractNumbers(decoded_line, isFloat=True))
                    print("uSvh: ", uSvh)

            if nSvh is not None and uSvh is not None and cpm is not None:
                dateTime = datetime.datetime.now()
                sensorDictionary = OrderedDict([
                    ("dateTime", str(dateTime)),
                    ("cpm", cpm),
                    ("nSv/h", nSvh),
                    ("uSv/h", uSvh)
                ])
                cpm = None      # reset all 3 to only update dict when all found
                nSvh = None
                uSvh = None
                print(sensorDictionary)
                mSR.sensorFinisher(dateTime, "SEN0463", sensorDictionary)
              
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")

    except KeyboardInterrupt:
        print("\nExiting program.")

    finally:
        if 'ser' in locals() and ser.isOpen():
            ser.close()
            print("Serial port closed.\n")

if __name__ == "__main__":
    print("\n======= MINTS RADIATION SENSING =======\n")
    main()
