#!/usr/bin/env python

import boto3
import botocore.exceptions
import click


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-b', '--bucket', help='Bucket name', required=True)
@click.option('-d', '--delete', help='Delete bucket after emptying it', is_flag=True)
def main(bucket, delete):
    """
    Empties an S3 bucket and deletes the bucket if specified.
    """

    s3_bucket = boto3.resource('s3').Bucket(bucket)

    try:
        print(f"Deleting all object versions in bucket '{bucket}'")
        s3_bucket.object_versions.delete()

        if delete:
            print('Deleting bucket')
            s3_bucket.delete()

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print("Bucket already deleted")
        else:
            raise


if __name__ == '__main__':
    main()
