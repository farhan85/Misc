#!/usr/bin/env python3

import boto3
import datetime
import json
from json import JSONEncoder


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()


if __name__ == '__main__':
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name="/aws/service/ami-amazon-linux-latest/al2023-ami-minimal-kernel-default-x86_64")

    try:
        print(json.dumps(response))
    except TypeError:
        print('Could not convert to json with default parameters. Response contains datetime value')
        pass

    print()
    print(json.dumps(response, cls=DateTimeEncoder))

    print()
    print(json.dumps(response, default=str))
