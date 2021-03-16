#!/usr/bin/env python

import argparse
import contextlib
import sys


@contextlib.contextmanager
def open_file(filename=None, mode='r'):
    """
    Return a file handler or stdin/stdout for reading (stdin) or writing (stdout).
    """

    if filename:
        handler = open(filename, mode)
    else:
        handler = sys.stdout if mode == 'w' else sys.stdin

    try:
        yield handler
    finally:
        if filename:
            handler.close()


def process_file(input_filename, output_filename):
    content = []

    with open_file(input_filename) as f:
        for line in f:
            content.append(line.rstrip())

    with open_file(output_filename, 'w') as f:
        for line in content:
            f.write(line + '\n')


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-f', '--file', action='store', default=None,
                        help='The file to read from (default to stdin if not specified)')

    parser.add_argument('-o', '--output', action='store', default=None,
                        help='The file to output to (default to stdout if not specified)')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    process_file(args.file, args.output)
