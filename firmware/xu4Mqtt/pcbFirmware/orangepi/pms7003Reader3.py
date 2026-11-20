#!/usr/bin/env python3
"""
MINTS reader for the Plantower PMS7003 over UART.

Publishes through the unchanged MINTS contract:
    mSR.sensorFinisher(dateTime, sensorName, sensor_data)
where dateTime is a naive datetime.datetime and sensor_data is an OrderedDict
whose first key is "dateTime" as a string.

Output keys follow the pcX_Y / pmX_Y naming (as used for IPS7100-style nodes):
    pc0_3 pc0_5 pc1_0 pc2_5 pc5_0 pc10_0   particle counts
    pm1_0 pm2_5 pm10_0                     mass concentration, ug/m3

The PMS7003 does not measure pc0_1, pm0_1, pm0_3, pm0_5 or pm5_0. Those keys
are omitted unless publishUnmeasured = True, in which case they are published
as None (empty cell in CSV, null in JSON) rather than invented values.

The serial driver is self-contained (no i2cMints dependency). It wakes the
sensor on every connect, which fixes the "sensor left asleep by the previous
run's sleep()" failure, and it resynchronises on the 42 4D header with a
checksum check, so stray ACKs or partial frames are skipped.
"""

import time
import signal
import datetime
from collections import OrderedDict

import serial

from mintsXU4 import mintsSensorReader as mSR

# ----------------------------------------------------------------- config
debug             = False
portIn            = "/dev/ttyS5"  # requires uart5 overlay in /boot/armbianEnv.txt
sensorName        = "PMS7003"
loopInterval      = 5             # seconds between samples

passiveMode       = True          # request each frame; avoids stale buffered data
warmupS           = 30            # datasheet: >= 30 s after wake for stable data
useUTC            = False         # match whatever the rest of your nodes use
sleepOnExit       = True          # park fan/laser on shutdown (we wake on start)

pmSource          = "atm"         # "atm" (atmospheric) or "cf1" (standard particle)
countsPerLiter    = False         # False: native #/0.1 L; True: scale x10 to #/L
differentialCounts = False        # False: cumulative (>= size); True: per bin
publishUnmeasured = False         # True: also emit pc0_1, pm0_1, pm0_3, pm0_5, pm5_0 as None

maxFailures       = 5             # consecutive bad reads before forcing reconnect
reconnectBackoff  = 5             # seconds between reconnect attempts


# ------------------------------------------------------------ PMS7003 driver
def _cmd(c, dl):
    b = [0x42, 0x4D, c, 0x00, dl]
    s = sum(b)
    return bytes(b + [s >> 8, s & 0xFF])


CMD_WAKE    = _cmd(0xE4, 0x01)
CMD_SLEEP   = _cmd(0xE4, 0x00)
CMD_ACTIVE  = _cmd(0xE1, 0x01)
CMD_PASSIVE = _cmd(0xE1, 0x00)
CMD_READ    = _cmd(0xE2, 0x00)

FRAME_LEN = 32


class PMS7003:
    def __init__(self, port, passive=True, debug=False):
        self.port, self.passive, self.debug = port, passive, debug
        self.ser = None

    def _send(self, c):
        self.ser.write(c)
        self.ser.flush()

    def open(self):
        try:
            self.ser = serial.Serial(self.port, 9600, bytesize=8, parity="N",
                                     stopbits=1, timeout=0.2)
            self._send(CMD_WAKE)
            time.sleep(1.0)
            self._send(CMD_PASSIVE if self.passive else CMD_ACTIVE)
            time.sleep(1.0)          # let any in-flight active frame finish
            self.ser.reset_input_buffer()
            return True
        except Exception as e:
            print(f"[{sensorName}] open failed: {e}")
            self.close()
            return False

    def close(self):
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def sleep(self):
        if self.ser is not None:
            self._send(CMD_SLEEP)

    @staticmethod
    def _find_frame(buf):
        """Return the last valid 32-byte data frame in buf, or None."""
        found, i = None, 0
        while i <= len(buf) - FRAME_LEN:
            if (buf[i] == 0x42 and buf[i + 1] == 0x4D
                    and ((buf[i + 2] << 8) | buf[i + 3]) == 28):
                f = buf[i:i + FRAME_LEN]
                if sum(f[:30]) & 0xFFFF == (f[30] << 8) | f[31]:
                    found = bytes(f)
                    i += FRAME_LEN
                    continue
            i += 1
        return found

    def read_frame(self, timeout=2.5):
        """Return a dict of decoded fields, or None on timeout/bad data."""
        if self.passive:
            self.ser.reset_input_buffer()
            self._send(CMD_READ)
        else:
            self.ser.reset_input_buffer()   # want a fresh frame, not a stale one

        buf, t0 = bytearray(), time.time()
        while time.time() - t0 < timeout:
            buf += self.ser.read(self.ser.in_waiting or 1)
            if len(buf) >= FRAME_LEN:
                f = self._find_frame(buf)
                if f is not None:
                    return self._decode(f)
        if self.debug:
            print(f"[{sensorName}] no valid frame; raw: {buf[:48].hex(' ')}")
        return None

    @staticmethod
    def _decode(f):
        w = [(f[4 + 2 * k] << 8) | f[5 + 2 * k] for k in range(13)]
        return {
            "pm1_0_cf1": w[0], "pm2_5_cf1": w[1], "pm10_0_cf1": w[2],
            "pm1_0_atm": w[3], "pm2_5_atm": w[4], "pm10_0_atm": w[5],
            # cumulative counts of particles >= d um per 0.1 L of air
            "n0_3": w[6], "n0_5": w[7], "n1_0": w[8],
            "n2_5": w[9], "n5_0": w[10], "n10_0": w[11],
            "version": f[28], "error_code": f[29],
        }


