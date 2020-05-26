#!/usr/bin/env python3
# This script needs access to the Google Drive and Google Sheets API.
#
# Creating a creds file for a service account:
# https://cloud.google.com/iam/docs/creating-managing-service-account-keys
#
# We'll have the Google servers compute the last non-empty cell in the
# third column, and we'll get the value from the reference cell when needed.
# LAST_ROW_CELL formula: =ArrayFormula(max(if(len(C:C),row(C:C),)))

from calendar import timegm
from datetime import datetime

import pygsheets
import pytz


def to_epoch(dt):
    return timegm(dt.astimezone(pytz.UTC).timetuple())


class Measurement(object):
    def __init__(self, dt, value_1, value_2):
        self.dt = dt
        self.value_1 = value_1
        self.value_2 = value_2

    def as_list(self):
        return [to_epoch(self.dt), self.value_1, self.value_2]


class GWorksheet(object):
    COL_OFFSET = 2
    LAST_ROW_CELL = 'B1'

    def __init__(self, worksheet):
        self.worksheet = worksheet

    def append(self, item):
        self.worksheet.update_row(self._next_row(), item.as_list(), self.COL_OFFSET)

    def _next_row(self):
        return int(self.worksheet.cell(self.LAST_ROW_CELL).value) + 1


gsheets_client = pygsheets.authorize(service_file='./credentials.json')
spreadsheet = gsheets_client.open('TestData')
worksheet = spreadsheet.sheet1
gworksheet = GWorksheet(worksheet)

now = datetime.now(pytz.UTC)
t1 = now.replace(hour=now.hour - 2)
t2 = now.replace(hour=now.hour - 1)
measurement1 = Measurement(t1, 1.1, 2.2)
measurement2 = Measurement(t2, 1.7, 3.4)

gworksheet.append(measurement1)
gworksheet.append(measurement2)
