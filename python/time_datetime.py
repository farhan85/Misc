#!/usr/bin/env python3

import iso8601
from zoneinfo import ZoneInfo # Python 3.9+
from datetime import datetime, timezone


TZ_PST = ZoneInfo('America/Los_Angeles')
TZ_EST = ZoneInfo('America/New_York')


def from_iso_str(s):
    # Note this fuction can only convert UTC ISO strings
    # The iso8601 package can handle the 'Z' format, but datetime only understands '+00:00' format
    return datetime.fromisoformat(s.replace('Z','')).astimezone(timezone.utc)


now_utc = datetime.now(timezone.utc)
now_pst = now_utc.astimezone(TZ_PST)
print("Now (UTC):", now_utc)
print("Convert to PDT:", now_pst)
print("Convert to EST:", now_utc.astimezone(TZ_EST))
print("UTC to epoch:", int(now_utc.timestamp()))
print("PST to epoch:", int(now_pst.timestamp()))
print("PST to string (ISO):", now_pst.isoformat())
print("PST to string with TZ code (custom):", now_pst.strftime('%d/%m/%y %H:%M:%S %Z'))
print("PST to string with numeric TZ (custom):", now_pst.strftime('%d/%m/%y %H:%M:%S %z'))
print()

print('Buiding datetime from datetime constructor')
est_dt = datetime(2012, 6, 20, 11, 10, 5, tzinfo=TZ_EST)
print('Starting date:', str(est_dt))
print('Convert to PST:', est_dt.astimezone(TZ_PST))
print('Convert to UTC:', est_dt.astimezone(timezone.utc))
print()

print('Buiding datetime from epoch')
epoch = 1732391153
print('Epoch:', epoch)
print('Epoch to local datetime:', datetime.fromtimestamp(epoch))
print('Epoch to UTC datetime:', datetime.fromtimestamp(epoch, tz=timezone.utc))
print('Epoch to PST datetime:', datetime.fromtimestamp(epoch, tz=TZ_PST))
print()

print('Buiding datetime from string')
tz_naive_dt = datetime.strptime('30/12/22 22:35:45', '%d/%m/%y %H:%M:%S')
print('TZ naive datetime:', tz_naive_dt)
print('Set TZ to UTC:', tz_naive_dt.replace(tzinfo=timezone.utc))
print('Set TZ to PST:', tz_naive_dt.replace(tzinfo=TZ_PST))
print()

print('Buiding datetime from ISO string')
print("Using 'Z':", from_iso_str('2022-12-30T22:35:45.123456Z'))
print("Using '+00:00':", from_iso_str('2022-12-30T22:35:45.123456+00:00'))
print()

print('Using iso8601 package to convert from string')
print('PST:', iso8601.parse_date('2023-02-08 13:05:00-07:00'))
print("UTC using 'Z':", iso8601.parse_date('2023-02-08 13:05:00Z'))
print("UTC using '+00:00':", iso8601.parse_date('2023-02-08 13:05:00+00:00'))

