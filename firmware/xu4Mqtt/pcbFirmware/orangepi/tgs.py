#!/usr/bin/env python3
"""
MINTS methane node -- Figaro TGS2611-C00 read through an ADS1115.

Adapted from the Odroid/INA219 version. Changes:
  * INA219 bus-voltage read  ->  ADS1115 single-ended conversion on AIN0
  * odroid_wiringpi dropped   (Orange Pi Zero 2W; wiringPiSetup() was unused here)
  * Adafruit/pi-ina219 dependency dropped -- raw /dev/i2c ioctl, no packages
  * voltage -> Rs -> CH4 ppm conversion; read_methane_ppm() returns ppm

Hardware (Dream_V3, checked against the schematic):
  U3 ADS1115  VDD=+3V3, ADDR->GND via R17 10k (JP2 open)  => 0x48
              SDA/SCL = PI6/PI5 (TWI0), header pins 22/15 => /dev/i2c-0
  IC1 pin 3 (sensor +) and pin 4 (heater) -> +5V
  IC1 pin 1 (heater) -> GND
  R3  1k  load resistor RL, IC1 pin 2 -> GND   (net ADS_ANALOG_0)
  R19 10k series protection, RL node -> AIN0
  AIN1..AIN3 are brought out on J10 through R20..R22 (10k)

Conversion
  Divider:      V_RL = Vc * RL / (Rs + RL)        =>  Rs = RL * (Vc / V_RL - 1)
  Power law:    Rs / R0 = (C / C0) ** (-BETA)    =>  C  = C0 * (Rs / R0) ** (-1 / BETA)
  BETA from the Figaro sensitivity spec Rs(9000)/Rs(3000) = 0.60 +/- 0.06:
                BETA = -ln(0.60) / ln(3) = 0.465   (0.37 .. 0.56 across the tolerance)
  Figaro characterises this law over 500 .. 10 000 ppm at 20 C / 65 %RH.
  Values below 500 ppm are an extrapolation; at ambient (~2 ppm) they are not
  quantitative without field calibration against T and H2O (Shah et al., AMT 2023).
"""

import datetime
import fcntl
import math
import os
import struct
import sys
import time
from collections import OrderedDict
from pprint import pprint

from mintsXU4 import mintsSensorReader as mSR

# ---------------------------------------------------------------- config

I2C_BUS       = 0
ADS_ADDR      = 0x48
ADS_CHANNEL   = 0           # AIN0 = RL node (ADS_ANALOG_0)

RL_OHMS       = 1000.0      # R3
VC_VOLTS      = 5.00        # measure the +5V rail at IC1 pin 3 and put the real value here

# Optional ratiometric correction: wire a divider from +5V to a spare input on J10
# (AIN1..AIN3) and set the channel and ratio here. None = use VC_VOLTS.
VC_CHANNEL    = None        # e.g. 1
VC_DIVIDER    = 2.0         # (R_top + R_bottom) / R_bottom of that divider

C0_PPM        = 5000.0      # reference concentration for R0
R0_OHMS       = 5550.0      # Rs at 5000 ppm CH4 -- SPAN CALIBRATE THIS SENSOR
BETA          = -math.log(0.60) / math.log(3.0)   # 0.465, calibrate with a 2nd span point

PPM_SPEC_MIN  = 500.0       # Figaro typical detection range
PPM_SPEC_MAX  = 10000.0

R_SERIES      = 10_000.0    # R19
Z_ADC         = 6.0e6       # ADS1115 common-mode input impedance at FSR +/-4.096 V
GAIN_CORR     = (Z_ADC + R_SERIES) / Z_ADC

SAMPLES       = 32          # 32 / 128 SPS = 250 ms = 15 mains cycles at 60 Hz
V_CLIP        = 3.20        # above this the 3.3 V-powered ADC is out of range

WARMUP_SECONDS = 60         # Figaro: >=2 min from cold, 7 days to meet full spec
loopInterval   = 1

I2C_SLAVE  = 0x0703
ADS_CONFIG = 0x8383         # OS=1, MUX set per channel, +/-4.096 V, single-shot, 128 SPS, comp off
ADS_LSB    = 4.096 / 32768

startTimePro = time.time()

# ---------------------------------------------------------------- ADC


