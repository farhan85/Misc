#!/usr/bin/env python

import argparse
from datetime import datetime, timezone, timedelta


USAGE = """
Examples:
  Convert seconds to datetime
  > %(prog)s -s 1784576493

  Convert milliseconds to datetime
  > %(prog)s -m 1753475290299981

  Convert microseconds to datetime
  > %(prog)s -u 1753475290299981

  Convert nanoseconds to (microseconds) datetime
  > %(prog)s -n 1718012345678901234
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Converts the given epoch to a human-readable timestamp',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=USAGE,
    )

    parser.add_argument('-s', '--s', type=int, help='Seconds since epoch')
    parser.add_argument('-m', '--ms', type=int, help='Milliseconds since epoch')
    parser.add_argument('-u', '--us', type=int, help='Microseconds since epoch')
    parser.add_argument('-n', '--ns', type=int, help='Nanoseconds since epoch')
    args = parser.parse_args()

    ns = 0
    if args.s:
        delta = timedelta(seconds=args.s)
    elif args.ms:
        delta = timedelta(milliseconds=args.ms)
    elif args.us:
        delta = timedelta(microseconds=args.us)
    elif args.ns:
        ts_ns = args.ns
        s = ts_ns // 1_000_000_000
        us = (ts_ns % 1_000_000_000) // 1000
        ns = ts_ns % 1000
        delta = timedelta(seconds=s, microseconds=us)

    epoch = datetime.fromtimestamp(0, tz=timezone.utc)
    dt = epoch + delta
    print(f'{dt} {ns}ns')
