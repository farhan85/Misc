#!/usr/bin/env python3

import argparse
import boto3
import time


def run_athena_query(query, database, s3_output):
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': s3_output}
    )
    execution_id = response['QueryExecutionId']

    while True:
        status = athena.get_query_execution(QueryExecutionId=execution_id)['QueryExecution']['Status']
        if status['State'] in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(2)
    if status['State'] != 'SUCCEEDED':
        raise Exception(f"Query failed: {status.get('StateChangeReason')}")

    results = []
    column_names = []

    paginator = athena.get_paginator('get_query_results')
    page_iterator = paginator.paginate(QueryExecutionId=execution_id)
    for page_num, page in enumerate(page_iterator):
        if page_num == 0:
            column_info = page['ResultSet']['ResultSetMetadata']['ColumnInfo']
            column_names = [col['Name'] for col in column_info]

        for row in page['ResultSet']['Rows']:
            row_data = [val.get('VarCharValue', None) for val in row['Data']]
            # Apparently we still need to check for this
            if row_data == column_names:
                continue
            results.append(dict(zip(column_names, row_data)))

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run an Athena query')
    parser.add_argument('--s3-output', required=True, help='S3 output bucket URI (e.g. s3://my-bucket/temp/)')
    args = parser.parse_args()

    athena = boto3.client('athena')

    DATABASE = 'raw_data_db'
    QUERY = 'SELECT * FROM orders'

    results = run_athena_query(QUERY, DATABASE, args.s3_output)

    print(f"Total rows retrieved: {len(results)}")
    for record in results[:5]:
        print(record)
