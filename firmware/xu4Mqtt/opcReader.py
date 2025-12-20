# OPC N3 reader, should mostly apply to N2 but with bin differences
# https://parmex.com.mx/show_catalogue_pdf/142183/1

import spidev
import time

spi = spidev.SpiDev()

# SPI bus 0 device 0
spi.open(0, 0)

spi.max_speed_hz = 500000  # 500 KHz
spi.mode = 0b01            # SPI mode 1

def main():
    turnOnFanAndLaser()
    print(getStatus())
    time.sleep(5)
    while True:
        print(readPmData())
        time.sleep(1)

# COMMANDS DEFINED IN APPENDIX D OF DATA SHEET

def turnOnFanAndLaser():
    spi.xfer2([0x03, 0x00])
    time.sleep(0.01)

def turnOffFanAndLaser():
    spi.xfer2([0x03, 0x01])
    time.sleep(0.01)

def turnOnFan():
    spi.xfer2([0x03, 0x04])
    time.sleep(0.01)

def turnOffFan():
    spi.xfer2([0x03, 0x05])
    time.sleep(0.01)

def turnOnLaser():
    spi.xfer2([0x03, 0x02])
    time.sleep(0.01)

def turnOffLaser():
    spi.xfer2([0x03, 0x03])
    time.sleep(0.01)

def getStatus():
    response = spi.xfer2([0x13, 0x00])
    status = response[1]

    fan = bool(status & 0x08)
    laser = bool(status & 0x04)

    return fan, laser

def readPmData():
    response = spi.xfer2([0x32, 0x00])  
    pm1 = (response[0] << 24) | (response[1] << 16) | (response[2] << 8) | response[3] # assuming big endianness
    pm2_5 = (response[4] << 24) | (response[5] << 16) | (response[6] << 8) | response[7]
    pm10 = (response[8] << 24) | (response[9] << 16) | (response[10] << 8) | response[11]
    return pm1, pm2_5, pm10

if __name__ == "__main__":
    print("==============")
    print("    MINTS     ")
    print("==============")
