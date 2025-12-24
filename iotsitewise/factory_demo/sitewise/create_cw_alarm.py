#!/usr/bin/env python3

import boto3
import click
import time
from datetime import datetime, timezone
from tinydb import TinyDB, Query


# Use Query objects to make ORM-style DB queries
Model = Query()
Asset = Query()


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    models = db.table('models')
    assets = db.table('assets')

    cw_client = boto3.client(service_name='cloudwatch', region_name=config['region'])

    factory_model = models.get(Model.type == 'factory')
    factory_asset = assets.get(Asset.type == 'factory')

    asset_id = factory_asset['id']
    property_id = factory_model['property_id']['power_rate']
    alarm_property_id = factory_model['composite_model_property_id']['power_rate_alarm']['AWS/ALARM_STATE']
    sns_arn = config['cw_alarm_sns_topic_arn']

    cw_client.put_metric_alarm(
        AlarmName='PowerRateAlarm',
        Namespace='IoTSiteWise/AssetMetrics',
        MetricName=f'Property_{property_id}',
        Dimensions=[
            { 'Name': 'AssetId', 'Value': asset_id  },
            { 'Name': 'Quality', 'Value': 'GOOD' }
        ],
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        Period=60,
        Statistic='Maximum',
        Threshold=4.0,
        ActionsEnabled=True,
        AlarmActions=[ sns_arn ],
        OKActions=[ sns_arn ],
        InsufficientDataActions=[ sns_arn ],
        Tags=[
            { 'Key': 'alarm_asset_id', 'Value': asset_id },
            { 'Key': 'alarm_property_id', 'Value': alarm_property_id },
        ],
    )
    print(f'Created CloudWatch alarm on Asset {asset_id} Property {property_id}')


if __name__ == '__main__':
    main()
