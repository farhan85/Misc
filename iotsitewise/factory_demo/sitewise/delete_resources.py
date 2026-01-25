#!/usr/bin/env python3

import boto3
import click
import time
from tinydb import TinyDB, Query


# Use Query objects to make ORM-style DB queries
Model = Query()
Interface = Query()
Asset = Query()
Association = Query()
AnomalyDetection = Query()


def disassociate_assets(sitewise, parent_asset_id, parent_asset_name, hierarchy_id, child_asset_id, child_asset_name):
    print(f'Disassociating Assets. {parent_asset_name} -> {child_asset_name}, Hierarchy={hierarchy_id}')
    sitewise.disassociate_assets(assetId=parent_asset_id, hierarchyId=hierarchy_id, childAssetId=child_asset_id)
    time.sleep(0.5)


def delete_asset(sitewise, asset_id, asset_name):
    print('Deleting Asset', asset_name)
    sitewise.delete_asset(assetId=asset_id)
    time.sleep(0.5)


def delete_asset_model(sitewise, asset_model_id, asset_model_name):
    print('Deleting AssetModel', asset_model_name)
    sitewise.delete_asset_model(assetModelId=asset_model_id)
    time.sleep(0.5)


def wait_for_asset_deleted(sitewise, asset_id, asset_name):
    print(f'Waiting for Asset {asset_name} to be deleted...', end = '', flush=True)
    for _ in range(0, 60):
        try:
            status = sitewise.describe_asset(assetId=asset_id)['assetStatus']
            print('.', end = '', flush=True)
            time.sleep(1)
        except sitewise.exceptions.ResourceNotFoundException:
            print('done')
            return
    print('failed')
    raise Exception(f'Failed to delete Asset {asset_name} ({asset_id}). Final status: {status}')


def wait_for_asset_model_deleted(sitewise, asset_model_id, asset_model_name):
    print(f'Waiting for AssetModel {asset_model_name} to be deleted...', end = '', flush=True)
    for _ in range(0, 60):
        try:
            status = sitewise.describe_asset_model(assetModelId=asset_model_id)['assetModelStatus']
            print('.', end = '', flush=True)
            time.sleep(1)
        except sitewise.exceptions.ResourceNotFoundException:
            print('done')
            return
    print('failed')
    raise Exception(f'Failed to delete AssetModel {asset_model_name} ({asset_model_id}). Final status: {status}')


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    models = db.table('models')
    interfaces = db.table('interfaces')
    assets = db.table('assets')
    associations = db.table('associations')
    anomaly_detection = db.table('anomaly_detection')

    sitewise = boto3.client('iotsitewise', region_name=config['region'])
    cw_events = boto3.client('events', region_name=config['region'])
    cw_client = boto3.client('cloudwatch', region_name=config['region'])

    print('Stopping MeasurementGenInvoker')
    cw_events.disable_rule(Name=config['meas_gen_invoker_rule'])

    print('Deleting CW Alarms')
    cw_client.delete_alarms(AlarmNames=['PowerRateAlarm'])

    for a in associations:
        parent_name = assets.get(Asset.id == a['parent_id'])['name']
        child_name = assets.get(Asset.id == a['child_id'])['name']
        disassociate_assets(sitewise, a['parent_id'], parent_name, a['hierarchy_id'], a['child_id'], child_name)
        associations.remove(Query().fragment(a))

    all_assets = list(assets)
    for asset in all_assets:
        delete_asset(sitewise, asset['id'], asset['name'])
    for asset in all_assets:
        asset_id = asset['id']
        wait_for_asset_deleted(sitewise, asset_id, asset['name'])
        assets.remove(Asset.id == asset_id)

    anomaly_detection.remove(AnomalyDetection.type == 'bulk_import_job')
    anomaly_detection.remove(AnomalyDetection.type == 'generated_data')

    factory_model = models.get(Model.type == 'factory')
    site_model = models.get(Model.type == 'site')
    generator_model = models.get(Model.type == 'generator')

    for model in (factory_model, site_model, generator_model):
        if model:
            model_id, model_name = model['id'], model['name']
            delete_asset_model(sitewise, model_id, model_name)
            wait_for_asset_model_deleted(sitewise, model_id, model_name)
            models.remove(Model.id == model_id)

    factory_interface = interfaces.get(Interface.type == 'factory')
    site_interface = interfaces.get(Interface.type == 'site')
    generator_interface = interfaces.get(Interface.type == 'generator')

    for interface in (factory_interface, site_interface, generator_interface):
        if interface:
            interface_id, interface_name = interface['id'], interface['name']
            delete_asset_model(sitewise, interface_id, interface_name)
            wait_for_asset_model_deleted(sitewise, interface_id, interface_name)
            interfaces.remove(Interface.id == interface_id)

if __name__ == '__main__':
    main()
