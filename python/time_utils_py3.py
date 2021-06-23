#!/usr/bin/env python3

import pytz
import time

from calendar import timegm
from datetime import datetime, timezone


tz_pdt = pytz.timezone("America/Los_Angeles")


def now_utc():
    return datetime.now(timezone.utc)

def to_epoch(dt):
    return timegm(dt.astimezone(timezone.utc).timetuple())

def to_epoch2():
    return int(time.time())

def now_epoch():
    return timegm(datetime.now(timezone.utc).timetuple())

def to_datetime(epoch=None, str_dt=None, tz=None):
    if str_dt:
        dt = datetime.strptime(str_dt, '%Y-%m-%d %H:%M:%S')
        if tz:
            tz.localize(dt)
        return dt.astimezone(timezone.utc)
    elif epoch:
        return datetime.fromtimestamp(epoch, tz=tz)


now = now_utc()
print("now (local):", now.astimezone(tz_pdt))
print("now (utc):", now.astimezone(timezone.utc))
print("now (epoch):", to_epoch(now))
print("now (epoch2):", to_epoch2())
print()


print('Buiding datetime from constructor')
print('Starting date: 2012-04-01 00:00 PDT')
local_dt = tz_pdt.localize(datetime(2012, 4, 1, 0, 0))
# prints 1333238400
epoch = to_epoch(local_dt)
print('Epoch:', epoch)
print('Convert to local:', to_datetime(epoch=epoch).astimezone(tz_pdt))
print('Convert to UTC:', to_datetime(epoch=epoch).astimezone(timezone.utc))
print()

print('Buiding datetime from UTC string')
utc_dt = to_datetime(str_dt='2018-06-07 05:10:05')
print('UTC dt:', utc_dt)
epoch = to_epoch(utc_dt)
print('Epoch:', epoch)
print('Convert to local:', to_datetime(epoch=epoch).astimezone(tz_pdt))
print('Convert to UTC:', to_datetime(epoch=epoch).astimezone(timezone.utc))
print()


print('Buiding datetime from PDT string')
local_dt = to_datetime(str_dt='2018-06-07 13:00:00', tz=tz_pdt)
print('Local dt:', local_dt)
epoch = to_epoch(local_dt)
print('Epoch:', epoch)
print('Convert to local:', to_datetime(epoch=epoch).astimezone(tz_pdt))
print('Convert to UTC:', to_datetime(epoch=epoch).astimezone(timezone.utc))
