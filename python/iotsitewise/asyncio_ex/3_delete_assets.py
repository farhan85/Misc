#!/usr/bin/env python3

import asyncio
import functools
from datetime import datetime, timezone

import asyncclick as aclick
import boto3
import click
import pickledb
from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from limits import RateLimitItemPerSecond
from limits.aio import storage, strategies


ratelimiter = strategies.MovingWindowRateLimiter(storage.MemoryStorage())


async def async_throttle(tps_limit):
    while not await ratelimiter.hit(tps_limit):
        window = await ratelimiter.get_window_stats(tps_limit)
        await asyncio.sleep(window.reset_time - int(datetime.now(timezone.utc).timestamp()))


async def wait_for_asset_deleted(tps_limit, sitewise, asset, db):
    asset_id = asset['id']
    asset_name = asset['name']
    for _ in range(12):
        try:
            await async_throttle(tps_limit)
            print(f"Got bandwidth. Checking Asset {asset_id} status")
            await sitewise.describe_asset(assetId=asset_id)
            await asyncio.sleep(5)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f'Deleted asset {asset_id} {asset_name}')
                db.lremvalue('assets', asset)
                break
            else:
                raise
    else:
        raise Exception(f'Asset {asset_id} {asset_name} is not deleted')


async def delete_asset(tps_limit, sitewise, asset):
    asset_id = asset['id']
    asset_name = asset['name']
    await async_throttle(tps_limit)
    print(f'Got bandwidth. Sending delete request for {asset_id} {asset_name}')
    await sitewise.delete_asset(assetId=asset_id)


async def delete_all_assets(sitewise, db):
    assets = db.lgetall('assets')
    delete_tps_limit = RateLimitItemPerSecond(2)
    describe_tps_limit = RateLimitItemPerSecond(3)

    print('Sending delete requests')
    tasks = [
        asyncio.ensure_future(delete_asset(delete_tps_limit, sitewise, asset))
        for asset in assets]
    await asyncio.gather(*tasks)

    print('Waiting for all assets to be deleted')
    tasks = [
        asyncio.ensure_future(wait_for_asset_deleted(describe_tps_limit, sitewise, asset, db))
        for asset in assets]
    await asyncio.gather(*tasks)


#
# I've implemented this differently so that I have some reference code on
# using the botocore async libs
#
@aclick.command(context_settings={'help_option_names': ['-h', '--help']})
@aclick.option('-d', '--db-filename', help='DB file name', required=True)
async def main(db_filename):
    db = pickledb.load(db_filename, True)
    if not db.exists('assets'):
        print('No assets entry found in DB')
        return

    session = get_session()
    async with session.create_client('iotsitewise') as sitewise:
        await delete_all_assets(sitewise, db)


if __name__ == '__main__':
    main()
