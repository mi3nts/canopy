#!/usr/bin/env python3

import sys
import time
import signal

from i2cMints.uart_pms7003 import PMS7003
from mintsXU4 import mintsSensorReader as mSR

# ----------------------------------------------------------------- config
debug            = False
portIn           = "/dev/ttyS5"   # requires uart5 overlay in /boot/armbianEnv.txt
sensorName       = "PMS7003"
loopInterval     = 5              # seconds between samples

passiveMode      = True           # request each frame; avoids stale buffered data
skipWarmup       = True           # block ~30 s after fan start before logging
legacySchema     = True           # emit only the original 13 keys
useUTC           = False          # match whatever the rest of your nodes use

maxFailures      = 5              # consecutive bad reads before forcing reconnect
reconnectBackoff = 5              # seconds between reconnect attempts

# ------------------------------------------------------------- lifecycle
_running = True


def _shutdown(signum, frame):
    global _running
    _running = False
    print(f"\n[{sensorName}] signal {signum} received, shutting down")


signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


def connect(pms, retries):
    """Open the port and, if requested, block through the fan warm-up."""
    if not pms.open(retries=retries):
        return False
    if skipWarmup and not pms.warm:
        print(f"[{sensorName}] warming up ({int(pms.WARMUP_S)} s)...")
        pms.wait_warm()
    return True


# ------------------------------------------------------------------ main
def main():
    pms = PMS7003(portIn, passive=passiveMode, utc=useUTC, debug=debug)

    connected = connect(pms, retries=10)
    if not connected:
        print(f"[{sensorName}] initial connection failed, will keep retrying")

    failures = 0
    startTime = time.time()

    while _running:
        try:
            if not connected:
                connected = connect(pms, retries=3)
                if not connected:
                    time.sleep(reconnectBackoff)
                    continue
                failures = 0

            dateTime, sensor_data = pms.read_mints()

            if sensor_data:
                failures = 0
                if sensor_data.get("error_code"):
                    print(f"[{sensorName}] sensor error_code="
                          f"{sensor_data['error_code']}")
                if legacySchema:
                    sensor_data = pms.legacy(sensor_data)
                if debug:
                    print(f"======= {sensorName} ========")
                    print(sensor_data)
                mSR.sensorFinisher(dateTime, sensorName, sensor_data)
            else:
                failures += 1
                print(f"[{sensorName}] read failed ({failures}/{maxFailures})")
                if failures >= maxFailures:
                    print(f"[{sensorName}] forcing reconnect")
                    pms.close()
                    connected = False
                    failures = 0

        except Exception as e:
            print(f"[{sensorName}] error in main loop: {e}")
            try:
                pms.close()
            except Exception:
                pass
            connected = False
            time.sleep(reconnectBackoff)

        startTime = mSR.delayMints(time.time() - startTime, loopInterval)

    try:
        pms.sleep()      # park fan and laser
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