#!/usr/bin/env python3

import boto3
import click
import time
from datetime import datetime
from tinydb import TinyDB, Query


# Use Query objects to make ORM-style DB queries
AnomalyDetection = Query()


def wait_for_bulk_import_complete(sitewise, import_job_id, import_job_name):
    print(f'Waiting for BulkImportJob {import_job_name} to complete...', end = '', flush=True)
    for _ in range(0, 120):
        state = sitewise.describe_bulk_import_job(jobId=import_job_id)['jobStatus']
        if state == 'COMPLETED':
            print('done')
            return
        print('.', end = '', flush=True)
        time.sleep(5)
    print('failed')
    raise Exception(f'Failed BulkImportJob {import_job_name} ({import_job_id}). Final state: {state}')


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    anomaly_detection = db.table('anomaly_detection')

    if anomaly_detection.get(AnomalyDetection.type == 'bulk_import_job') is None:
        generated_data = anomaly_detection.get(AnomalyDetection.type == 'generated_data')
        sitewise = boto3.client('iotsitewise', region_name=config['region'])

        response = sitewise.create_bulk_import_job(
            jobName=f'{config["resource_name_prefix"]}-BulkImport-{datetime.now().strftime("%Y%m%d_%H%M")}',
            jobRoleArn=config['bulk_import_role_arn'],
            files=[{
                'bucket': config['bucket_name'],
                'key': generated_data['historical_data_s3_prefix'],
            }],
            errorReportLocation={
                'bucket': config['bucket_name'],
                'prefix': generated_data['bulk_import_errors_s3_prefix'],
            },
            jobConfiguration={
                'fileFormat': {
                    'csv': {
                        'columnNames': ['ASSET_ID', 'PROPERTY_ID', 'DATA_TYPE', 'TIMESTAMP_SECONDS', 'VALUE']
                    }
                }
            },
            adaptiveIngestion=False,
            deleteFilesAfterImport=False
        )

        job_id = response['jobId']
        job_name = response['jobName']
        anomaly_detection.insert({
            'type': 'bulk_import_job',
            'id': job_id,
            'name': job_name
        })
        wait_for_bulk_import_complete(sitewise, job_id, job_name)


if __name__ == '__main__':
    main()
