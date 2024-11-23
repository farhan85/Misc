#!/usr/bin/env python3

import iso8601
import pytz
from datetime import datetime, timezone


tz_pst = pytz.timezone('America/Los_Angeles')
tz_est = pytz.timezone('America/New_York')


def now_utc():
    return datetime.now(timezone.utc)


def to_epoch(dt):
    # If it's already in UTC: int(dt.timestamp())
    return int(dt.astimezone(timezone.utc).timestamp())


def from_iso_str(s):
    # The iso8601 package can handle the 'Z' format, but datetime only understands '+00:00' format
    return datetime.fromisoformat(s.replace('Z','')).astimezone(timezone.utc)


now = now_utc()
print("now (local):", now.astimezone(tz_pst))
print("now (utc):", now)
print("now (epoch):", to_epoch(now))
print("now (ISO):", now.isoformat())
print("now (custom):", now.strftime('%d/%m/%y %H:%M:%S'))
print()


print('Buiding datetime from datetime constructor')
est_dt = tz_est.localize(datetime(2012, 6, 20, 11, 10, 5))
print('Starting date:', str(est_dt))
print('Epoch:', to_epoch(est_dt))
print('Convert to local:', est_dt.astimezone(tz_pst))
print('Convert to UTC:', est_dt.astimezone(timezone.utc))
print()

print('Buiding datetime from epoch')
epoch = to_epoch(now)
print('Epoch to local datetime:', datetime.fromtimestamp(epoch))
print('Epoch to UTC datetime:', datetime.fromtimestamp(epoch, tz=timezone.utc))
print('Epoch to PST datetime:', datetime.fromtimestamp(epoch, tz=tz_pst))
print()

print('Buiding datetime from string')
utc_dt = datetime.strptime('30/12/22 22:35:45', '%d/%m/%y %H:%M:%S').replace(tzinfo=timezone.utc)
print('Starting date:', utc_dt)
print('Epoch:', to_epoch(utc_dt))
print('Convert to local:', utc_dt.astimezone(tz_pst))
print('Convert to EST:', utc_dt.astimezone(tz_est))
print()

print('Buiding datetime from ISO string')
utc_dt = from_iso_str('2022-12-30T22:35:45.123456Z')
print('Starting date:', utc_dt)
print('Epoch:', to_epoch(utc_dt))
print('Convert to local:', utc_dt.astimezone(tz_pst))
print('Convert to EST:', utc_dt.astimezone(tz_est))
print()


print('Using iso8601 package to convert from string')
print(iso8601.parse_date('2023-02-08 13:05:00-07:00'))
print(iso8601.parse_date('2023-02-08 13:05:00+00:00'))
print(iso8601.parse_date('2023-02-08 13:05:00Z'))
