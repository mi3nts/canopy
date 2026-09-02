"""
PMS7003 (Plantower) UART driver.

Target: Linux SBC, e.g. Orange Pi Zero 2W (Allwinner H618, Armbian).
Protocol: 9600 8N1, 32-byte big-endian frames, header 0x42 0x4D.

Frame layout (byte offsets within the 32-byte frame):
     0..1   0x42 0x4D
     2..3   frame length field (== 28)
     4..9   PM1.0 / PM2.5 / PM10  CF=1 ("standard", factory calibration)
    10..15  PM1.0 / PM2.5 / PM10  atmospheric
    16..27  particle counts > 0.3, 0.5, 1.0, 2.5, 5.0, 10.0 um per 0.1 L
    28      version
    29      error code
    30..31  checksum = sum(frame[0:30])

Notes on measurement validity:
  - The CF=1 values are the raw factory-calibrated output; the "atmospheric"
    values apply an additional density correction. They are identical below
    roughly 100 ug/m3 and diverge above it. Report which one you logged.
  - The optical counts are NOT true bin counts: they are cumulative
    (> threshold), and the 6 channels are interpolated from a smaller number
    of physically resolved bins. Treat pc_* as semi-quantitative.
  - Allow >= 30 s of fan runtime before trusting a reading.
"""

from __future__ import annotations

import datetime
import struct
import time
from collections import OrderedDict
from typing import Optional

import serial


