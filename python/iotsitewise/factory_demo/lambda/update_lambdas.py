#!/usr/bin/env python3

import boto3
import click
import itertools
import jinja2
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from tinydb import TinyDB, Query


DIRECTORY = Path(__file__).parent.absolute()

# Use Query objects to make ORM-style DB queries
Model = Query()
Asset = Query()


def update_measurement_gen_lambda(lambda_client, models_db, assets_db, lambda_function_name, region):
    generator_model = models_db.get(Model.type == 'generator')
    generator_assets = list(assets_db.search(Asset.type == 'generator'))

    asset_ids = [a['id'] for a in generator_assets]
    prop_ids = [generator_model['power_meas_prop_id'], generator_model['temp_meas_prop_id']]

    templateLoader = jinja2.FileSystemLoader(searchpath=DIRECTORY)
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template('measurement_gen.py.jinja')
    meas_gen_code = template.render(asset_properties=itertools.product(asset_ids, prop_ids),
                                    region=region)

    memory_file = BytesIO()
    with ZipFile(memory_file, mode='w', compression=ZIP_DEFLATED) as zf:
        zf.writestr('index.py', meas_gen_code)

    lambda_client.update_function_code(FunctionName=lambda_function_name,
                                       ZipFile=memory_file.getvalue())
    print('Updated Measurement Generator Lambda function')


def update_cloudwatch_sender_lambda(lambda_client, lambda_function_name):
    memory_file = BytesIO()
    with ZipFile(memory_file, mode='w', compression=ZIP_DEFLATED) as zf:
        zf.write(f'{DIRECTORY}/cw_sender.py', arcname='index.py')

    lambda_client.update_function_code(FunctionName=lambda_function_name,
                                       ZipFile=memory_file.getvalue())
    print('Updated CloudWatch Sender Lambda function')


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    models = db.table('models')
    assets = db.table('assets')

    region = config['region']
    lambda_client = boto3.client('lambda', region_name=region)

    update_measurement_gen_lambda(lambda_client, models, assets, config['meas_gen_function_name'], region)
    update_cloudwatch_sender_lambda(lambda_client, config['cw_sender_function_name'])


if __name__ == '__main__':
    main()
