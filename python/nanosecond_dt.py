from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from functools import total_ordering
from zoneinfo import ZoneInfo


@total_ordering
class NanoDatetime:
    """Represents a datetime with nanosecond precision."""

    def __init__(self, dt: datetime, ns_offset: int = 0) -> NanoDatetime:
        if 0 <= ns_offset < 1000:
            self.dt = dt
            self.ns_offset = ns_offset
        else:
            us_delta, remainder = divmod(ns_offset, 1000)
            self.dt = dt + timedelta(microseconds=us_delta)
            self.ns_offset = remainder

    @classmethod
    def from_string(cls, dt_str: str) -> NanoDatetime:
        """Parses an ISO format string with up to nanosecond precision.

        Example: '2026-07-20 16:12:00.123456789+05:30'
        """

        if "." in dt_str:
            # Split timestamp from fractional part
            base_str, remaining = dt_str.split(".")
            # Split fractional part again into fractional-seconds + timezone
            match = re.match(r"(\d+)(.*)", remaining)
            fraction = match.group(1)
            tz_suffix = match.group(2)

            nano_str = fraction.ljust(9, "0")[:9]
            nanos = int(nano_str)
            micros, nano_offset = divmod(nanos, 1000)
            micros_str = str(micros).zfill(6)
            native_str = f"{base_str}.{micros_str}{tz_suffix}"
        else:
            native_str = dt_str
            nano_offset = 0

        if 'Z' in native_str:
            # Python versions before 3.11 do not support 'Z'
            native_str = native_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(native_str)
        return cls(dt, nano_offset)

    def to_json(self) -> str:
        epoch_s = int(self.dt.timestamp())
        timestamp_us = epoch_s * 1_000_000 + self.dt.microsecond
        return json.dumps({
            'timestamp': timestamp_us,
            'nanos_offset': self.ns_offset,
        })

    @classmethod
    def from_json(cls, json_s: str) -> NanoDatetime:
        d = json.loads(json_s)
        dt = datetime.fromtimestamp(d['timestamp'] / 1_000_000, tz=timezone.utc)
        return cls(dt, d['nanos_offset'])

    def to_epoch_ns(self) -> int:
        epoch_s = int(self.dt.timestamp())
        timestamp_us = epoch_s * 1_000_000 + self.dt.microsecond
        return timestamp_us * 1_000 + self.ns_offset

    @classmethod
    def from_epoch_ns(cls, epoch: int) -> NanoDatetime:
        ns_offset = epoch % 1_000
        us_epoch = epoch // 1_000
        dt = datetime.fromtimestamp(us_epoch / 1_000_000, tz=timezone.utc)
        return cls(dt, ns_offset)

    def add(self,
            days: int = 0,
            hours: int = 0,
            minutes: int = 0,
            seconds: int = 0,
            milliseconds: int = 0,
            microseconds: int = 0,
            nanoseconds: int = 0,
        ) -> NanoDatetime:

        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds,
                          milliseconds=milliseconds, microseconds=microseconds)
        new_dt = self.dt + delta
        new_ns = self.ns_offset + nanoseconds
        return NanoDatetime(new_dt, new_ns)

    def _tuple(self) -> tuple[datetime, int]:
        """Helper to return comparable tuples."""
        return (self.dt, self.ns_offset)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NanoDatetime):
            return NotImplemented
        return self._tuple() == other._tuple()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, NanoDatetime):
            return NotImplemented
        return self._tuple() < other._tuple()

    def _timestamp_str(self):
        base = self.dt.strftime("%Y-%m-%d %H:%M:%S")
        subseconds = str(self.dt.microsecond).zfill(6) + str(self.ns_offset).zfill(3)
        tz = self.dt.strftime("%z") if self.dt.tzinfo else ""
        return f"{base}.{subseconds}{tz}"

    def __str__(self) -> str:
        return self._timestamp_str()

    def __repr__(self) -> str:
        return "{}({}, {})".format(self.__class__.__name__, repr(self.dt), self.ns_offset)


if __name__ == '__main__':
    ts1 = NanoDatetime.from_string('2026-07-20 16:12:33.123456111')
    ts2 = NanoDatetime.from_string('2026-07-20 16:12:33.123456789')
    ts3 = NanoDatetime.from_string('2026-07-20 16:12:33.123456999')
    print(ts2)
    print('In range?', ts1 <= ts2 <= ts3)

    ts4 = NanoDatetime.from_string('2026-07-20 18:30:13.123456789+05:30')
    print(ts4)

    ts5 = NanoDatetime.from_string('2026-07-20 06:45:59.123456789Z')
    print(ts5)

    print(repr(ts5))
    print(ts5.add(days=3, nanoseconds=999))

    print(ts4.to_json())
    print(NanoDatetime.from_json('{"timestamp": 1784563920123456, "nanos_offset": 789}'))

    epoch_ns = ts1.to_epoch_ns()
    print(epoch_ns)
    print(NanoDatetime.from_epoch_ns(epoch_ns))
