#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
from datetime import datetime


def value_to_metric_data(value, asset_id, property_id):
    timestamp = datetime.fromtimestamp(value['timestamp']['timeInSeconds'])
    value_type = list(value['value'].keys())[0]
    prop_value = 'null' if value_type == 'nullValue' else value['value'][value_type]
    quality = value.get('quality', 'UNKNOWN')
    return {
        'MetricName': f'Property_{property_id}',
        'Value': prop_value,
        'Timestamp': timestamp,
        'Dimensions': [
            {
                'Name': 'AssetId',
                'Value': asset_id
            },
            {
                'Name': 'Quality',
                'Value': quality
            }
        ]
    }


def handler(event, context):
    print('Event:', event)
    cw_client = boto3.client(service_name='cloudwatch')

    payload = event['payload']
    metric_data = [value_to_metric_data(value, payload['assetId'], payload['propertyId'])
                   for value in payload['values']]
    params = {
        'Namespace': 'IoTSiteWise/AssetMetrics',
        'MetricData': metric_data
    }
    print(f'Sending metrics to CloudWatch: {params}')

    response = cw_client.put_metric_data(**params)
    print('Sent to CW.', response)
