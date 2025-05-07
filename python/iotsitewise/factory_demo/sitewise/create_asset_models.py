#!/usr/bin/env python3

import boto3
import click
import time
from tinydb import TinyDB, Query


# Use a Query object to make ORM-style DB queries
Model = Query()

GENERATOR_POWER_MEAS_PROP_NAME = 'power'
GENERATOR_TEMP_MEAS_PROP_NAME = 'temperature_f'
GENERATOR_POWER_PROP_NAME = 'power_avg'
GENERATOR_TEMP_PROP_NAME = 'temperature_avg'
SITE_POWER_PROP_NAME = 'power_max'
SITE_TEMP_PROP_NAME = 'temperature_avg'
SITE_HIERARCHY_NAME = 'hierarchy_1'
FACTORY_HIERARCHY_NAME = 'hierarchy_1'
FACTORY_THERM_EFF_PROP_NAME = 'thermal_efficiency'


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
        'assetModelName': f'{name_prefix}-GeneratorModel',
        'assetModelDescription': 'Generator with raw power/temperature measurements',
        'assetModelProperties': [
            {
                'name': GENERATOR_POWER_MEAS_PROP_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Watts',
                'type': { 'measurement': {} }
            },
            {
                'name': GENERATOR_POWER_PROP_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Watts',
                'type': {
                    'metric': {
                        'expression': 'avg(p)',
                        'variables': [
                            { 'name': 'p', 'value':  { 'propertyId':  'power' } }
                        ],
                        'window': { 'tumbling': { 'interval': '1m' } }
                    }
                }
            },
            {
                'name': GENERATOR_TEMP_MEAS_PROP_NAME,
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
                            { 'name': 'f', 'value':  { 'propertyId':  'temperature_f' } }
                        ]
                    }
                }
            },
            {
                'name': GENERATOR_TEMP_PROP_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Celsius',
                'type': {
                    'metric': {
                        'expression': 'avg(t)',
                        'variables': [
                            { 'name': 't', 'value':  { 'propertyId':  'temperature_c' } }
                        ],
                        'window': { 'tumbling': { 'interval': '1m' } }
                    }
                }
            }
        ]
    }


def create_site_asset_model(name_prefix, child_model_id, power_prop_id, temp_prop_id):
    return {
        'assetModelName': f'{name_prefix}-SiteModel',
        'assetModelDescription': 'Site with multiple generators',
        'assetModelProperties': [
            {
                'name': SITE_POWER_PROP_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Watts',
                'type': {
                    'metric': {
                        'expression': 'max(p)',
                        'variables': [
                            { 'name': 'p', 'value':  { 'propertyId':  power_prop_id, 'hierarchyId':  SITE_HIERARCHY_NAME } }
                        ],
                        'window': { 'tumbling': { 'interval': '1m' } }
                    }
                }
            },
            {
                'name': SITE_TEMP_PROP_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Celsius',
                'type': {
                    'metric': {
                        'expression': 'avg(t)',
                        'variables': [
                            { 'name': 't', 'value':  { 'propertyId':  temp_prop_id, 'hierarchyId':  SITE_HIERARCHY_NAME } }
                        ],
                        'window': { 'tumbling': { 'interval': '1m' } }
                    }
                }
            }
        ],
        'assetModelHierarchies': [
            { 'name': SITE_HIERARCHY_NAME, 'childAssetModelId': child_model_id }
        ]
    }


