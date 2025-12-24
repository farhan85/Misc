import argparse
import csv
import random
from datetime import datetime, timezone

import boto3


def load_asset_property_ids(filename):
    # Expected file format: row contents: <asset ID>,<property ID>
    with open(filename, 'r') as f:
        return [(row[0], row[1]) for row in csv.reader(file)]


def chunks(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]


def send_values(sitewise, asset_property_values, dt_now):
    timestamp = int(dt_now.timestamp())
    entries = [
        {
            'entryId': str(i),
            'assetId': asset_id,
            'propertyId': property_id,
            'propertyValues': [{
                'value': { 'doubleValue': value },
                'timestamp': { 'timeInSeconds': timestamp }
            }]
        }
        for i, (asset_id, property_id, value) in enumerate(asset_property_values)
    ]

    for batch in chunks(entries, 10):
        print('Sending batch to Sitewise:')
        for entry in batch:
            print(entry)
        response = sitewise.batch_put_asset_property_value(entries=batch)
        print('Response:', response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', required=True, help='CSV file with assetId/propertyId pairs')
    args = parser.parse_args()

    sitewise = boto3.client('iotsitewise')

    asset_properties = load_asset_property_ids(args.filename)
    if asset_properties:
        dt_now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        init_values = [(asset_id, property_id, random.uniform(10, 100))
                       for asset_id, property_id in asset_properties]
        send_values(sitewise, init_values, dt_now)


if __name__ == '__main__':
    main()