class ADS1115:
    def __init__(self, bus, address):
        self.fd = os.open("/dev/i2c-%d" % bus, os.O_RDWR)
        fcntl.ioctl(self.fd, I2C_SLAVE, address)

    def _read_reg(self, reg):
        os.write(self.fd, bytes((reg,)))
        return struct.unpack(">H", os.read(self.fd, 2))[0]

    def probe(self):
        """Threshold registers read 0x8000/0x7FFF after reset."""
        return self._read_reg(0x02) == 0x8000 and self._read_reg(0x03) == 0x7FFF

    def counts(self, channel=ADS_CHANNEL):
        cfg = ADS_CONFIG | ((0x4 | channel) << 12)      # MUX = AINx vs GND
        os.write(self.fd, bytes((0x01, cfg >> 8, cfg & 0xFF)))
        deadline = time.time() + 0.1
        while not (self._read_reg(0x01) & 0x8000):
            if time.time() > deadline:
                raise IOError("ADS1115 conversion timeout")
            time.sleep(0.001)
        os.write(self.fd, b"\x00")
        return struct.unpack(">h", os.read(self.fd, 2))[0]

    def volts(self, channel=ADS_CHANNEL, n=SAMPLES):
        return sum(self.counts(channel) for _ in range(n)) / float(n) * ADS_LSB * GAIN_CORR


# ---------------------------------------------------------------- conversion


def supply_voltage():
    """Circuit voltage Vc across sensor + RL."""
    if VC_CHANNEL is None:
        return VC_VOLTS
    return ads.volts(VC_CHANNEL) * VC_DIVIDER


def resistance(v_rl, vc):
    """Sensor resistance Rs from the voltage across RL."""
    if v_rl <= 0.0:
        return float("inf")
    if v_rl >= vc:
        return 0.0
    return (vc / v_rl - 1.0) * RL_OHMS


def rs_to_ppm(rs):
    """Invert Rs/R0 = (C/C0)^-BETA. Returns ppm, or None if Rs is not finite/positive."""
    if not (0.0 < rs < float("inf")):
        return None
    return C0_PPM * (rs / R0_OHMS) ** (-1.0 / BETA)


def read_methane_ppm():
    """
    One averaged measurement. Returns (ppm, voltage, rs, clipped).
    ppm is None when the ADC is clipped: Rs is then only an upper bound,
    so the concentration is only known to be >= the clipped value.
    """
    vc      = supply_voltage()
    voltage = ads.volts(ADS_CHANNEL)
    clipped = voltage >= V_CLIP
    rs      = resistance(voltage, vc)
    conc    = None if clipped else rs_to_ppm(rs)
    return conc, voltage, rs, clipped


# ---------------------------------------------------------------- init

try:
    ads = ADS1115(I2C_BUS, ADS_ADDR)
    if not ads.probe():
        raise IOError("device at 0x%02X is not an ADS1x15" % ADS_ADDR)

except Exception as e:
    time.sleep(.5)
    print("Error and type: %s - %s." % (e, type(e)))
    time.sleep(.5)
    print("Methane Sensor not found")
    time.sleep(.5)
    sys.exit()


def read():
    startTime = time.time()
    while True:
        try:
            dateTime = datetime.datetime.now()

            conc, voltage, rs, clipped = read_methane_ppm()

            # Same keys, same order as before -- data pipeline unchanged.
            sensorDictionary = OrderedDict([
                ("dateTime",            str(dateTime)),
                ("methaneEQBusVoltage", round(voltage, 6)),
                ("methaneEQResistance", round(rs, 1) if rs < 1e9 else None),
                ("methaneEQPPM",        round(conc, 1) if conc is not None else None),
                ("methaneEQClipped",    int(clipped))
            ])

            if conc is not None and not (PPM_SPEC_MIN <= conc <= PPM_SPEC_MAX):
                print("Note: %.1f ppm is outside Figaro's %d-%d ppm characterised range"
                      % (conc, PPM_SPEC_MIN, PPM_SPEC_MAX))

            if time.time() - startTimePro > WARMUP_SECONDS:
                print("Sensor Warmed Up -- CH4: %s ppm" % sensorDictionary["methaneEQPPM"])
                mSR.sensorFinisher(dateTime, "TGS2611C00", sensorDictionary)
            else:
                print("Sensor Not Warmed Up")
                pprint(sensorDictionary)
                print()

            startTime = mSR.delayMints(time.time() - startTime, loopInterval)

        except Exception as e:
            time.sleep(.5)
            print("Error and type: %s - %s." % (e, type(e)))
            time.sleep(.5)
            print("Data Packet Not Sent for Methane")
            time.sleep(.5)


if __name__ == "__main__":
    print("=============")
    print("    MINTS    ")
    print("=============")
    read()
