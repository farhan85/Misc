import asyncio
import os
import random

import boto3
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from dynamodb_json import json_util as json


NEW_MODELS_TABLE = os.environ['NEW_MODELS_TABLE']
COMPLETED_MODELS_TABLE = os.environ['COMPLETED_MODELS_TABLE']
MODELS_TABLE = os.environ['MODELS_TABLE']
HIERARCHY_PREFIX = 'hierarchy'
MAX_MODELS_CREATE = 500
MAX_MODELS_PARALLEL_CREATE = 10


async def scan_new_models(ddb, group, max_results):
    params = {
        'TableName': NEW_MODELS_TABLE,
        'FilterExpression': '#group = :g',
        'ExpressionAttributeValues': { ':g': { 'N': str(group) } },
        'ExpressionAttributeNames': { '#group': 'group' }
    }
    count = 0
    while True:
        response = await ddb.scan(**params)
        for item in response.get('Items', []):
            yield json.loads(item, as_dict=True)
            count += 1
            if count == max_results:
                return
        last_evaluated_key = response.get('LastEvaluatedKey')
        if last_evaluated_key:
            params['ExclusiveStartKey'] = last_evaluated_key
        else:
            break


async def more_models_to_create(ddb, group):
    params = {
        'TableName': NEW_MODELS_TABLE,
        'KeyConditionExpression': '#group = :g',
        'ExpressionAttributeValues': { ':g': { 'N': str(group) } },
        'ExpressionAttributeNames': { '#group': 'group' },
        'Select': 'COUNT'
    }
    response = await ddb.query(**params)
    return response['Count'] > 0


async def mark_model_created(ddb, event):
    transaction = [
        { 'Delete': { 'TableName': NEW_MODELS_TABLE, 'Key': json.dumps(event, as_dict=True) } },
        { 'Put': { 'TableName': COMPLETED_MODELS_TABLE, 'Item': json.dumps(event, as_dict=True) } },
    ]
    await ddb.transact_write_items(TransactItems=transaction)


async def get_config(ddb):
    response = await ddb.get_item(TableName=MODELS_TABLE,
                                  Key=json.dumps({'name': 'config'}, as_dict=True))
    return json.loads(response['Item'], as_dict=True)


async def get_model(ddb, model_name):
    response = await ddb.get_item(TableName=MODELS_TABLE,
                                  Key=json.dumps({'name': model_name}, as_dict=True))
    return json.loads(response['Item'], as_dict=True)


def create_leaf_model_spec(name):
    return { 'assetModelName': name }


def create_parent_model_spec(name, child_model_ids):
    return {
        'assetModelName': name,
        'assetModelHierarchies': [
            { 'name': f'{HIERARCHY_PREFIX}-{idx}', 'childAssetModelId': child_id }
            for idx, child_id in enumerate(child_model_ids, start=1)
        ]
    }


async def wait_for_model_active(sitewise, asset_model_id):
    for _ in range(0, 300):
        sw_model = await sitewise.describe_asset_model(assetModelId=asset_model_id)
        status = sw_model['assetModelStatus']
        if status['state'] == 'ACTIVE':
            return
        await asyncio.sleep(1)
    raise Exception(f'Failed to create AssetModel {asset_model_id} final status: {status}')


async def create_sitewise_model(semaphore, sitewise, ddb, new_event):
    async with semaphore:
        model = await get_model(ddb, new_event['name'])
        model_name = model['name']
        model_id = model['sw_id']
        if model_id is None:
            if model['is_leaf_node']:
                model_spec = create_leaf_model_spec(model_name)
            else:
                child_ids = []
                for child_name in model['children']:
                    child = await get_model(ddb, child_name)
                    child_ids.append(child['sw_id'])
                model_spec = create_parent_model_spec(model_name, child_ids)

            await asyncio.sleep(random.uniform(0.1, 1))
            try:
                response = await sitewise.create_asset_model(**model_spec)
                model_id = response['assetModelId']
                print('Creating AssetModel. Name={}, Id={}, RequestId={}'.format(
                    model_name,
                    model_id,
                    response['ResponseMetadata']['RequestId']))
                model['sw_id'] = model_id
                await ddb.put_item(TableName=MODELS_TABLE, Item=json.dumps(model, as_dict=True))
            except ClientError as e:
                print('Failed to create AssetModel. Name={}, RequestId={}, Error={} {}'.format(
                    model_name,
                    e.response['ResponseMetadata']['RequestId'],
                    e.response['Error']['Code'],
                    e.response['Error']['Message']))
                raise

        await wait_for_model_active(sitewise, model_id)
        await mark_model_created(ddb, new_event)
        print(f'AssetModel {model_name} created')


async def create_models(sitewise, ddb):
    config = await get_config(ddb)
    current_group = config['current_group']
    tasks = []
    semaphore = asyncio.Semaphore(MAX_MODELS_PARALLEL_CREATE)
    async for new_event in scan_new_models(ddb, current_group, MAX_MODELS_CREATE):
        tasks.append(asyncio.ensure_future(create_sitewise_model(semaphore, sitewise, ddb, new_event)))
    await asyncio.gather(*tasks)


    if await more_models_to_create(ddb, current_group):
        return { 'finished': False }
    else:
        if await more_models_to_create(ddb, current_group + 1):
            config['current_group'] += 1
            await ddb.put_item(TableName=MODELS_TABLE, Item=json.dumps(config, as_dict=True))
            return { 'finished': False }
        else:
            return { 'finished': True }


async def async_handler(event, context):
    ddb_endpoint = os.environ.get('DDB_ENDPOINT')
    session = get_session()
    async with (session.create_client('iotsitewise') as sitewise,
                session.create_client('dynamodb', endpoint_url=ddb_endpoint) as ddb):
        return await create_models(sitewise, ddb)


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_handler(event, context))