# ------------------------------------------------------- MINTS dictionary
def build_mints_dict(dateTime, d):
    scale = 10 if countsPerLiter else 1
    cum = [d["n0_3"], d["n0_5"], d["n1_0"], d["n2_5"], d["n5_0"], d["n10_0"]]
    if differentialCounts:
        counts = [max(cum[k] - cum[k + 1], 0) for k in range(5)] + [cum[5]]
    else:
        counts = cum
    counts = [c * scale for c in counts]

    sfx = "atm" if pmSource == "atm" else "cf1"
    pm = {"pm1_0": d[f"pm1_0_{sfx}"],
          "pm2_5": d[f"pm2_5_{sfx}"],
          "pm10_0": d[f"pm10_0_{sfx}"]}

    out = OrderedDict()
    out["dateTime"] = str(dateTime)
    if publishUnmeasured:
        out["pc0_1"] = None
    out["pc0_3"], out["pc0_5"], out["pc1_0"], out["pc2_5"], \
        out["pc5_0"], out["pc10_0"] = counts
    if publishUnmeasured:
        out["pm0_1"] = None
        out["pm0_3"] = None
        out["pm0_5"] = None
    out["pm1_0"] = pm["pm1_0"]
    out["pm2_5"] = pm["pm2_5"]
    if publishUnmeasured:
        out["pm5_0"] = None
    out["pm10_0"] = pm["pm10_0"]
    return out


def now():
    if useUTC:
        return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    return datetime.datetime.now()


# ------------------------------------------------------------- lifecycle
_running = True


def _shutdown(signum, frame):
    global _running
    _running = False
    print(f"\n[{sensorName}] signal {signum} received, shutting down")


signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


def interruptible_sleep(seconds):
    end = time.time() + seconds
    while _running and time.time() < end:
        time.sleep(min(0.5, end - time.time()))


def connect(pms):
    """Wake, set mode, warm up, and discard the first frame."""
    if not pms.open():
        return False
    print(f"[{sensorName}] warming up ({warmupS} s)...")
    interruptible_sleep(warmupS)
    if not _running:
        return False
    pms.read_frame()             # throw away first post-warm-up frame
    return True


# ------------------------------------------------------------------ main
def main():
    pms = PMS7003(portIn, passive=passiveMode, debug=debug)
    connected = connect(pms)
    if not connected and _running:
        print(f"[{sensorName}] initial connection failed, will keep retrying")

    failures = 0
    startTime = time.time()

    while _running:
        try:
            if not connected:
                pms.close()
                connected = connect(pms)
                if not connected:
                    interruptible_sleep(reconnectBackoff)
                    continue
                failures = 0
                startTime = time.time()

            d = pms.read_frame()
            if d is not None:
                failures = 0
                if d["error_code"]:
                    print(f"[{sensorName}] sensor error_code={d['error_code']}")
                dateTime = now()
                sensor_data = build_mints_dict(dateTime, d)
                if debug:
                    print(f"======= {sensorName} ========")
                    print(sensor_data)
                try:
                    mSR.sensorFinisher(dateTime, sensorName, sensor_data)
                except OSError as e:
                    # storage/permission problem, not a sensor fault
                    print(f"[{sensorName}] write failed: {e}")
            else:
                failures += 1
                print(f"[{sensorName}] read failed ({failures}/{maxFailures})")
                if failures >= maxFailures:
                    print(f"[{sensorName}] forcing reconnect (wake + re-warm)")
                    pms.close()
                    connected = False
                    failures = 0
                    continue

        except Exception as e:
            print(f"[{sensorName}] error in main loop: {e}")
            pms.close()
            connected = False
            interruptible_sleep(reconnectBackoff)
            continue

        startTime = mSR.delayMints(time.time() - startTime, loopInterval)

    if sleepOnExit:
        try:
            pms.sleep()
        except Exception:
            pass
    pms.close()
    print(f"[{sensorName}] stopped")


if __name__ == "__main__":
    print("=============")
    print("    MINTS    ")
    print("=============")
    print(f"Monitoring {sensorName} on port {portIn}")
    main()
