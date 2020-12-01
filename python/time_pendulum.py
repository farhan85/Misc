#!/usr/bin/env python3

import pendulum
from tabulate import tabulate


cmds = [
    "pendulum.local(2020, 11, 3).timezone.name",
    "pendulum.datetime(2012, 1, 1, 13, 23, 45, tz='America/Los_Angeles')",
    "pendulum.now()",
    "pendulum.now(tz='UTC')",
    "pendulum.now(tz='UTC').int_timestamp",
    "pendulum.now(tz='America/Los_Angeles')",
    "pendulum.now(tz='America/Los_Angeles').int_timestamp",
    "pendulum.now(tz='America/Los_Angeles').in_tz('UTC')",
    "pendulum.from_format('1975-05-21 22:10:40', 'YYYY-MM-DD HH:mm:ss')",
    "pendulum.from_format('1975-05-21 22', 'YYYY-MM-DD HH', tz='America/New_York')",
    "pendulum.from_timestamp(1605765508)",
    "pendulum.from_timestamp(-1, tz='Australia/Sydney')",
    "pendulum.parse('1975-05-21T22:00:00')",
    "pendulum.parse('1975-05-21T22:00:00', tz='Australia/Perth')",
]

print(tabulate((cmd, eval(cmd)) for cmd in cmds))
