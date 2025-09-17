#!/usr/bin/env python3

import argparse
import time
from datetime import datetime, timezone

import boto3
from tenacity import retry, wait_exponential
from limits import parse, storage, strategies


RATE_LIMITER = strategies.MovingWindowRateLimiter(storage.MemoryStorage())
TPS_LIMIT = parse('3/second')


def tps_wait():
     while not RATE_LIMITER.hit(TPS_LIMIT):
         stats = RATE_LIMITER.get_window_stats(TPS_LIMIT)
         now = int(datetime.now(timezone.utc).timestamp())
         time.sleep(stats.reset_time - now)


def truncate_table(dynamodb, tableName):
    table = dynamodb.Table(tableName)

    # Only retrieve the table keys to minimize data transfer
    key_names = [key.get('AttributeName') for key in table.key_schema]

    # Use expression attribute names to protect from cases where the key names
    # are also DynamoDB reserved keywords
    projection_expression = ', '.join(f'#{name}' for name in key_names)
    expression_attribute_names = { f'#{name}': name for name in key_names }

    print('Scanning table for all items')
    dynamodb_items = []
    params = {
        'ProjectionExpression': projection_expression,
        'ExpressionAttributeNames': expression_attribute_names,
        'Limit': 10000  # Note that DynamoDB caps the returned data at 1MB
    }
    while True:
        tps_wait()
        response = table.scan(**params)
        dynamodb_items.extend(response['Items'])
        if 'LastEvaluatedKey' not in response:
            break
        params['ExclusiveStartKey'] = response['LastEvaluatedKey']

    print('Deleting all items')
    with table.batch_writer() as batch:

        @retry(wait=wait_exponential(multiplier=1, min=2, max=10))
        def delete_item(key):
            batch.delete_item(Key=key)

        for dynamodb_item in dynamodb_items:
            delete_item(key={ key: dynamodb_item[key] for key in key_names })


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--table-names', nargs='+', type=str, help='List of table names')
    args = parser.parse_args()

    dynamodb = boto3.resource('dynamodb')
    for table_name in args.table_names:
        truncate_table(dynamodb, table_name)
