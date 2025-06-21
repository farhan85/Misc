#!/usr/bin/env python3

import boto3
import click
import time
from datetime import datetime, timezone
from tinydb import TinyDB, Query


# Use Query objects to make ORM-style DB queries
Model = Query()
Asset = Query()


def create_asset(sitewise, asset_model_id, asset_name):
    time.sleep(0.5)
    response = sitewise.create_asset(assetModelId=asset_model_id, assetName=asset_name)
    asset_id = response['assetId']
    print(f"Creating Asset {asset_name} ({asset_id})")
    return asset_id


def wait_for_asset_active(sitewise, asset_id, asset_name):
    print(f'Waiting for Asset {asset_name} to become Active...', end = '', flush=True)
    for _ in range(0, 60):
        status = sitewise.describe_asset(assetId=asset_id)['assetStatus']
        if status['state'] == 'ACTIVE':
            print('done')
            return
        print('.', end = '', flush=True)
        time.sleep(1)
    print('failed')
    raise Exception(f'Asset {asset_name} ({asset_id}) final status: {status}')


def new_asset(sitewise, assets_db, model, asset_name):
    if not assets_db.contains((Asset.type == model['type']) & (Asset.name == asset_name)):
        asset_id = create_asset(sitewise, model['id'], asset_name)
        asset = {'type': model['type'], 'id': asset_id, 'name': asset_name, 'model_id': model['id']}
        if 'hierarchy_id' in model:
            asset['hierarchy_id'] = model['hierarchy_id']
        assets_db.insert(asset)
        return asset_id


def enable_notifications(sitewise, asset_id, property_id):
    sitewise.update_asset_property(assetId=asset_id,
                                   propertyId=property_id,
                                   propertyNotificationState='ENABLED')

@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    models = db.table('models')
    assets = db.table('assets')
    prefix = config['resource_name_prefix']

    sitewise = boto3.client('iotsitewise', region_name=config['region'])

    factory_model = models.get(Model.type == 'factory')
    site_model = models.get(Model.type == 'site')
    generator_model = models.get(Model.type == 'generator')
    num_sites = config['num_sites']
    num_generators = config['num_generators']
    asset_ids = []

    for idx in range(1, num_generators + 1):
        asset_name = f'{prefix}-Generator-{idx}'
        if asset_id := new_asset(sitewise, assets, generator_model, asset_name):
            asset_ids.append((asset_id, asset_name))

    for idx in range(1, num_sites + 1):
        asset_name = f'{prefix}-Site-{idx}'
        if asset_id := new_asset(sitewise, assets, site_model, asset_name):
            asset_ids.append((asset_id, asset_name))

    factory_asset_name = f'{prefix}-Factory'
    if factory_asset_id := new_asset(sitewise, assets, factory_model, factory_asset_name):
        asset_ids.append((factory_asset_id, factory_asset_name))

    for asset_id, asset_name in asset_ids:
        wait_for_asset_active(sitewise, asset_id, asset_name)

    # Enable notifications for properties that will be forwarded to CloudWatch for monitoring
    enable_notifications(sitewise, factory_asset_id, factory_model['thermal_eff_prop_id'])


if __name__ == '__main__':
    main()
