#!/usr/bin/env python3

import json
import os
import re
from datetime import datetime, timedelta, timezone

import boto3
import click


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

    print("RequestId: ", response['ResponseMetadata']['RequestId'])
    error_messages = [entry['errorMessage'] for entry in response.get('errorEntries', [])]
    if error_messages:
        print('Errors:', '\n'.join(error_messages))
    else:
        print(json.dumps(response['successEntries']))


if __name__ == '__main__':
    main()
