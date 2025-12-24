import asyncio
import os
import random

import boto3
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from dynamodb_json import json_util as ddbjson


COMPLETED_MODELS_TABLE = os.environ['COMPLETED_MODELS_TABLE']
MODELS_TABLE = os.environ['MODELS_TABLE']
MAX_MODELS_DELETE = 500
MAX_MODELS_PARALLEL_DELETE = 10


async def scan_completed_models(ddb, group, max_results):
    params = {
        'TableName': COMPLETED_MODELS_TABLE,
        'FilterExpression': '#group = :g',
        'ExpressionAttributeValues': { ':g': { 'N': str(group) } },
        'ExpressionAttributeNames': { '#group': 'group' }
    }
    count = 0
    while True:
        response = await ddb.scan(**params)
        for item in response.get('Items', []):
            yield ddbjson.loads(item, as_dict=True)
            count += 1
            if count == max_results:
                return
        last_evaluated_key = response.get('LastEvaluatedKey')
        if last_evaluated_key:
            params['ExclusiveStartKey'] = last_evaluated_key
        else:
            break


async def more_models_to_delete(ddb, group):
    params = {
        'TableName': COMPLETED_MODELS_TABLE,
        'KeyConditionExpression': '#group = :g',
        'ExpressionAttributeValues': { ':g': { 'N': str(group) } },
        'ExpressionAttributeNames': { '#group': 'group' },
        'Select': 'COUNT'
    }
    response = await ddb.query(**params)
    return response['Count'] > 0


async def mark_model_deleted(ddb, new_event):
    key = { 'group': new_event['group'],
            'name': new_event['name'] }
    model_key = { 'name': new_event['name'] }
    transaction = [
        { 'Delete': { 'TableName': COMPLETED_MODELS_TABLE, 'Key': ddbjson.dumps(key, as_dict=True) } },
        { 'Delete': { 'TableName': MODELS_TABLE, 'Key': ddbjson.dumps(model_key , as_dict=True) } },
    ]
    await ddb.transact_write_items(TransactItems=transaction)


async def get_config(ddb):
    response = await ddb.get_item(TableName=MODELS_TABLE,
                                  Key=ddbjson.dumps({'name': 'config'}, as_dict=True))
    return ddbjson.loads(response['Item'], as_dict=True)


async def wait_for_model_deleted(sitewise, asset_model_id):
    for _ in range(0, 180):
        try:
            sw_model = await sitewise.describe_asset_model(assetModelId=asset_model_id)
            status = sw_model['assetModelStatus']
            if status['state'] == 'FAILED':
                break
            await asyncio.sleep(1)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return
            else:
                raise
    raise RuntimeError(f'Failed to delete AssetModel {asset_model_id} final status: {status}')


async def delete_sitewise_model(semaphore, sitewise, ddb, new_event):
    async with semaphore:
        model_name = new_event['name']
        model_id = new_event['sw_id']

        await asyncio.sleep(random.uniform(0.1, 1))
        try:
            response = await sitewise.delete_asset_model(assetModelId=model_id)
            print('Deleting AssetModel. Name={}, ID={}, RequestId={}'.format(
                model_name,
                model_id,
                response['ResponseMetadata']['RequestId']))
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                print('Failed to delete AssetModel. Name={}, ID={}, RequestId={}, Error={} {}'.format(
                    model_name,
                    model_id,
                    e.response['ResponseMetadata']['RequestId'],
                    e.response['Error']['Code'],
                    e.response['Error']['Message']))
                raise

        await wait_for_model_deleted(sitewise, model_id)
        await mark_model_deleted(ddb, new_event)
        print(f'Model {model_name} deleted')


async def delete_models(sitewise, ddb):
    config = await get_config(ddb)
    current_group = config['current_group']

    tasks = []
    semaphore = asyncio.Semaphore(MAX_MODELS_PARALLEL_DELETE)
    async for new_event in scan_completed_models(ddb, current_group, MAX_MODELS_DELETE):
        tasks.append(asyncio.ensure_future(delete_sitewise_model(semaphore, sitewise, ddb, new_event)))
    await asyncio.gather(*tasks)

    if await more_models_to_delete(ddb, current_group):
        return { 'finished': False }
    else:
        if current_group > 0:
            config['current_group'] -= 1
            await ddb.put_item(TableName=MODELS_TABLE, Item=ddbjson.dumps(config, as_dict=True))
            return { 'finished': False }
        else:
            return { 'finished': True }


async def async_handler(event, context):
    ddb_endpoint = os.environ.get('DDB_ENDPOINT')

    session = get_session()
    async with (session.create_client('iotsitewise') as sitewise,
                session.create_client('dynamodb', endpoint_url=ddb_endpoint) as ddb):
        return await delete_models(sitewise, ddb)


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_handler(event, context))
