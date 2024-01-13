#!/usr/bin/env python

import os
import requests
import xml.dom.minidom
from requests_aws4auth import AWS4Auth


SERVICE_ENDPOINT = 's3.us-east-1.amazonaws.com'
SERVICE_REGION = 'us-east-1'
SERVICE_NAME = 's3'


aws_auth = AWS4Auth(os.getenv('AWS_ACCESS_KEY_ID'),
                    os.getenv('AWS_SECRET_ACCESS_KEY'),
                    SERVICE_REGION,
                    SERVICE_NAME,
                    session_token=os.getenv('AWS_SESSION_TOKEN', ''))


def list_buckets():
    url = f'https://{SERVICE_ENDPOINT}'
    r = requests.request('GET', url, auth=aws_auth)
    dom = xml.dom.minidom.parseString(r.text)
    print(dom.toprettyxml())


def get_object(bucket, key)
    url = f'https://{bucket}.{SERVICE_ENDPOINT}/{key}'
    r = requests.request('GET', url, auth=aws_auth)
    print(r.text)
