import asyncio
import os
import random

import boto3
import json
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from dynamodb_json import json_util as ddbjson


COMPLETED_MODELS_TABLE = os.environ['COMPLETED_MODELS_TABLE']
MODELS_TABLE = os.environ['MODELS_TABLE']
S3_BUCKET = os.environ['DATA_BUCKET']
MODELS_FILE_KEY = os.environ['MODELS_FILE_KEY']
HIERARCHY_PREFIX = 'hierarchy'
MAX_MODELS_CREATE = 500
MAX_MODELS_PARALLEL_CREATE = 10
TEMPERATURE_METRIC_NAME = 'temperature_avg'


async def get_models_file(s3):
    response = await s3.get_object(Bucket=S3_BUCKET, Key=MODELS_FILE_KEY)
    async with response['Body'] as stream:
        file_content = await stream.read()
    return json.loads(file_content.decode('utf-8'))


async def save_models_file(s3, models):
    await s3.put_object(Body=json.dumps(models), Bucket=S3_BUCKET, Key=MODELS_FILE_KEY, ContentType='application/json')


async def save_new_model_ddb(ddb, new_model):
    model_group = {
        'group': new_model['group'],
        'name': new_model['name'],
        'sw_id': new_model['sw_id'],
    }
    ddb_model = {
         'name': new_model['name'],
         'sw_id': new_model['sw_id'],
         'children': new_model['children'],
         'metric_id': new_model.get('metric_id'),
    }
    transaction = [
        { 'Put': { 'TableName': COMPLETED_MODELS_TABLE, 'Item': ddbjson.dumps(model_group, as_dict=True) } },
        { 'Put': { 'TableName': MODELS_TABLE, 'Item': ddbjson.dumps(ddb_model, as_dict=True) } },
    ]
    await ddb.transact_write_items(TransactItems=transaction)


async def get_config(ddb):
    response = await ddb.get_item(TableName=MODELS_TABLE,
                                  Key=ddbjson.dumps({'name': 'config'}, as_dict=True))
    return ddbjson.loads(response['Item'], as_dict=True)


async def get_model(ddb, model_name):
    try:
        response = await ddb.get_item(TableName=MODELS_TABLE,
                                      Key=ddbjson.dumps({'name': model_name}, as_dict=True))
        return ddbjson.loads(response['Item'], as_dict=True)
    except KeyError:
        return None


def create_leaf_model_spec(name):
    return {
        'assetModelName': name,
        'assetModelProperties': [
            {
                'name': 'temperature_f',
                'dataType': 'DOUBLE',
                'unit': 'Fahrenheit',
                'type': { 'measurement': {} }
            },
            {
                'name': 'temperature_c',
                'dataType': 'DOUBLE',
                'unit': 'Celsius',
                'type': {
                    'transform': {
                        'expression': '(f - 32.0)*(5.0/9.0)',
                        'variables': [ { 'name': 'f', 'value':  { 'propertyId':  'temperature_f' } } ]
                    }
                }
            },
            {
                'name': TEMPERATURE_METRIC_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Celsius',
                'type': {
                    'metric': {
                        'expression': 'avg(t)',
                        'variables': [ { 'name': 't', 'value':  { 'propertyId':  'temperature_c' } } ],
                        'window': { 'tumbling': { 'interval': '5m' } }
                    }
                }
            }
        ]
    }


def create_parent_model_spec(name, child_models):
    expression_vars = []
    variables = []
    hierarchies = []
    for idx, child in enumerate(child_models, start=1):
        child_model_id = child['sw_id']
        child_metric_id = child['metric_id']
        hierarchy_name = f'{HIERARCHY_PREFIX}-{idx}'
        var_name = f't_{idx}'
        expression_vars.append(var_name)
        variables.append({'name': var_name,
                          'value': {'propertyId': child_metric_id, 'hierarchyId': hierarchy_name}})
        hierarchies.append({'name': hierarchy_name, 'childAssetModelId': child_model_id})
    return {
        'assetModelName': name,
        'assetModelProperties': [
            {
                'name': TEMPERATURE_METRIC_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Celsius',
                'type': {
                    'metric': {
                        'expression': 'avg({})'.format(','.join(expression_vars)),
                        'variables': variables,
                        'window': { 'tumbling': { 'interval': '5m' } }
                    }
                }
            }
        ],
        'assetModelHierarchies': hierarchies
    }


