#!/usr/bin/env python3

import boto3
import click
import time
from tinydb import TinyDB, Query


# Use a Query object to make ORM-style DB queries
Model = Query()

GENERATOR_POWER_MEAS_PROP_NAME = 'power'
GENERATOR_TEMP_MEAS_PROP_NAME = 'temperature_f'
SITE_HIERARCHY_NAME = 'hierarchy_1'
FACTORY_ALARM_PROP_NAME = 'power_rate_alarm'
FACTORY_HIERARCHY_NAME = 'hierarchy_1'


def wait_for_asset_model_active(sitewise, asset_model_id, asset_model_name):
    print(f'Waiting for AssetModel {asset_model_name} to become Active...', end = '', flush=True)
    for _ in range(0, 60):
        status = sitewise.describe_asset_model(assetModelId=asset_model_id)['assetModelStatus']
        if status['state'] == 'ACTIVE':
            print('done')
            return
        print('.', end = '', flush=True)
        time.sleep(1)
    print('failed')
    raise Exception(f'AssetModel {asset_model_name} ({asset_model_id}) final status: {status}')


def create_generator_asset_model(name_prefix):
    return {
        'assetModelName': f'{name_prefix}-Generator-Model',
        'assetModelDescription': 'Generator with raw power/temperature measurements',
        'assetModelProperties': [
            {
                'name': GENERATOR_POWER_MEAS_PROP_NAME ,
                'dataType': 'DOUBLE',
                'unit': 'Watts',
                'type': { 'measurement': {} }
            },
            {
                'name': GENERATOR_TEMP_MEAS_PROP_NAME ,
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
                        'variables': [
                            { 'name': 'f', 'value': { 'propertyId': 'temperature_f' } }
                        ]
                    }
                }
            }
        ]
    }


def create_site_asset_model(name_prefix, child_model_id):
    return {
        'assetModelName': f'{name_prefix}-Site-Model',
        'assetModelDescription': 'Site with multiple generators',
        'assetModelProperties': [],
        'assetModelHierarchies': [
            { 'name': SITE_HIERARCHY_NAME, 'childAssetModelId': child_model_id }
        ]
    }


def create_factory_asset_model(name_prefix, child_model_id):
    return {
        'assetModelName': f'{name_prefix}-Factory-Model',
        'assetModelDescription': 'Factory with multiple sites',
        'assetModelProperties': [],
        'assetModelCompositeModels': [
            {
                'name': FACTORY_ALARM_PROP_NAME,
                'type': 'AWS/ALARM',
                'properties': [
                    {
                        'name': 'AWS/ALARM_TYPE',
                        'dataType': 'STRING',
                        'unit': 'none',
                        'type': { 'attribute': { 'defaultValue': 'EXTERNAL' } }
                    },
                    {
                        'name': 'AWS/ALARM_STATE',
                        'dataType': 'STRUCT',
                        'dataTypeSpec': 'AWS/ALARM_STATE',
                        'unit': 'none',
                        'type': { 'measurement': {} }
                    }
                ]
            }
        ],
        'assetModelHierarchies': [
            { 'name': FACTORY_HIERARCHY_NAME, 'childAssetModelId': child_model_id }
        ]
    }


def create_asset_model(sitewise, asset_model_spec):
    response = sitewise.create_asset_model(**asset_model_spec)
    asset_model_id = response['assetModelId']
    print(f"Creating AssetModel {asset_model_spec['assetModelName']} ({asset_model_id})")
    return sitewise.describe_asset_model(assetModelId=asset_model_id)


def to_db_item(asset_model, asset_model_type):
    return {
        'type': asset_model_type,
        'id': asset_model['assetModelId'],
        'name': asset_model['assetModelName'],
        'property_id': {p['name']: p['id'] for p in asset_model['assetModelProperties']},
        'composite_model_property_id': {cm['name']: {p['name']: p['id'] for p in cm['properties']}
                                        for cm in asset_model.get('assetModelCompositeModels', [])},
        'hierarchy_id': asset_model['assetModelHierarchies'][0]['id'] if asset_model['assetModelHierarchies'] else None,
    }


def new_asset_model(sitewise, model_db, asset_model_type, model_spec):
    model = model_db.get(Model.type == asset_model_type)
    if model is None:
        model = create_asset_model(sitewise, model_spec)
        model = to_db_item(model, asset_model_type)
        model_db.insert(model)
        wait_for_asset_model_active(sitewise, model['id'], model['name'])
    return model


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    models = db.table('models')
    prefix = config['resource_name_prefix']

    sitewise = boto3.client('iotsitewise', region_name=config['region'])

    model_spec = create_generator_asset_model(prefix)
    generator_model = new_asset_model(sitewise, models, 'generator', model_spec)

    model_spec = create_site_asset_model(prefix, generator_model['id'])
    site_model = new_asset_model(sitewise, models, 'site', model_spec)

    model_spec = create_factory_asset_model(prefix, site_model['id'])
    factory_model = new_asset_model(sitewise, models, 'factory', model_spec)


if __name__ == '__main__':
    main()

