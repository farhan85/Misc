#!/usr/bin/env python3

import asyncio
import functools
from datetime import datetime, timezone

import boto3
import click
import pickledb
from limits import RateLimitItemPerSecond
from limits.aio import storage, strategies


ratelimiter = strategies.MovingWindowRateLimiter(storage.MemoryStorage())


async def async_call(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))


async def async_throttle(tps_limit):
    while not await ratelimiter.hit(tps_limit):
        window = await ratelimiter.get_window_stats(tps_limit)
        await asyncio.sleep(window.reset_time - int(datetime.now(timezone.utc).timestamp()))


async def wait_for_asset_active(tps_limit, sitewise, asset_id):
    for _ in range(12):
        await async_throttle(tps_limit)
        print(f"Got bandwidth. Checking Asset {asset_id} status")
        response = await async_call(sitewise.describe_asset, assetId=asset_id)
        state = response['assetStatus']['state']
        if state == 'ACTIVE':
            print(f'Asset {asset_id} {response["assetName"]} is active')
            break
        await asyncio.sleep(5)
    else:
        raise RuntimeError(f'Asset {asset_id} is not active. Current state: {state}')


async def create_asset(tps_limit, sitewise, asset_model_id, asset_name, db):
    await async_throttle(tps_limit)
    print(f'Got bandwidth. Creating asset {asset_name}')
    response = await async_call(sitewise.create_asset, assetModelId=asset_model_id, assetName=asset_name)
    asset_id = response['assetId']
    db.ladd('assets', {'id': asset_id, 'name': asset_name})
    print(f'Created asset {asset_name} with id {asset_id}')
    return asset_id


async def create_all_assets(sitewise, asset_model_id, asset_name_prefix, num_assets, db):
    create_tps_limit = RateLimitItemPerSecond(2)
    describe_tps_limit = RateLimitItemPerSecond(3)

    print('Waiting for all assets to be created')
    tasks = [
        asyncio.ensure_future(create_asset(create_tps_limit, sitewise, asset_model_id, f'{asset_name_prefix}-{i}', db))
        for i in range(1, num_assets + 1)
    ]
    asset_ids = await asyncio.gather(*tasks)

    print('Waiting for all assets to be active')
    tasks = [
        asyncio.ensure_future(wait_for_asset_active(describe_tps_limit, sitewise, id))
        for id in asset_ids
    ]
    await asyncio.gather(*tasks)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-p', '--asset-name-prefix', help='Asset name prefix', required=True)
@click.option('-n', '--num-assets', help='Number of Assets to create', type=int, required=True)
@click.option('-d', '--db-filename', help='DB file name', required=True)
def main(asset_name_prefix, num_assets, db_filename):
    db = pickledb.load(db_filename, True)
    if not db.exists('assets'):
        db.lcreate('assets')

    sitewise = boto3.client('iotsitewise')
    asset_model_id = db.get('asset_model')['id']

    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_all_assets(sitewise, asset_model_id, asset_name_prefix, num_assets, db))
    loop.close()


if __name__ == '__main__':
    main()
