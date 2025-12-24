#!/usr/bin/env python3

import boto3
import click
import time
from tinydb import TinyDB, Query


# Use Query objects to make ORM-style DB queries
Asset = Query()
Association = Query()


def split_into_groups(site_ids, generator_ids):
    min_group_size = int(len(generator_ids) / len(site_ids))
    extra = len(generator_ids) % len(site_ids)
    generator_idx_start = 0
    site_idx = 0
    while generator_idx_start < len(generator_ids):
        generator_idx_end = generator_idx_start + min_group_size
        if extra > 0:
            generator_idx_end += 1
            extra -= 1
        yield site_ids[site_idx], generator_ids[generator_idx_start:generator_idx_end]
        generator_idx_start = generator_idx_end
        site_idx += 1


def associate_assets(sitewise, associations_db, parent_asset, child_asset):
    association = {'parent_id': parent_asset['id'],
                   'hierarchy_id': parent_asset['hierarchy_id'],
                   'child_id': child_asset['id']}
    if not associations_db.contains(Association.fragment(association)):
        print(f"Associating Assets. {parent_asset['name']} -> {child_asset['name']}")
        sitewise.associate_assets(assetId=parent_asset['id'],
                                  hierarchyId=parent_asset['hierarchy_id'],
                                  childAssetId=child_asset['id'])
        associations_db.insert(association)
        time.sleep(0.5)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    assets = db.table('assets')
    associations = db.table('associations')
    prefix = config['resource_name_prefix']

    sitewise = boto3.client('iotsitewise', region_name=config['region'])

    factory_asset = assets.get(Asset.type == 'factory')
    site_assets = list(assets.search(Asset.type == 'site'))
    generator_assets = list(assets.search(Asset.type == 'generator'))

    for site in site_assets:
        associate_assets(sitewise, associations, factory_asset, site)
    for site, generators in split_into_groups(site_assets, generator_assets):
        for generator in generators:
            associate_assets(sitewise, associations, site, generator)


if __name__ == '__main__':
    main()
