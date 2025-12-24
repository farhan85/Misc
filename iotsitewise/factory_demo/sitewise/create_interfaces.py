#!/usr/bin/env python3

import boto3
import click
import time
from tinydb import TinyDB, Query


# Use a Query object to make ORM-style DB queries
Interface = Query()
Model = Query()

GENERATOR_POWER_PROP_NAME = 'power_avg'
GENERATOR_TEMP_PROP_NAME = 'temperature_avg'
SITE_POWER_PROP_NAME = 'power_max'
SITE_TEMP_PROP_NAME = 'temperature_avg'
SITE_HIERARCHY_NAME = 'hierarchy_1'
FACTORY_POWER_PROP_NAME = 'power_rate'
FACTORY_HIERARCHY_NAME = 'hierarchy_1'


def wait_for_asset_model_active(sitewise, asset_model_id, asset_model_name):
    print(f'Waiting for AssetModel {asset_model_name} to become Active...', end = '', flush=True)
    for _ in range(0, 60):
        state = sitewise.describe_asset_model(assetModelId=asset_model_id)['assetModelStatus']['state']
        if state == 'ACTIVE':
            print('done')
            return
        print('.', end = '', flush=True)
        time.sleep(1)
    print('failed')
    raise Exception(f'AssetModel {asset_model_name} ({asset_model_id}) final state: {state}')


def create_generator_interface(name_prefix):
    return {
        'assetModelName': f'{name_prefix}-Generator-Interface',
        'assetModelType': 'INTERFACE',
        'assetModelProperties': [
            {
                'name': 'power',
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
                            { 'name': 'p', 'value': { 'propertyId': 'power' } }
                        ],
                        'window': { 'tumbling': { 'interval': '1m' } }
                    }
                }
            },
            {
                'name': 'temperature_c',
                'dataType': 'DOUBLE',
                'unit': 'Celsius',
                'type': { 'measurement': {} }
            },
            {
                'name': GENERATOR_TEMP_PROP_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Celsius',
                'type': {
                    'metric': {
                        'expression': 'avg(t)',
                        'variables': [
                            { 'name': 't', 'value': { 'propertyId': 'temperature_c' } }
                        ],
                        'window': { 'tumbling': { 'interval': '1m' } }
                    }
                }
            }
        ]
    }


def create_site_interface(name_prefix, child_interface_id, power_prop_id, temp_prop_id):
    return {
        'assetModelName': f'{name_prefix}-Site-Interface',
        'assetModelType': 'INTERFACE',
        'assetModelProperties': [
            {
                'name': SITE_POWER_PROP_NAME,
                'dataType': 'DOUBLE',
                'unit': 'Watts',
                'type': {
                    'metric': {
                        'expression': 'max(p)',
                        'variables': [
                            { 'name': 'p', 'value': { 'propertyId': power_prop_id, 'hierarchyId': SITE_HIERARCHY_NAME } }
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
                            { 'name': 't', 'value': { 'propertyId': temp_prop_id, 'hierarchyId': SITE_HIERARCHY_NAME } }
                        ],
                        'window': { 'tumbling': { 'interval': '1m' } }
                    }
                }
            }
        ],
        'assetModelHierarchies': [
            { 'name': SITE_HIERARCHY_NAME, 'childAssetModelId': child_interface_id }
        ]
    }


def create_factory_interface(name_prefix, child_interface_id, power_prop_id, temp_prop_id):
    return {
        'assetModelName': f'{name_prefix}-Factory-Interface',
        'assetModelType': 'INTERFACE',
        'assetModelProperties': [
            {
                'name': FACTORY_POWER_PROP_NAME,
                'dataType': 'DOUBLE',
                'unit': 'W/C',
                'type': {
                    'metric': {
                        'expression': 'avg(p)/avg(t)',
                        'variables': [
                            { 'name': 'p', 'value': { 'propertyId': power_prop_id, 'hierarchyId': FACTORY_HIERARCHY_NAME  } },
                            { 'name': 't', 'value': { 'propertyId': temp_prop_id, 'hierarchyId': FACTORY_HIERARCHY_NAME  } }
                        ],
                        'window': { 'tumbling': { 'interval': '1m' } }
                    }
                }
            }
        ],
        'assetModelCompositeModels': [],
        'assetModelHierarchies': [
            { 'name': FACTORY_HIERARCHY_NAME , 'childAssetModelId': child_interface_id }
        ]
    }


def create_asset_model(sitewise, asset_model_spec):
    response = sitewise.create_asset_model(**asset_model_spec)
    asset_model_id = response['assetModelId']
    print(f"Creating AssetModel {asset_model_spec['assetModelName']} ({asset_model_id})")
    return sitewise.describe_asset_model(assetModelId=asset_model_id)


def apply_interface_to_model(sitewise, interface_id, interface_name, model_id, model_name):
    print(f'Applying Interface {interface_name} to Model {model_name}')
    sitewise.put_asset_model_interface_relationship(
        assetModelId=model_id,
        interfaceAssetModelId=interface_id,
        propertyMappingConfiguration={'matchByPropertyName': True,
                                      'createMissingProperty': True,
                                      'overrides': []})


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
    interfaces = db.table('interfaces')
    models = db.table('models')
    prefix = config['resource_name_prefix']

    sitewise = boto3.client('iotsitewise', region_name=config['region'])

    generator_model = models.get(Model.type == 'generator')
    site_model = models.get(Model.type == 'site')
    factory_model = models.get(Model.type == 'factory')

    model_spec = create_generator_interface(prefix)
    generator_interface = new_asset_model(sitewise, interfaces, 'generator', model_spec)

    model_spec = create_site_interface(prefix,
                                       generator_interface['id'],
                                       generator_interface['property_id'][GENERATOR_POWER_PROP_NAME],
                                       generator_interface['property_id'][GENERATOR_TEMP_PROP_NAME])
    site_interface = new_asset_model(sitewise, interfaces, 'site', model_spec)

    model_spec = create_factory_interface(prefix,
                                          site_interface['id'],
                                          site_interface['property_id'][SITE_POWER_PROP_NAME],
                                          site_interface['property_id'][SITE_TEMP_PROP_NAME])
    factory_interface = new_asset_model(sitewise, interfaces, 'factory', model_spec)

    interface_and_models = [ (generator_interface, generator_model),
                             (site_interface, site_model),
                             (factory_interface, factory_model) ]

    for iface, model in interface_and_models:
        if 'interface_id' not in model:
            apply_interface_to_model(sitewise, iface['id'], iface['name'], model['id'], model['name'])

            new_model = sitewise.describe_asset_model(assetModelId=model['id'])
            new_model = to_db_item(new_model, model['type'])
            new_model['interface_id'] = iface['id']
            models.update(new_model, Model.id == model['id'])

    for _, model in interface_and_models:
        wait_for_asset_model_active(sitewise, model['id'], model['name'])


if __name__ == '__main__':
    main()

