#!/usr/bin/env python3

import boto3
import click
import time
from datetime import datetime
from tinydb import TinyDB, Query


# Use Query objects to make ORM-style DB queries
Model = Query()
Asset = Query()


def create_entries(asset_id, property_ids):
    return [
        {
            'entryId': str(idx),
            'assetId': str(asset_id),
            'propertyId': str(property_id),
        }
       for idx, property_id in enumerate(property_ids)
    ]

def get_asset_property_values(sitewise, request_entries):
    params = { 'entries': request_entries }
    while True:
        response = sitewise.batch_get_asset_property_value(**params)
        if response['errorEntries']:
            error_messages = [entry['errorMessage'] for entry in response['errorEntries']]
            error_message = '\n'.join(error_messages)
            print(f'ERROR:\n{error_message }')
        for entry in response['successEntries']:
            yield entry
        if 'nextToken' not in response:
            break
        params['nextToken'] = response['nextToken']
        time.sleep(0.2)


def print_latest_values(sitewise, asset, model):
    asset_name, asset_id = asset['name'], asset['id']
    property_id_map = { p_id: p_name for p_name, p_id in model['property_id'].items() }
    property_id_map.update((prop['AWS/ALARM_STATE'], cm_name) for cm_name, prop in model['composite_model_property_id'].items())

    request_entries = create_entries(asset_id, property_id_map.keys())
    response_entries = get_asset_property_values(sitewise, request_entries)

    for entry in response_entries:
        entry_id = entry['entryId']
        request_entry = [e for e in request_entries if e['entryId'] == entry_id][0]
        asset_id = request_entry['assetId']
        property_id = request_entry['propertyId']
        property_name = property_id_map[property_id]
        if 'assetPropertyValue' in entry:
            property_value = entry['assetPropertyValue']
            dt = datetime.fromtimestamp(property_value['timestamp']['timeInSeconds'])
            value_type = list(property_value['value'].keys())[0]
            value = property_value['value'][value_type]
            print(f'{asset_name}, {property_name}, {dt.isoformat()}, {value}')
        else:
            print(f'{asset_name}, {property_name}, -, -')


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    models = db.table('models')
    assets = db.table('assets')

    sitewise = boto3.client('iotsitewise', region_name=config['region'])

    factory_model = models.get(Model.type == 'factory')
    site_model = models.get(Model.type == 'site')
    generator_model = models.get(Model.type == 'generator')

    factory_asset = assets.get(Asset.type == 'factory')
    site_assets = list(assets.search(Asset.type == 'site'))
    generator_assets = list(assets.search(Asset.type == 'generator'))

    print_latest_values(sitewise, factory_asset, factory_model)
    for site in site_assets:
        print_latest_values(sitewise, site, site_model)
        print_latest_values(sitewise, site, site_model)
    for generator in generator_assets:
        print_latest_values(sitewise, generator, generator_model)
        print_latest_values(sitewise, generator, generator_model)


if __name__ == '__main__':
    main()
