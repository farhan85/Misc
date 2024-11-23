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


def create_entry(entry_id, asset_id, property_id, alias, quality, start_dt, end_dt):
    entry = { 'entryId': str(entry_id) }
    if asset_id and property_id:
        entry['assetId'] = asset_id
        entry['propertyId'] = property_id
    if alias:
        entry['propertyAlias'] = alias
    if start_dt and end_dt:
        entry['startDate'] = to_epoch(start_dt)
        entry['endDate'] = to_epoch(end_dt)
        entry['qualities'] = [quality.upper()]
        entry['timeOrdering'] = 'ASCENDING'
    return entry


def extract_property_data(property_value):
    dt = datetime.fromtimestamp(property_value['timestamp']['timeInSeconds'], tz=TZ_PST)
    dt_nanos = property_value['timestamp']['offsetInNanos']
    value = list(property_value['value'].values())[0]
    quality = property_value['quality']
    return (f'{dt} {dt_nanos}ns', value, quality)


def print_success_entries(entries):
    if len(entries) > 1:
        raise RuntimeError('Expected only one entry', entries)

    entry = entries[0]
    if 'assetPropertyValueHistory' in entry:
        headers = ['Timestamp', 'Value', 'quality']
        row_data = [extract_property_data(v) for v in entry['assetPropertyValueHistory']]
        print(tabulate(row_data, headers=headers, tablefmt="presto"))
    else:
        dt, value, quality = extract_property_data(entry['assetPropertyValue'])
        print('Timestamp:', dt)
        print('Value:    ', value)
        print('Quality:  ', quality)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-a', '--asset-id', help='Asset ID')
@click.option('-p', '--property-id', help='Property ID')
@click.option('-l', '--alias', help='Asset Property Alias')
@click.option('-m', '--minutes', type=int, help='History duration in minutes (gets latest if not specified)')
@click.option('-q', '--quality', default='GOOD', help='Quality type (GOOD, BAD)')
@click.option('-d', '--dry-run', is_flag=True, help='Display request json')
def main(asset_id, property_id, alias, minutes, quality, dry_run):
    iotsitewise_client = boto3.client('iotsitewise')

    if minutes:
        end_dt = now_utc()
        start_dt = end_dt - timedelta(minutes=minutes)
    else:
        end_dt = None
        start_dt = None

    entries = [create_entry(0, asset_id, property_id, alias, quality, start_dt, end_dt)]
    if dry_run:
        print(json.dumps({'entries': entries}, indent=2))
        return

    if minutes:
        response = iotsitewise_client.batch_get_asset_property_value_history(entries=entries)
    else:
        response = iotsitewise_client.batch_get_asset_property_value(entries=entries)
    print("RequestId:", response['ResponseMetadata']['RequestId'])

    error_messages = [entry['errorMessage'] for entry in response.get('errorEntries', [])]
    if error_messages:
        print('Errors:', '\n'.join(error_messages))
        return

    print_success_entries(response['successEntries'])


if __name__ == '__main__':
    main()
