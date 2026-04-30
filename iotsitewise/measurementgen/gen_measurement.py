import os
import random
from datetime import datetime

import boto3
import awswrangler as wr
import numpy as np
import pandas as pd
from botocore.exceptions import ClientError


VALUES_S3_KEY = 'property_values.csv'


def load_asset_properties(asset_properties_path):
    asset_properties = wr.s3.read_csv(asset_properties_path)
    print(f'Found {len(asset_properties)} asset/property IDs')
    return asset_properties


def load_property_values(asset_properties, property_values_path):
    if not wr.s3.does_object_exist(property_values_path):
        print('No property values file found')
        return None

    print('Found property values file')
    df = wr.s3.read_csv(property_values_path)
    ap_keys = set(zip(asset_properties['assetId'], asset_properties['propertyId']))
    df_keys = set(zip(df['assetId'], df['propertyId']))
    if ap_keys != df_keys:
        print('Asset/property IDs mismatch in property values file')
        return None

    return df


def generate_values(asset_properties, property_values, property_values_path):
    rng = np.random.default_rng()
    if property_values is None:
        print('Generating init values')
        df = asset_properties.copy()
        df['value'] = rng.uniform(low=1, high=100, size=len(df))
    else:
        print('Applying random walk')
        df = property_values
        df['value'] += rng.normal(0, 1, size=len(df))

    wr.s3.to_csv(df, property_values_path, index=False)
    print(f"Uploaded values file to {property_values_path}")
    return df


def chunk_list(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def send_values(sitewise, df, dt_now):
    timestamp = int(dt_now.timestamp())
    entries = [
        {
            'entryId': str(i),
            'assetId': row['assetId'],
            'propertyId': row['propertyId'],
            'propertyValues': [{
                'value': { 'doubleValue': row['value'] },
                'timestamp': { 'timeInSeconds': timestamp }
            }]
        }
        for i, row in df.iterrows()
    ]

    for batch in chunk_list(entries, 10):
        print(f'Sending batch with {len(batch)} entries to Sitewise')
        response = sitewise.batch_put_asset_property_value(entries=batch)
        print('Response:', response)

        error_messages = '\n'.join([
            '{} {}'.format(error['errorCode'], error['errorMessage'])
            for entry in response.get('errorEntries', [])
            for error in entry.get('errors', [])
        ])
        if error_messages:
            raise RuntimeError(f'Failed sending data to SiteWise: {error_messages}')


def handler(event, context):
    dt_now = datetime.fromisoformat(event['time']).replace(second=0, microsecond=0)
    s3_bucket = os.environ['DATA_S3_BUCKET']
    s3_key = os.environ['ASSET_PROPERTY_ID_S3_KEY']
    asset_properties_path = f's3://{s3_bucket}/{s3_key}'
    property_values_path = f's3://{s3_bucket}/{VALUES_S3_KEY}'

    sitewise = boto3.client('iotsitewise')

    asset_properties = load_asset_properties(asset_properties_path)
    property_values = load_property_values(asset_properties, property_values_path)
    df = generate_values(asset_properties, property_values, property_values_path)
    send_values(sitewise, df, dt_now)
