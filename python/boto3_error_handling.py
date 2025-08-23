#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError


client = boto3.client('...')

try:
    client.api_call()
except ClientError as e:
    print('RequestId:     ', e.response['ResponseMetadata']['RequestId'])
    print('Error:         ', e.response['Error']['Code'])
    print('Error message: ', e.response['Error']['Message'])
    #print('Response obj:', e.response)

