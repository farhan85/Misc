#!/usr/bin/env python3

import json
import os
import time
from collections import namedtuple
from tabulate import tabulate

import boto3
import click


Property = namedtuple('Property', 'asset_id id name')
PropertyValue = namedtuple('PropertyValue', 'asset_id id name value timestamp quality')


def asset_properties(iotsitewise, asset_id):
    params = { 'assetId': asset_id, 'filter': 'ALL' }
    while True:
        response = iotsitewise.list_asset_properties(**params)
        for asset_property in response['assetPropertySummaries']:
            yield Property(asset_id, asset_property['id'], asset_property['path'][-1]['name'])
        if 'nextToken' not in response:
            break
        params['nextToken'] = response['nextToken']
        time.sleep(0.1)


def create_entries(properties):
    return [{'entryId': str(idx), 'assetId': str(prop.asset_id), 'propertyId': str(prop.id)}
            for (idx, prop) in enumerate(properties)]


def asset_property_values(iotsitewise, request_entries):
    params = { 'entries': request_entries }
    while True:
        response = iotsitewise.batch_get_asset_property_value(**params)
        if response['errorEntries']:
            error_messages = [entry['errorMessage'] for entry in response['errorEntries']]
            raise RuntimeError('\n'.join(error_messages))
        for entry in response['successEntries']:
            yield entry
        if 'nextToken' not in response:
            break
        params['nextToken'] = response['nextToken']
        time.sleep(0.1)


def to_property_values(properties, request_entries, response_entries):
    prop_names = dict((p.id, p.name) for p in properties)
    entries = dict((e['entryId'], e) for e in request_entries)
    default_property_value = {
        'value': { 'stringValue': '-' },
        'timestamp': { 'timeInSeconds': '-' },
        'quality': '-',
    }
    property_values = []
    for entry in response_entries:
        entry_id = entry['entryId']
        asset_id = entries[entry_id]['assetId']
        prop_id = entries[entry_id]['propertyId']
        prop_name = prop_names[prop_id]
        response_value = entry.get('assetPropertyValue', default_property_value)
        prop_val = list(response_value['value'].values())[0]
        prop_ts = response_value['timestamp']['timeInSeconds']
        prop_qual = response_value['quality']
        property_values.append(PropertyValue(asset_id, prop_id, prop_name, prop_val, prop_ts, prop_qual))
    return property_values


def value_as_string(property):
    value = property.value
    if isinstance(value, str):
        if property.name == 'AWS/ALARM_STATE' and value != '-':
            return json.loads(value)['stateName']
        elif len(value) > 18:
            return '{}...'.format(value[0:15])
    elif isinstance(value, float):
        return '{:.5f}'.format(value)
    return str(value)


def print_property_values(property_values):
    headers = ['AssetId', 'PropertyId', 'Name', 'Value', 'Timestamp', 'Quality']
    row_data = [(p.asset_id, p.id, p.name, value_as_string(p), p.timestamp, p.quality)
                for p in property_values]
    print(tabulate(row_data, headers=headers, tablefmt="presto"))


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.argument('asset-id')
def main(asset_id):
    iotsitewise = boto3.client('iotsitewise')
    properties = sorted(asset_properties(iotsitewise, asset_id), key=lambda p: p.name)
    request_entries = create_entries(properties)
    response_entries = asset_property_values(iotsitewise, request_entries)
    values = to_property_values(properties, request_entries, response_entries)
    print_property_values(values)


if __name__ == '__main__':
    main()
