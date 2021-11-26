#!/usr/bin/env python

import boto
import click


def wait_and_get(sqs_client, queue_url, wait_time_s=20):
    while True:
        response = sqs_client.receive_message(QueueUrl=queue_url, WaitTimeSeconds=wait_time_s)
        for message in response.get('Messages', []):
            sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])
            if message['Body'] == 'STOP':
                return
            yield message['Body']


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-q', '--queue-name', help='SQS queue name')
@click.option('-r', '--region-name', help='AWS region name')
def main(queue_name, region_name):
    sqs_client = boto3.client('sqs', region_name=region)
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    for message in wait_and_get(sqs_client, queue_url):
        print(message)
    print('Done')


if __name__ == '__main__':
    main()
