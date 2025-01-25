#!/usr/bin/env python3

import json
import os
import re
import textwrap
import time
from distutils.util import strtobool

import boto3
import click


ALARM_STATES = {
    'a': 'ACTIVE',
    'd': 'DISABLED',
    'n': 'NORMAL',
    'ack': 'ACKNOWLEDGED',
    'l': 'LATCHED',
    'sd': 'SNOOZE_DISABLED'
}

# The '>' and '<' characters are special chars in bash so
# we'll use the string versions of those operators
ALARM_OPERATORS = {
    'gt': 'GREATER',
    '/':  'GREATER',
    'ge': 'GREATER_OR_EQUAL',
    'lt': 'LESS',
    'le': 'LESS_OR_EQUAL',
    'eq': 'EQUAL',
    '=':  'EQUAL',
    'ne': 'NOT_EQUAL',
    '!=': 'NOT_EQUAL'
}


class NullValue:
    def __init__(self, value_type):
        self.value_type = value_type

    @staticmethod
    def from_str(s):
        if s.lower().startswith('null-'):
            value_type = s.split('-')[1].upper()
            return NullValue(value_type)
        else:
            raise ValueError('Not a null value')


def epoch_now():
    return int(time.time())


def alarm_state_value(alarm_value):
    values = re.split('(/|gt|ge|lt|le|eq|ne|>=|<=|!=|>|<|=)', alarm_value)
    if len(values) == 1:
        values.extend(['/', None, None, None])
    state_code, _, measured_value, operator, threshold_value = values

    value = { 'stateName': ALARM_STATES[state_code] }
    if measured_value and threshold_value:
        value['ruleEvaluation'] = {
            "simpleRule": {
                "inputProperty": measured_value,
                "operator": ALARM_OPERATORS[operator],
                "threshold": threshold_value
            }
        }
    return value


def cast_value(value_str):
    if re.match('^-?(\d+)?(\.\d+)?$', value_str):
        return float(value_str) if '.' in value_str else int(value_str)
    try:
        return bool(strtobool(value_str))
    except ValueError: pass
    try:
        return NullValue.from_str(value_str)
    except ValueError: pass
    try:
        return json.dumps(alarm_state_value(value_str))
    except KeyError: pass
    return value_str


def _create_property_value(value_str):
    value = cast_value(value_str)

    if isinstance(value, bool):
        return {'booleanValue': value}
    elif isinstance(value, int):
        return {'integerValue': value}
    elif isinstance(value, float):
        return {'doubleValue': value}
    elif isinstance(value, NullValue):
        return {'nullValue': {'valueType': value.value_type}}
    else:
        return {'stringValue': value}


def create_property_value(timestamp_s, value_str):
    value = _create_property_value(value_str)
    return {
        'value': value,
        'timestamp': {
            'timeInSeconds': timestamp_s,
            'offsetInNanos': 0
        },
        'quality': 'GOOD' if 'nullValue' not in value else 'UNCERTAIN'
    }


def create_entry(entry_id, asset_id, property_id, alias, property_values):
    entry = { 'entryId': str(entry_id) }
    if asset_id and property_id:
        entry['assetId'] = asset_id
        entry['propertyId'] = property_id
    if alias:
        entry['propertyAlias'] = alias
    entry['propertyValues'] = property_values
    return entry


def create_entries(asset_id, property_id, alias, value):
    property_values = [create_property_value(epoch_now(), value)]
    return [create_entry(0, asset_id, property_id, alias, property_values)]


def send_entries(iotsitewise_client, entries):
    response = iotsitewise_client.batch_put_asset_property_value(entries=entries)
    print("RequestId: ", response['ResponseMetadata']['RequestId'])
    error_messages = [error['errorMessage']
                      for entry in response.get('errorEntries', [])
                      for error in entry.get('errors', [])]
    error_messages = '\n'.join(error_messages)
    if error_messages:
        return f'Error(s): {error_messages}'


def custom_doc(f):
    alarm_states = '\n        '.join(f'{k}: {v}' for k, v in ALARM_STATES.items())
    alarm_operators = '\n        '.join(f'{k}: {v}' for k, v in ALARM_OPERATORS.items())
    doc = f"""
    Sends a measurement to an Asset Property.

    \b
    Specifying values
        <double>             Double (must include decimal point to differentiate from integers)
        <integer>            Integer (will try again as double if rejected)
        <boolean>            Boolean
        [s]                  <alarm state>
        [s]/[val][op][val]   <alarm state>/<measured value> <alarm operator> <threshold value>
        null-[type]          Null value for <type> data stream (i.e. null-[d|b|s|i])
        <string>             String (default if the value cannot be parsed)

    \b
    Valid alarm states:
        {alarm_states}

    \b
    Valid alarm operators:
        {alarm_operators}

    \b
    Examples of values:
        12.5                 Send double value
        10.0                 Send double value
        3                    Send integer value
        False                Send boolean value
        n                    Send alarm value: NORMAL
        a/12.4/10.0          Send alarm value: ACTIVE 12.4 > 10.0
        a/12.0lt30.0         Send alarm value: ACTIVE 12.0 < 30.0
        l/7le9               Send alarm value: LATCHED 7 <= 9
        'test value'         Send string value
        null-d               Send null value for a double data stream
    """
    f.__doc__ = textwrap.dedent(doc)
    return f


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-a', '--asset-id', help='Asset ID')
@click.option('-p', '--property-id', help='Property ID')
@click.option('-l', '--alias', help='Asset Property Alias')
@click.option('-v', '--value', help='Value')
@click.option('-d', '--dry-run', is_flag=True, help='Display request json')
@custom_doc
def main(asset_id, property_id, alias, value, dry_run):
    entries = create_entries(asset_id, property_id, alias, value)

    if dry_run:
        print(json.dumps({'entries': entries}, indent=2))
        return

    iotsitewise_client = boto3.client('iotsitewise')
    error_message = send_entries(iotsitewise_client, entries)
    if error_message and 'Property value does not match data type DOUBLE' in error_message:
        print('Trying again as double value')
        entries = create_entries(asset_id, property_id, alias, str(float(value)))
        error_message = send_entries(iotsitewise_client, entries)
    if error_message:
        print(error_message)


if __name__ == '__main__':
    main()