async def wait_for_model_active(sitewise, asset_model_id):
    for _ in range(0, 300):
        sw_model = await sitewise.describe_asset_model(assetModelId=asset_model_id)
        status = sw_model['assetModelStatus']
        if status['state'] == 'ACTIVE':
            return
        await asyncio.sleep(1)
    raise Exception(f'Failed to create AssetModel {asset_model_id} final status: {status}')


def get_prop_id(asset_model, prop_name):
    for property in asset_model.get('assetModelProperties', []):
        if property['name'] == prop_name:
            return property['id']


async def _create_sitewise_model(sitewise, ddb, new_model):
    model_name = new_model['name']
    if new_model['is_leaf_node']:
        model_spec = create_leaf_model_spec(model_name)
    else:
        child_models = []
        for child_name in new_model['children']:
            child = await get_model(ddb, child_name)
            child_models.append(child)
        model_spec = create_parent_model_spec(model_name, child_models)

    await asyncio.sleep(random.uniform(0.1, 1))
    try:
        response = await sitewise.create_asset_model(**model_spec)
        model_id = response['assetModelId']
        print('Creating AssetModel. Name={}, Id={}, RequestId={}'.format(
            model_name,
            model_id,
            response['ResponseMetadata']['RequestId']))

        response = await sitewise.describe_asset_model(assetModelId=model_id)
        new_model['sw_id'] = model_id
        new_model['metric_id'] = get_prop_id(response, TEMPERATURE_METRIC_NAME)
        await save_new_model_ddb(ddb, new_model)
        return model_id
    except ClientError as e:
        print('Failed to create/describe AssetModel. Name={}, RequestId={}, Error={} {}'.format(
            model_name,
            e.response['ResponseMetadata']['RequestId'],
            e.response['Error']['Code'],
            e.response['Error']['Message']))
        raise


async def create_sitewise_model(semaphore, sitewise, ddb, new_model):
    async with semaphore:
        model_name = new_model['name']
        model = await get_model(ddb, model_name)
        if model is None:
            model_id = await _create_sitewise_model(sitewise, ddb, new_model)
        else:
            model_id = model['sw_id']

        await wait_for_model_active(sitewise, model_id)
        print(f'AssetModel {model_name} created')


async def create_models(sitewise, s3, ddb):
    models = await get_models_file(s3)
    config = await get_config(ddb)
    current_group = config['current_group']
    next_batch = [m for m in models['models'] if m['group'] == current_group and m['sw_id'] is None]
    total_model_count = len(next_batch)
    next_batch = next_batch[0:MAX_MODELS_CREATE]

    tasks = []
    semaphore = asyncio.Semaphore(MAX_MODELS_PARALLEL_CREATE)
    try:
        for new_model in next_batch:
            tasks.append(asyncio.ensure_future(create_sitewise_model(semaphore, sitewise, ddb, new_model)))
        await asyncio.gather(*tasks)
    finally:
        await save_models_file(s3, models)

    if len(next_batch) < total_model_count:
        return { 'finished': False }
    else:
        if next((m for m in models['models'] if m['group'] == current_group + 1), None) is not None:
            config['current_group'] += 1
            await ddb.put_item(TableName=MODELS_TABLE, Item=ddbjson.dumps(config, as_dict=True))
            return { 'finished': False }
        else:
            return { 'finished': True }


async def async_handler(event, context):
    ddb_endpoint = os.environ.get('DDB_ENDPOINT')

    session = get_session()
    async with (session.create_client('iotsitewise') as sitewise,
                session.create_client('s3') as s3,
                session.create_client('dynamodb', endpoint_url=ddb_endpoint) as ddb):
        return await create_models(sitewise, s3, ddb)


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_handler(event, context))
