import os
import random
from datetime import datetime

import boto3


def get_asset_property_ids(s3, bucket, key):
    # Expected file format: row contents: <asset ID>,<property ID>
    content = s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8')
    lines = content.strip().split('\n')
    return [line.split(',') for line in lines if line]


def batch_get_asset_property_values(sitewise, entries):
    params = {'entries': entries}
    while True:
        response = sitewise.batch_get_asset_property_value(**params)
        yield response
        if 'nextToken' not in response:
            break
        params['nextToken'] = response['nextToken']


def get_latest_values(sitewise, asset_properties):
    entries = [{'entryId': str(i), 'assetId': asset_id, 'propertyId': property_id}
               for i, (asset_id, property_id) in enumerate(asset_properties)]
    results = []
    for response in batch_get_asset_property_values(sitewise, entries):
        for skipped in response['skippedEntries']:
            print(f'WARN - Skipped entry - {skipped}')
        for error in response['errorEntries']:
            print(f'WARN - Error entry - {error}')
        for success in response['successEntries']:
            if 'assetPropertyValue' in success:
                entry_id = int(success['entryId'])
                asset_id, property_id = asset_properties[entry_id]
                value = float(success['assetPropertyValue']['value']['doubleValue'])
                results.append((asset_id, property_id, value))
    return results


def generate_new_values(asset_property_values):
    # Generate values using random walk
    return [(asset_id, property_id, value + random.gauss(0, 1.0))
            for asset_id, property_id, value in asset_property_values]


def chunk_list(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def send_values(sitewise, asset_property_values, dt_now):
    timestamp = int(dt_now.timestamp())
    entries = [
        {
            'entryId': str(i),
            'assetId': asset_id,
            'propertyId': property_id,
            'propertyValues': [{
                'value': { 'doubleValue': value },
                'timestamp': { 'timeInSeconds': timestamp }
            }]
        }
        for i, (asset_id, property_id, value) in enumerate(asset_property_values)
    ]

    for batch in chunk_list(entries, 10):
        print('Sending batch to Sitewise:')
        for entry in batch:
            print(entry)
        response = sitewise.batch_put_asset_property_value(entries=batch)
        print('Response:', response)


def handler(event, context):
    s3_bucket = os.environ['DATA_S3_BUCKET']
    s3_key = os.environ['ASSET_PROPERTY_ID_S3_KEY']
    dt_now = datetime.fromisoformat(event['time']).replace(second=0, microsecond=0)

    s3 = boto3.client('s3')
    sitewise = boto3.client('iotsitewise')

    asset_properties = get_asset_property_ids(s3, s3_bucket, s3_key)
    print(f'Found {len(asset_properties)} asset/property IDs')

    if asset_properties:
        values = get_latest_values(sitewise, asset_properties)
        print(f'Received {len(values)} latest values')

        values = generate_new_values(values)
        send_values(sitewise, values, dt_now)
