#!/usr/bin/env python3

import os
import sys
import time
from datetime import datetime

import boto3
import click
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session


def assume_role_creds(sts_client, role_arn, role_session_name):
    response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=role_session_name)
    creds = response['Credentials']
    return {
        'access_key': creds['AccessKeyId'],
        'secret_key': creds['SecretAccessKey'],
        'token': creds['SessionToken'],
        'expiry_time': creds['Expiration'].isoformat()
    }


def auto_refresh_session(region_name, creds_provider, creds_method):
    session_credentials = RefreshableCredentials.create_from_metadata(
        metadata=creds_provider(),
        refresh_using=creds_provider,
        method=creds_method)
    session = get_session()
    session._credentials = session_credentials
    session.set_config_variable("region", region_name)
    return boto3.Session(botocore_session=session)


def test_refreshing_session(session):
    sqs = session.resource('sqs')
    count = 1
    while True:
        print(f'{count} minutes - {[q for q in sqs.queues.all()]}')
        time.sleep(60)
        count += 1


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-a', '--role-arn', help='The IAM role ARN')
@click.option('-s', '--role-session-name', help='The role session name')
@click.option('-r', '--region-name', help='Region name')
def main(role_arn, role_session_name, region_name):
    if 'AWS_ACCESS_KEY_ID' not in os.environ or 'AWS_SECRET_ACCESS_KEY' not in os.environ:
        sys.exit('Missing credential env variables')

    role_session_name = role_session_name or f'session-{int(datetime.now().timestamp())}'
    sts = boto3.client('sts', region_name=region_name)
    session = auto_refresh_session(
            region_name,
            lambda: assume_role_creds(sts, role_arn, role_session_name),
            'sts-assume-role')

    test_refreshing_session(session)


if __name__ == '__main__':
    main()
