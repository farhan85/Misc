import csv
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import boto3
import click
from botocore.exceptions import ClientError


CSV_FIELDS = ['resource', 'name', 'id', 'model_id']

thread_local = threading.local()
MAX_WORKERS = 8


def create_model_spec(name):
    return {
        'assetModelName': name,
        'assetModelDescription': 'Load test model',
        'assetModelProperties': [
            {
                'name': 'power',
                'dataType': 'DOUBLE',
                'unit': 'Watts',
                'type': {'measurement': {}}
            }
        ]
    }


def append_row(state_file, save_lock, row):
    with save_lock:
        with open(state_file, 'a', newline='') as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writerow(row)
            f.flush()
            os.fsync(f.fileno())


def read_state_file(filename):
    model = None
    assets = []
    with open(filename, newline='') as f:
        for row in csv.DictReader(f):
            if row['resource'] == 'model':
                model = {'id': row['id'], 'name': row['name']}
            else:
                assets.append(row)
    return model, assets


def get_client(client_factory):
    if not hasattr(thread_local, 'client'):
        thread_local.client = client_factory()
    return thread_local.client


def create_model(state_file, save_lock, client_factory, model_name):
    sitewise = get_client(client_factory)
    response = sitewise.create_asset_model(**create_model_spec(model_name))
    model_id = response['assetModelId']
    sitewise.get_waiter('asset_model_active').wait(assetModelId=model_id)
    row = {'resource': 'model', 'name': model_name, 'id': model_id, 'model_id': model_id}
    append_row(state_file, save_lock, row)
    print(f'Created AssetModel {model_name} {model_id}')
    return model_id


def create_assets(executor, client_factory, state_file, save_lock, model_id, asset_names):
    def create(name):
        sitewise = get_client(client_factory)
        response = sitewise.create_asset(assetModelId=model_id, assetName=name)
        asset_id = response['assetId']
        row = {'resource': 'asset', 'name': name, 'id': asset_id, 'model_id': model_id}
        append_row(state_file, save_lock, row)
        sitewise.get_waiter('asset_active').wait(assetId=asset_id)
        print(f'Created Asset {name} {asset_id}')

    futures = [executor.submit(create, name) for name in asset_names]
    for future in futures:
        future.result()


def delete_resources(executor, client_factory, model, assets):
    def delete_asset(asset):
        sitewise = get_client(client_factory)
        try:
            sitewise.delete_asset(assetId=asset['id'])
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        sitewise.get_waiter('asset_not_exists').wait(assetId=asset['id'])
        print(f"Deleted Asset {asset['name']} {asset['id']}")

    print('Deleting Assets')
    futures = [executor.submit(delete_asset, asset) for asset in assets]
    for future in futures:
        future.result()

    if model:
        sitewise = get_client(client_factory)
        try:
            sitewise.delete_asset_model(assetModelId=model['id'])
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise
        sitewise.get_waiter('asset_model_not_exists').wait(assetModelId=model['id'])
        print(f"Deleted AssetModel {model['name']} {model['id']}")


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-p', '--prefix', help='Resource name prefix')
@click.option('-n', '--num-assets', '--num', type=int, help='Number of assets to create')
@click.option('-f', '--state-file', required=True, help='CSV state file to append progress to and resume from')
@click.option('-d', '--delete', is_flag=True, help='Delete all assets and the model recorded in the state file')
@click.option('-r', '--region', help='Bifrost region', envvar='AWS_DEFAULT_REGION')
def main(prefix, num_assets, state_file, delete, region):
    client_factory = lambda: boto3.client('iotsitewise', region_name=region)

    if delete:
        if not os.path.exists(state_file):
            raise click.UsageError(f'State file {state_file} not exists')
        model, assets = read_state_file(state_file)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            delete_resources(executor, client_factory, model, assets)
        print('Deleted all assets')
        return

    if not prefix or not num_assets:
        raise click.UsageError('Missing --prefix and --num-assets')
    if not os.path.exists(state_file):
        with open(state_file, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()

    save_lock = threading.Lock()
    model, assets = read_state_file(state_file)
    created = {asset['name'] for asset in assets}
    all_names = {f'{prefix}-asset-{i}' for i in range(1, num_assets + 1)}
    pending = all_names - created
    print(f'Loaded {len(created)} assets from {state_file}')
    print(f'Remaining {len(pending)} assets to be created')

    if model:
        model_id = model['id']
    else:
        model_id = create_model(state_file, save_lock, client_factory, f'{prefix}-model')

    if pending:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            create_assets(executor, client_factory, state_file, save_lock, model_id, pending)
        print('Created all assets')


if __name__ == '__main__':
    main()
