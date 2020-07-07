#!/usr/bin/env python3

import argparse
import dryable
import logging
import sys
import time


@dryable.Dryable('default value')
def slow_triple(x):
    time.sleep(3)
    return x*3

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dry-run', action='store_true', help='Run in dry run mode')
    parser.add_argument('value', type=int, help='A number to compute')
    args = parser.parse_args()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    dryable.set(args.dry_run)

    print('triple value:', slow_triple(args.value))

if __name__ == '__main__':
    main()