class PMS7003:
    BODY_LEN = 30                 # bytes following the 0x42 0x4D header
    FRAME_LENGTH_FIELD = 28       # expected value of bytes 2..3

    CMD_PASSIVE = bytes((0x42, 0x4D, 0xE1, 0x00, 0x00, 0x01, 0x70))
    CMD_ACTIVE  = bytes((0x42, 0x4D, 0xE1, 0x00, 0x01, 0x01, 0x71))
    CMD_REQUEST = bytes((0x42, 0x4D, 0xE2, 0x00, 0x00, 0x01, 0x71))
    CMD_SLEEP   = bytes((0x42, 0x4D, 0xE4, 0x00, 0x00, 0x01, 0x73))
    CMD_WAKE    = bytes((0x42, 0x4D, 0xE4, 0x00, 0x01, 0x01, 0x74))

    WARMUP_S = 30.0

    # Keys of the original MINTS schema, in order. Used to keep CSV headers
    # stable against an existing archive when extra fields are added here.
    MINTS_KEYS = (
        "dateTime",
        "pm1_0_standard", "pm2_5_standard", "pm10_0_standard",
        "pm1_0_atm", "pm2_5_atm", "pm10_0_atm",
        "pc_0_3", "pc_0_5", "pc_1_0", "pc_2_5", "pc_5_0", "pc_10_0",
    )

    def __init__(self, port, baudrate=9600, timeout=1.0,
                 passive=True, utc=False, debug=False):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.passive = passive
        self.utc = utc
        self.debug = debug
        self.ser: Optional[serial.Serial] = None
        self._fan_started: Optional[float] = None
        self.last_datetime: Optional[datetime.datetime] = None

    # accept the original keyword name used by the MINTS readers
    @classmethod
    def from_mints(cls, serial_port, **kwargs):
        return cls(serial_port, **kwargs)

    def _now(self) -> datetime.datetime:
        """Naive datetime, matching the MINTS convention of str(datetime)."""
        if self.utc:
            return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        return datetime.datetime.now()

    # ---------------------------------------------------------------- setup

    def _log(self, msg):
        if self.debug:
            print(f"[PMS7003:{self.port}] {msg}")

    def open(self, retries=10, backoff=1.0) -> bool:
        """Open the port. Returns True on success. Idempotent."""
        for attempt in range(1, retries + 1):
            try:
                if self.ser is not None:
                    self.ser.close()
                self.ser = serial.Serial(
                    self.port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout,
                    write_timeout=self.timeout,
                )
                if not self.ser.is_open:
                    self.ser.open()
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                self._fan_started = time.monotonic()
                if self.passive:
                    self.set_passive()
                self._log(f"connected (attempt {attempt})")
                return True
            except (serial.SerialException, OSError) as exc:
                self._log(f"open attempt {attempt}/{retries} failed: {exc}")
                self.ser = None
                time.sleep(backoff)
        return False

    # keep the original name working
    initiate = open

    def close(self):
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def __enter__(self):
        if not self.open():
            raise serial.SerialException(f"cannot open {self.port}")
        return self

    def __exit__(self, *exc):
        self.close()

    # -------------------------------------------------------------- commands

    def _write(self, cmd: bytes):
        if self.ser is None or not self.ser.is_open:
            raise serial.SerialException("port not open")
        self.ser.write(cmd)
        self.ser.flush()

    def set_passive(self):
        self._write(self.CMD_PASSIVE)
        self.passive = True
        time.sleep(0.1)
        self.ser.reset_input_buffer()   # drop the command ACK / in-flight frame

    def set_active(self):
        self._write(self.CMD_ACTIVE)
        self.passive = False
        time.sleep(0.1)
        self.ser.reset_input_buffer()

    def sleep(self):
        """Stop fan and laser. Extends the ~8000 h laser lifetime."""
        self._write(self.CMD_SLEEP)
        self._fan_started = None

    def wake(self):
        self._write(self.CMD_WAKE)
        self._fan_started = time.monotonic()
        time.sleep(0.1)
        self.ser.reset_input_buffer()

    @property
    def warm(self) -> bool:
        """True once the fan has run long enough for the datasheet-stable regime."""
        return (self._fan_started is not None
                and time.monotonic() - self._fan_started >= self.WARMUP_S)

    def wait_warm(self):
        if self._fan_started is None:
            return
        remaining = self.WARMUP_S - (time.monotonic() - self._fan_started)
        if remaining > 0:
            time.sleep(remaining)

    # ------------------------------------------------------------ frame read

    def _sync(self, deadline) -> bool:
        """Byte-wise search for 0x42 0x4D. Immune to odd-boundary desync."""
        prev = None
        while time.monotonic() < deadline:
            b = self.ser.read(1)
            if not b:
                continue
            cur = b[0]
            if prev == 0x42 and cur == 0x4D:
                return True
            prev = cur
        return False

    def _read_exact(self, n, deadline) -> Optional[bytes]:
        buf = bytearray()
        while len(buf) < n and time.monotonic() < deadline:
            chunk = self.ser.read(n - len(buf))
            if chunk:
                buf.extend(chunk)
        return bytes(buf) if len(buf) == n else None

    def read(self, max_wait=3.0, reconnect=True) -> Optional[OrderedDict]:
        """
        Return one validated measurement, or None.

        In passive mode a read request is issued and the reply is consumed, so
        the sample is always fresh. In active mode the input buffer is flushed
        first for the same reason.
        """
        if self.ser is None or not self.ser.is_open:
            if not (reconnect and self.open(retries=1)):
                return None

        deadline = time.monotonic() + max_wait
        try:
            if self.passive:
                self.ser.reset_input_buffer()
                self._write(self.CMD_REQUEST)
            else:
                self.ser.reset_input_buffer()

            if not self._sync(deadline):
                self._log("no header within timeout")
                return None

            body = self._read_exact(self.BODY_LEN, deadline)
            if body is None:
                self._log("truncated frame")
                return None
            # timestamp at frame arrival, not at request time
            dt = self._now()

        except (serial.SerialException, OSError) as exc:
            self._log(f"serial error: {exc}")
            self.close()
            if reconnect and self.open(retries=1):
                return None
            return None

        return self._parse(body)

    def _parse(self, body: bytes) -> Optional[OrderedDict]:
        frame_len = (body[0] << 8) | body[1]
        if frame_len != self.FRAME_LENGTH_FIELD:
            self._log(f"unexpected frame length field: {frame_len}")
            return None

        checksum = 0x42 + 0x4D + sum(body[:28])
        expected = (body[28] << 8) | body[29]
        if checksum != expected:
            self._log(f"checksum mismatch: {checksum:#06x} != {expected:#06x}")
            return None

        vals = struct.unpack(">12H", body[2:26])
        version, error_code = body[26], body[27]

        return OrderedDict((
            ("dateTime",        datetime.datetime.now(datetime.timezone.utc).isoformat()),
            ("pm1_0_standard",  float(vals[0])),
            ("pm2_5_standard",  float(vals[1])),
            ("pm10_0_standard", float(vals[2])),
            ("pm1_0_atm",       float(vals[3])),
            ("pm2_5_atm",       float(vals[4])),
            ("pm10_0_atm",      float(vals[5])),
            ("pc_0_3",          int(vals[6])),
            ("pc_0_5",          int(vals[7])),
            ("pc_1_0",          int(vals[8])),
            ("pc_2_5",          int(vals[9])),
            ("pc_5_0",          int(vals[10])),
            ("pc_10_0",         int(vals[11])),
            ("version",         int(version)),
            ("error_code",      int(error_code)),
            ("warm",            self.warm),
        ))


if __name__ == "__main__":
    import sys

    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyS5"

    with PMS7003(port, passive=True, debug=True) as pms:
        print("warming up...")
        pms.wait_warm()
        while True:
            sample = pms.read()
            if sample is None:
                print("read failed")
            else:
                print(f"{sample['dateTime']}  "
                      f"PM1.0={sample['pm1_0_atm']:6.1f}  "
                      f"PM2.5={sample['pm2_5_atm']:6.1f}  "
                      f"PM10={sample['pm10_0_atm']:6.1f} ug/m3  "
                      f"err={sample['error_code']}")
            time.sleep(1.0)