def create_factory_asset_model(name_prefix, child_model_id, power_prop_id, temp_prop_id):
    return {
        'assetModelName': f'{name_prefix}-FactoryModel',
        'assetModelDescription': 'Factory with multiple sites',
        'assetModelProperties': [
            {
                'name': FACTORY_THERM_EFF_PROP_NAME,
                'dataType': 'DOUBLE',
                'unit': 'W/C',
                'type': {
                    'metric': {
                        'expression': 'avg(p)/avg(t)',
                        'variables': [
                            { 'name': 'p', 'value':  { 'propertyId':  power_prop_id, 'hierarchyId':  FACTORY_HIERARCHY_NAME } },
                            { 'name': 't', 'value':  { 'propertyId':  temp_prop_id, 'hierarchyId':  FACTORY_HIERARCHY_NAME } }
                        ],
                        'window': { 'tumbling': { 'interval': '1m' } }
                    }
                }
            }
        ],
        'assetModelCompositeModels': [],
        'assetModelHierarchies': [
            { 'name': FACTORY_HIERARCHY_NAME, 'childAssetModelId': child_model_id }
        ]
    }


def create_asset_model(sitewise, asset_model_spec):
    response = sitewise.create_asset_model(**asset_model_spec)
    asset_model_id = response['assetModelId']
    print(f"Creating AssetModel {asset_model_spec['assetModelName']} ({asset_model_id})")
    return sitewise.describe_asset_model(assetModelId=asset_model_id)


def get_prop_id(asset_model, prop_name):
    return next(p for p in asset_model.get('assetModelProperties', []) if p['name'] == prop_name)['id']


def get_hierarchy_id(asset_model, hierarchy_name):
    return next(h for h in asset_model.get('assetModelHierarchies', []) if h['name'] == hierarchy_name)['id']


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    models = db.table('models')
    prefix = config['resource_name_prefix']

    sitewise = boto3.client('iotsitewise', region_name=config['region'])

    generator_model = models.get(Model.type == 'generator')
    if generator_model is None:
        generator_model = create_generator_asset_model(prefix)
        generator_model = create_asset_model(sitewise, generator_model)
        generator_model = {
            'type': 'generator',
            'id': generator_model['assetModelId'],
            'name': generator_model['assetModelName'],
            'power_meas_prop_id': get_prop_id(generator_model, GENERATOR_POWER_MEAS_PROP_NAME),
            'temp_meas_prop_id': get_prop_id(generator_model, GENERATOR_TEMP_MEAS_PROP_NAME),
            'power_prop_id': get_prop_id(generator_model, GENERATOR_POWER_PROP_NAME),
            'temp_prop_id': get_prop_id(generator_model, GENERATOR_TEMP_PROP_NAME),
        }
        models.insert(generator_model)
        wait_for_asset_model_active(sitewise, generator_model['id'], generator_model['name'])

    site_model = models.get(Model.type == 'site')
    if site_model  is None:
        site_model = create_site_asset_model(prefix, generator_model['id'], generator_model['power_prop_id'], generator_model['temp_prop_id'])
        site_model = create_asset_model(sitewise, site_model)
        site_model = {
            'type': 'site',
            'id': site_model['assetModelId'],
            'name': site_model['assetModelName'],
            'power_prop_id': get_prop_id(site_model, SITE_POWER_PROP_NAME),
            'temp_prop_id': get_prop_id(site_model, SITE_TEMP_PROP_NAME),
            'hierarchy_id': get_hierarchy_id(site_model, SITE_HIERARCHY_NAME),
        }
        models.insert(site_model)
        wait_for_asset_model_active(sitewise, site_model['id'], site_model['name'])

    factory_model = models.get(Model.type == 'factory')
    if models.get(Model.type == 'factory')  is None:
        factory_model = create_factory_asset_model(prefix, site_model['id'], site_model['power_prop_id'], site_model['temp_prop_id'])
        factory_model = create_asset_model(sitewise, factory_model)
        factory_model = {
            'type': 'factory',
            'id': factory_model['assetModelId'],
            'name': factory_model['assetModelName'],
            'thermal_eff_prop_id': get_prop_id(factory_model, FACTORY_THERM_EFF_PROP_NAME),
            'hierarchy_id': get_hierarchy_id(factory_model, FACTORY_HIERARCHY_NAME),
        }
        models.insert(factory_model)
        wait_for_asset_model_active(sitewise, factory_model['id'], factory_model['name'])


if __name__ == '__main__':
    main()

