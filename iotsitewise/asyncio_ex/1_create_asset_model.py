#!/usr/bin/env python3

import time

import boto3
import click
import pickledb


def wait_for_asset_model_active(sitewise, asset_model_id):
    print(f'Waiting for AssetModel to be created...', end = '', flush=True)
    for _ in range(12):
        response = sitewise.describe_asset_model(assetModelId=asset_model_id)
        state = response['assetModelStatus']['state']
        if state == 'ACTIVE':
            print('done')
            break
        time.sleep(1)
        print('.', end = '', flush=True)
    else:
        raise RuntimeError(f'AssetModel {asset_model_id} is not active. Current state: {state}')


def create_asset_model(sitewise, asset_model_name):
    response = sitewise.create_asset_model(assetModelName=asset_model_name)
    asset_model_id = response['assetModelId']
    wait_for_asset_model_active(sitewise, asset_model_id)
    return asset_model_id


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-n', '--asset-model-name', help='AssetModel name', required=True)
@click.option('-d', '--db-filename', help='DB file name', required=True)
def main(asset_model_name, db_filename):
    db = pickledb.load(db_filename, True)
    sitewise = boto3.client('iotsitewise')

    asset_model_id = create_asset_model(sitewise, asset_model_name)
    print(f'Created AssetModel {asset_model_id} {asset_model_name}')
    db.set('asset_model', {'id': asset_model_id, 'name': asset_model_name})


if __name__ == '__main__':
    main()
