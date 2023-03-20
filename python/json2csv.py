#!/usr/bin/env python
"""
Converts json files of the form list-of-objects into CSV files, and vice versa.

When converting JSON-to-CSV, the CSV header comes from the keys of the first
JSON object. All other JSON objects must have the same keys as the first one.

Example (JSON-to-CSV):

  > cat input.json
  [
    { "field1": 1, "field2": 2, "field3": 3 },
    { "field1": 4, "field2": 5, "field3": 6 },
    { "field1": 7, "field2": 8, "field3": 9 }
  ]

  > python json2csv.py -f input.json
  field1,field2,field3
  1,2,3
  4,5,6
  7,8,9

Example (CSV-to-JSON):

  > cat input.csv
   field1,field2,field3
   1,2,3
   4,5,6
   7,8,9

   > python json2csv.py -f input.csv -j
   [{ "field1": 1, "field2": 2, "field3": 3 },...
"""

import argparse
import contextlib
import csv
import json
import os
import sys


@contextlib.contextmanager
def file_reader(filename=None, **kwargs):
    reader = open(filename, 'r', **kwargs) if filename else sys.stdin
    yield reader
    if filename: reader.close()


def to_csv(input_filename):
    with file_reader(input_filename) as f:
        data = json.load(f)
    fields = data[0].keys()

    csv_writer = csv.DictWriter(sys.stdout, fieldnames=fields)
    csv_writer.writeheader()
    for datum in data:
        csv_writer.writerow(datum)


def to_json(input_filename):
    with file_reader(input_filename, newline='') as f:
        csv_reader = csv.DictReader(f)
        data = list(csv_reader)
    print(json.dumps(data))


def main(input_filename=None, json=None):
    file_extension = os.path.splitext(input_filename)[1] if input_filename else None
    if json or file_extension == '.csv':
        to_json(input_filename)
    else:
        to_csv(input_filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-f', '--file', help='Input file (read from stdin if not provided)')
    parser.add_argument('-r', '-j', '--json', help='Reverse operation (Convert to JSON)', action='store_true')
    args = parser.parse_args()

    try:
        main(args.file, args.json)
    except json.decoder.JSONDecodeError as e:
        sys.exit(f'Error reading JSON: {e}')
