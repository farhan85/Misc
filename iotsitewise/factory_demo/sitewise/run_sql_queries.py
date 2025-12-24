#!/usr/bin/env python3

import boto3
import click
import time
from tabulate import tabulate
from tinydb import TinyDB, Query


# Use Query objects to make ORM-style DB queries
Model = Query()
Asset = Query()


def all_assets():
    return '''
        SELECT asset_id, asset_name, asset_model_id, parent_asset_id
        FROM asset
    '''


def assets_with_id(asset_id):
    return f'''
        SELECT a.asset_id, a.asset_name
        FROM asset a
        WHERE a.asset_id = '{asset_id}'
    '''


def asset_properties(asset_id):
    return f'''
        SELECT a.asset_name, p.property_name
        FROM asset a, asset_property p
        WHERE a.asset_id = '{asset_id}'
    '''


def assets_with_name(asset_name):
    return f'''
        SELECT a.asset_id, a.asset_name
        FROM asset a
        WHERE a.asset_name LIKE '%{asset_name}%'
    '''


def assets_with_property(property_name):
    return f'''
        SELECT a.asset_id, a.asset_name, p.property_name
        FROM asset a, asset_property p
        WHERE p.property_name LIKE '%{property_name}%'
    '''


def property_latest_values(property_name):
    return f'''
        SELECT a.asset_id, p.property_id, a.asset_name, p.property_name, ts.double_value, ts.event_timestamp
        FROM asset a, asset_property p, latest_value_time_series ts
        WHERE p.property_name = '{property_name}'
    '''


def assets_with_property_double_value(property_name, comparison_operator, property_value):
    return f'''
        SELECT a.asset_id, p.property_id, a.asset_name, p.property_name, ts.double_value, ts.event_timestamp
        FROM asset a, asset_property p, latest_value_time_series ts
        WHERE p.property_name = '{property_name}'
          AND ts.double_value {comparison_operator} {property_value}
    '''


def assets_with_property_double_value_using_uuids(asset_id, property_id, comparison_operator, property_value):
    return f'''
        SELECT a.asset_id, a.asset_name, p.property_name, p.property_id, ts.double_value, ts.event_timestamp
        FROM asset a, asset_property p, latest_value_time_series ts
        WHERE a.asset_id = '{asset_id}'
          AND p.property_id = '{property_id}'
          AND ts.double_value {comparison_operator} {property_value}
    '''

def execute_query(sitewise, query):
    params = {'queryStatement': query}
    headers = None
    row_data = []
    while True:
        response = sitewise.execute_query(**params)
        print('RequestId:', response['ResponseMetadata']['RequestId'])
        if not headers and 'columns' in response:
            headers = [h['name'] for h in response['columns']]
        for row in response['rows']:
            values = []
            for data in row['data']:
                k, v = list(data.items())[0]
                values.append('-' if k == 'nullValue' else v)
            row_data.append(values)
        if 'nextToken' not in response:
            break
        params['nextToken'] = response['nextToken']
        time.sleep(0.5)
    return headers, row_data


def run_query(sitewise, title, query):
    print(f'Use case: {title}')
    query_str = ' '.join(query.replace('\n', ' ').split())
    print(f'Query: {query_str}')
    print()
    headers, row_data = execute_query(sitewise, query)
    print()
    if headers:
        print(tabulate(row_data, headers=headers, tablefmt="presto"))
    else:
        print('No data returned')
    print()


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    models = db.table('models')
    assets = db.table('assets')
    generator_model = models.get(Model.type == 'generator')
    generator_assets = list(assets.search(Asset.type == 'generator'))

    sitewise = boto3.client('iotsitewise', region_name=config['region'])

    print('== Running SiteWise SQL queries ==')
    print()
    run_query(sitewise, 'All Assets', all_assets())
    run_query(sitewise, 'Search on specific UUID', assets_with_id(generator_assets[0]['id']))
    run_query(sitewise, 'List all Properties of an Asset', asset_properties(generator_assets[0]['id']))
    run_query(sitewise, 'Search on Asset name', assets_with_name('Site'))
    run_query(sitewise, 'Search on Property (display) name', assets_with_property('power'))
    run_query(sitewise, 'Get Property latest values', property_latest_values('temperature_f'))
    run_query(sitewise, 'Search on Property value (using prop name)', assets_with_property_double_value('temperature_f', '>', '90.0'))
    run_query(sitewise, 'Search on Property value (using UUIDs)', assets_with_property_double_value_using_uuids(
        generator_assets[1]['id'], generator_model['temp_meas_prop_id'], '<', '90.0'))


if __name__ == '__main__':
    main()
