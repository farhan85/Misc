## Introduction

Sets up an AWS Lambda Function to run every minute and generate random measurement data for
IoT SiteWise Asset Properties.

This package contains the following files:
- `create_stack.sh`: Helper script to set up the infra and deploy the Lambda function
- `gen_init_values.py`: Generates initial values for the Asset Properties
- `gen_measurement.py`: Lambda function to generate new random measurement values every minute
- `infra.yaml`: Creates the infrastructure to run the Lambda function every minute


## Requirements

The only Python library needed to install is Boto3

```
python -m pip install boto3
```

## Building the resources

```
# Ensure your CLI environment has the required AWS environment variables
> echo $AWS_ACCESS_KEY_ID
> echo $AWS_DEFAULT_REGION

# Create the CloudFormation stack
> ./create_stack.sh
```

The output of that script summarizes the commands to run, that is explained in the remainder of
this README file.

The CloudFormation stack will create resources needed to run the Lambda function periodically.
Take note of these two resources that are created, you will need to reference them later.
- Amazon EventBridge Rule for invoking the Lambda function every minute
- S3 Bucket for storing the input file, a list of (assetID,propertyID) pairs

These resources can be obtained from the CloudFormation stack's output (they will also be
displayed in the `create_stack.sh` output)

```
> aws cloudformation describe-stacks --stack-name <stack name> --query 'Stacks[].Outputs' --output table
```

Once you have created all your IoT SiteWise Assets, create a csv file that contains the pairs
of Asset ID and Measurement Property IDs that is used as input to the two Python scripts

```
# Store the asset and property IDs in a csv file
> cat asset_property_ids.csv
12345678-90ab-cdef-1234-abcdef111111,12345678-90ab-cdef-1234-abcdef222222
12345678-90ab-cdef-1234-abcdef333333,12345678-90ab-cdef-1234-abcdef444444
...
```

Upload this file to the S3 bucket, as it will be used as input for the Lambda function. The
S3 bucket can be obtained from the CloudFormation output, and the S3 key is defined in the
`create_stack.sh` script.

```
> aws s3 cp asset_property_ids.csv s3://<S3 bucket>/asset_property_ids.csv
```

Now you need to set initial values for all the asset properties. Run the following script to
generate these values and send them to IoT SiteWise.

```
> python ./gen_init_values.py -f asset_property_ids.csv
```

Now you can start the measurement data generator to generate random values for all the asset
properties every minute.

```
> aws events enable-rule --name <Amazon EventBridge Rule>
```
