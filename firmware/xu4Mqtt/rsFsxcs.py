from pymodbus.client import ModbusSerialClient
import struct
import time
import datetime
from collections import OrderedDict
from mintsXU4 import mintsSensorReader as mSR
from mintsXU4 import mintsDefinitions  as mD


def connectClient():
    client = ModbusSerialClient(
        port='/dev/ttyUSB0',
        baudrate=4800,
        bytesize=8,
        parity='N',
        stopbits=1,
        timeout=1
    )

    for attempt in range(5):
        if client.connect():
            print("Sensor RS-FSXCS found!")
            return client
        print("Failed to connect to RS-FSXCS. Retrying...")
        time.sleep(1)

    print("ERROR: Failed to connect to RS-FSXCS.")
    return None


def main():
    client = connectClient()

    if client is None:
        exit()

    try:
        while True:
            response = client.read_holding_registers(
                address=500,
                count=14,
                slave=1
            )

            if response.isError():
                print("Read error")
            else:
                dateTime        = datetime.datetime.now()
                windSpeed       = response.registers[0] / 100
                windForce       = response.registers[1]
                # windDirectionFiles = response.registers[2]?
                windDirection   = response.registers[3]
                humidity        = response.registers[4] / 10
                temperature     = response.registers[5] / 10
                noise           = response.registers[6] / 10
                pm2_5           = response.registers[7]
                pm10            = response.registers[8]
                pressureAtm     = response.registers[9] / 10
                highLux         = response.registers[10]
                lowLux          = response.registers[11]
                totalLux        = (highLux << 16) | lowLux
                lightValue20W   = response.registers[12] * 100      # unit = 100 lux
                opticalRainfall = response.registers[13] / 10

                sensorDictionary = OrderedDict([
                    ("dateTime",        str(dateTime)),
                    ("windSpeed",        windSpeed),
                    ("windForce",        windForce),
                    ("windDirection",    windDirection),
                    ("humidity",         humidity),
                    ("temperature",      temperature),
                    ("noise",            noise),
                    ("PM2.5",            pm2_5),
                    ("PM10",             pm10),
                    ("Pressure(atm)",    pressureAtm),
                    ("totalLux",         totalLux),
                    ("lightValue20W",    lightValue20W),
                    ("rainfall",         opticalRainfall)
                ])

                mSR.sensorFinisher(dateTime, "RS_FSXCS_N01", sensorDictionary)
                # print(sensorDictionary)
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping...")
        client.close()

if __name__ == "__main__":
    print("=== MINTS RS-FSXCS Reader ===")
    main()