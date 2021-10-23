import boto3
import botocore
import datetime
from locust import User, events, task, constant_throughput


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument('--aws-region', env_var='AWS_REGION', default='us-east-1', help='AWS region name')
    parser.add_argument('--queue-name', help='SQS queue name', required=True)


class BotoClientWrapper:
    def __init__(self, client, request_event):
        self.client = client
        self.request_event = request_event

    def __getattr__(self, api_name):
        func = getattr(self.client, api_name)

        def wrapper(*args, **kwargs):
            start_time = datetime.datetime.now()
            request_meta = {
                'request_type': 'API',
                'name': api_name,
                'start_time': start_time,
                'context': {},
                'exception': None,
                'response': None,
                'response_length': 0,
            }
            try:
                response = func(*args, **kwargs)
                request_meta['response'] = response
                request_meta['response_length'] = len(response)
            except botocore.exceptions.ClientError as error:
                request_meta['exception'] = error
            elapsed = datetime.datetime.now() - start_time
            request_meta['response_time'] = int(elapsed.total_seconds()*1000)
            self.request_event.fire(**request_meta)
            return request_meta['response']

        return wrapper


class SqsTester(User):
    wait_time = constant_throughput(2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        region = self.environment.parsed_options.aws_region
        client = boto3.client('sqs', region_name=region)
        request_event = self.environment.events.request
        self.client = BotoClientWrapper(client, request_event)
        queue_name = self.environment.parsed_options.queue_name
        self.queue_url = client.get_queue_url(QueueName=queue_name)['QueueUrl']

    @task
    def send_message(self):
        self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=f'Test message - {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
