#!/usr/bin/env python
"""
A Lambda Function that can be invoked by AWS EventBridge to periodically send
dummy values to AWS IoT SiteWise.
"""

import os
import random
from math import cos, sin, pi

import boto3
import iso8601
from awsretry import AWSRetry
from botocore.exceptions import ClientError


def to_epoch(dt):
    return int(dt.timestamp())


def gen_prop_values(t):
    return (
        ('/test/alias-1', sin((4*pi/60)*t) + 2.0*sin((8*pi/60)*t) ),
        ('/test/alias-2', cos((4*pi/60)*t) + 2.2*cos((8*pi/60)*t) ),
        ('/test/alias-3', sin((8*pi/60)*t) + 2.0*sin((9*pi/60)*t) ),
        ('/test/alias-4', cos((3*pi/60)*t) + 2.0*cos((5*pi/60)*t) ),
        ('/test/alias-5', random.expovariate(1.0)),
        ('/test/alias-6', random.expovariate(3.0)),
    )


def create_entry(entry_id, timestamp_sec, property_alias, property_value):
    return {
        'entryId': str(entry_id),
        'propertyAlias': property_alias,
        'propertyValues': [{
            'value': {
                'doubleValue': property_value
            },
            'timestamp': {
                'timeInSeconds': timestamp_sec,
                'offsetInNanos': 0
            },
            'quality': 'GOOD'
        }]
    }


@AWSRetry.backoff()
def send_values(sitewise_client, entries):
    try:
        response = sitewise_client.batch_put_asset_property_value(entries=entries)
        print('Sent values to SiteWise. Response:', response)
    except ClientError as e:
        print('Failed to send values to SiteWise. Response:', e.response)
        raise e


def handler(event, context):
    region = os.environ["AWS_REGION"]
    timestamp = iso8601.parse_date(event['time']).replace(second=0)

    print(f'Region: {region}')
    print(f'Timestamp: {timestamp}')

    ts_epoch = to_epoch(timestamp)
    values = gen_prop_values(ts_epoch)
    entries = [create_entry(idx, ts_epoch, prop_alias, prop_value)
               for idx, (prop_alias, prop_value) in enumerate(values)]

    print(f'Entries:{entries}')
    print('Sending values to SiteWise')
    sitewise_client = boto3.client('iotsitewise', region_name=region)
    send_values(sitewise_client, entries)
