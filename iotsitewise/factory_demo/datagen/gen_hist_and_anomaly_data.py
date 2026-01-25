import boto3
import click
import csv
import math
import os
import random
from datetime import datetime, timedelta, timezone
from tinydb import TinyDB, Query


# Use Query objects to make ORM-style DB queries
Model = Query()
Asset = Query()
AnomalyDetection = Query()

ANOMALY_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'


def generate_data(timestamps, mean, stdev, anomaly_offset, num_anomalies, anomaly_range):
    values = [random.gauss(mean, stdev) for _ in timestamps]

    anomalies = []
    anomaly_positions = random.sample(range(anomaly_range, len(timestamps)-anomaly_range), num_anomalies)
    for pos in anomaly_positions:
        for i in range(anomaly_range):
            values[pos + i] += anomaly_offset
        anomalies.append((
            timestamps[pos].strftime(ANOMALY_DATE_FORMAT),
            timestamps[pos + anomaly_range - 1].strftime(ANOMALY_DATE_FORMAT)
        ))

    return list(zip(timestamps, values)), anomalies


def write_data(data_entries, historial_data_filename, anomaly_data_filename):
    with open(historial_data_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        for entry in data_entries:
            for ts, val in entry['historical_values']:
                writer.writerow([entry['asset_id'], entry['property_id'], 'DOUBLE', int(ts.timestamp()), val])
    print(f'Written historical data to file: {historial_data_filename}')

    with open(anomaly_data_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        for entry in data_entries:
            for anomaly in entry['anomalies']:
                writer.writerow(anomaly)
    print(f'Written anomaly labels to file: {anomaly_data_filename}')


def days_to_minutes(days):
    minutes_per_day = 1440
    return days * minutes_per_day


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-d', '--db', '--db-filename', help='DB file name', required=True)
def main(db_filename):
    db = TinyDB(db_filename)
    config = db.table('config').get(doc_id=1)
    models = db.table('models')
    assets = db.table('assets')
    anomaly_detection = db.table('anomaly_detection')

    if anomaly_detection.get(AnomalyDetection.type == 'generated_data') is None:
        model = models.get(Model.type == 'generator')
        asset = assets.get((Asset.type == 'generator') & (Asset.faulty == True))
        prop_ids = [model['property_id'][prop_name] for prop_name in ['power', 'temperature_f']]

        num_points = days_to_minutes(14)
        start_time = datetime.now(timezone.utc).replace(second=0, microsecond=0) \
                        - timedelta(minutes=num_points)
        timestamps = [start_time + timedelta(minutes=i) for i in range(num_points)]

        timestamp_s = datetime.now().strftime('%Y%m%d_%H%M')
        gen_data_file = f'historical_data_{timestamp_s}.csv'
        anomaly_file = f'anomaly_labels_{timestamp_s}.dat'

        data_entries = []
        num_anomalies = 5
        anomaly_range = 10
        mean = 10
        stdev = 1
        anomaly_offset = 20
        for i, prop_id in enumerate(prop_ids, 1):
            hist_data, anomalies = generate_data(timestamps, mean, stdev, anomaly_offset, num_anomalies, anomaly_range)
            data_entries.append({
                'asset_id': asset['id'],
                'property_id': prop_id,
                'historical_values': hist_data,
                'anomalies': anomalies
            })

        write_data(data_entries, gen_data_file, anomaly_file)

        s3_client = boto3.client('s3', region_name=config['region'])
        bucket_name = config['bucket_name']
        bulk_import_prefix = 'bulk_import'
        historical_data_prefix = f'{bulk_import_prefix}/{gen_data_file}'
        anomaly_labels_prefix = f'anomaly_detection/{anomaly_file}'
        s3_client.upload_file(gen_data_file, bucket_name, historical_data_prefix)
        s3_client.upload_file(anomaly_file, bucket_name, anomaly_labels_prefix)
        os.remove(gen_data_file)
        os.remove(anomaly_file)

        anomaly_detection.insert({
            'type': 'generated_data',
            'mean': mean,
            'stdev': stdev,
            'anomaly_offset': anomaly_offset,
            'historical_data_s3_prefix': historical_data_prefix,
            'anomalies_s3_prefix': anomaly_labels_prefix,
            'start_time_epoch': int(timestamps[0].timestamp()),
            'end_time_epoch': int(timestamps[-1].timestamp()),
            'bulk_import_errors_s3_prefix': f'{bulk_import_prefix}/errors/',
        })


if __name__ == '__main__':
    main()

