#!/usr/bin/env python3

import time

import boto3
import click
import pickledb
from botocore.exceptions import ClientError


def wait_for_asset_model_deleted(sitewise, asset_model_id):
    print(f'Waiting for AssetModel to be deleted...', end = '', flush=True)
    for _ in range(12):
        try:
            sitewise.describe_asset_model(assetModelId=asset_model_id)
            time.sleep(1)
            print('.', end = '', flush=True)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print('done')
                break
            else:
                raise
    else:
        raise RuntimeError(f'AssetModel {asset_model_id} is not deleted')


def delete_asset_model(sitewise, asset_model):
    asset_model_id = asset_model['id']
    asset_model_name = asset_model['name']
    sitewise.delete_asset_model(assetModelId=asset_model_id)
    wait_for_asset_model_deleted(sitewise, asset_model_id)
    print(f'Deleted AssetModel {asset_model_id} {asset_model_name}')


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = pickledb.load(db_filename, True)
    if not db.exists('asset_model'):
        print('No asset_model entry found in DB')
        return

    sitewise = boto3.client('iotsitewise')

    asset_model = db.get('asset_model')
    delete_asset_model(sitewise, asset_model)
    db.rem('asset_model')


if __name__ == '__main__':
    main()
