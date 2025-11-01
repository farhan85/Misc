#!/usr/bin/env python3

import json
import os
import pytz
import re
from tabulate import tabulate
from datetime import datetime, timedelta, timezone

import boto3
import click


TZ_PST = pytz.timezone("America/Los_Angeles")


def now_utc():
    return datetime.now(timezone.utc)


def to_epoch(dt):
    return int(dt.timestamp())


def batch_get_asset_property_value_history(iotsitewise_client, entries):
    values, errors = [], []
    params = {'entries': entries, 'maxResults': 500}
    print('Retrieving values...', end='', flush=True)
    while True:
        response = iotsitewise_client.batch_get_asset_property_value_history(**params)
        errors.extend(response['errorEntries'])
        values.extend(value
                      for entry in response['successEntries']
                      for value in entry['assetPropertyValueHistory'])
        if 'nextToken' in response:
            params['nextToken'] = response['nextToken']
            print('.', end='', flush=True)
            time.sleep(0.5)
        else:
            print('done')
            return values, errors


def batch_get_asset_property_value(iotsitewise_client, entries):
    response = iotsitewise_client.batch_get_asset_property_value(entries=entries)
    entry = response['successEntries'][0] if response['successEntries'] else {}
    value = entry.get('assetPropertyValue', None)
    errors = response['errorEntries']
    return value, errors


def create_entry(entry_id, asset_id, property_id, alias, start_dt=None, end_dt=None, quality=None):
    entry = { 'entryId': str(entry_id) }
    if asset_id and property_id:
        entry['assetId'] = asset_id
        entry['propertyId'] = property_id
    if alias:
        entry['propertyAlias'] = alias
    if start_dt and end_dt and quality:
        entry['startDate'] = to_epoch(start_dt)
        entry['endDate'] = to_epoch(end_dt)
        entry['qualities'] = [quality.upper()]
        entry['timeOrdering'] = 'ASCENDING'
    return entry


def extract_property_data(property_value):
    dt = datetime.fromtimestamp(property_value['timestamp']['timeInSeconds'], tz=TZ_PST)
    dt_nanos = property_value['timestamp']['offsetInNanos']
    value_type = list(property_value['value'].keys())[0]
    value = 'null' if value_type == 'nullValue' else property_value['value'][value_type]
    quality = property_value['quality']
    return (f'{dt} {dt_nanos}ns', value, quality)


def print_property_values(values):
    if isinstance(values, list):
        headers = ['Timestamp', 'Value', 'Quality']
        row_data = [extract_property_data(v) for v in values]
        row_data = sorted(row_data, key=lambda x:x[0])
        print(tabulate(row_data, headers=headers, tablefmt="presto"))
    else:
        dt, value, quality = extract_property_data(values) if values else ('-', '-', '-')
        print('Timestamp:', dt)
        print('Value:    ', value)
        print('Quality:  ', quality)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-a', '--asset-id', help='Asset ID')
@click.option('-p', '--property-id', help='Property ID')
@click.option('-l', '--alias', help='Asset Property (or Data Stream) Alias')
@click.option('-m', '--minutes', type=int, help='History duration in minutes (gets latest if not specified)')
def main(asset_id, property_id, alias, minutes):
    iotsitewise_client = boto3.client('iotsitewise')

    if minutes:
        end_dt = now_utc()
        start_dt = end_dt - timedelta(minutes=minutes)
        entries = [create_entry(idx, asset_id, property_id, alias, start_dt, end_dt, quality)
                   for idx, quality in enumerate(['GOOD', 'BAD', 'UNCERTAIN'])]
        values, errors = batch_get_asset_property_value_history(iotsitewise_client, entries)
    else:
        end_dt = None
        start_dt = None
        entries = [create_entry(0, asset_id, property_id, alias)]
        values, errors = batch_get_asset_property_value(iotsitewise_client, entries)

    if errors:
        print('Errors: {}\n'.format('\n'.join(error_entries)))
    print_property_values(values)


if __name__ == '__main__':
    main()
