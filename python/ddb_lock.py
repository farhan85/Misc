#!/usr/bin/env python3
# An example of using the DynamoDB lock library in boto3

import time

import boto3
from botocore.exceptions import ClientError
from python_dynamodb_lock.python_dynamodb_lock import DynamoDBLockClient, DynamoDBLockError


class DdbLock(object):
    def __init__(self, ddb_resource):
        self.lock_client = DynamoDBLockClient(ddb_resource)

    def acquire_lock(self, lock_name):
        return self.lock_client.acquire_lock(lock_name)

    @staticmethod
    def ensure_ddb_lock_table_exists(ddb_client):
        try:
            DynamoDBLockClient.create_dynamodb_table(ddb_client)
        except ClientError as e:
            if 'ResourceInUseException' in str(e):
                # Table already exists
                return
            raise


def do_something(ddb):
    lock_client = DdbLock(ddb)
    try:
        with lock_client.acquire_lock('test-lock'):
            print('Acquired lock. Sleeping for 5s')
            time.sleep(5)
            print("I'm awake now. Releasing lock")
    except DynamoDBLockError as e:
        if e.code == DynamoDBLockError.ACQUIRE_TIMEOUT:
            print('Another process already holds the lock')
        else:
            raise


if __name__ == '__main__':
    session = boto3.Session()
    ddb_resource = session.resource('dynamodb')
    DdbLock.ensure_ddb_lock_table_exists(ddb_resource.meta.client)
    do_something(ddb_resource)
