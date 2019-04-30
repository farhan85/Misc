#!/usr/bin/env python

import calendar
import pytz

from calendar import timegm
from datetime import datetime


#for tz in pytz.all_timezones:
#    print tz
tz_pdt = pytz.timezone("America/Los_Angeles")


def now_utc():
    return datetime.now(pytz.UTC)

def to_epoch(dt):
    # Returns a unix epoch (seconds since Epoch)
    return timegm(dt.astimezone(pytz.UTC).timetuple())

def to_datetime(epoch=None, str_dt=None):
    if str_dt:
        return pytz.UTC.localize(datetime.strptime(str_dt, '%Y-%m-%d %H:%M:%S'))
    elif epoch:
        return pytz.UTC.localize(datetime.utcfromtimestamp(epoch))


class UtcTime(object):
    """Stores a datetime object with its timezone set to UTC"""

    def __init__(self, *args, **kwargs):
        if 'utcdt' in kwargs:
            self.dt = kwargs['utcdt']
        else:
            self.dt = pytz.UTC.localize(datetime(*args))

    def epoch(self):
        return timegm(self.dt.utctimetuple())

    def epoch_ms(self):
        return self.epoch() * 1000 + self.dt.microsecond/1000

    def epoch_us(self):
        return (self.epoch() * 1000000) + self.dt.microsecond

    def __str__(self):
        return str(self.dt)

    def __repr__(self):
        return '{}({}, {}, {}, {}, {}, {}, {})'.format(
            self.__class__.__name__,
            self.dt.year,
            self.dt.month,
            self.dt.day,
            self.dt.hour,
            self.dt.minute,
            self.dt.second,
            self.dt.microsecond
            )

    @staticmethod
    def now():
        return UtcTime(utcdt=datetime.now(pytz.UTC))


now = now_utc()
print "now:", now
print "now (local):", now.astimezone(tz_pdt)
print "now (epoch):", to_epoch(now)
print


local_dt = tz_pdt.localize(datetime(2012, 4, 1, 0, 0))
# prints 1333238400
epoch = to_epoch(local_dt)
print epoch
print to_datetime(epoch=epoch).astimezone(tz_pdt)
print

print to_datetime(str_dt='2018-06-07 05:10:05')

utc_now = UtcTime.now()
print utc_now
print repr(utc_now)
print utc_now.epoch()
print utc_now.epoch_ms()
print utc_now.epoch_us()
