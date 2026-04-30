#!/usr/bin/env bash

[[ -z "$AWS_ACCESS_KEY_ID" ]] && { echo "Missing AWS creds"; exit 1; }

stack_name='SiteWiseMeasurementGen'
asset_property_s3_key='asset_property_ids.csv'

cfn_output=$(aws cloudformation describe-stacks --stack-name $stack_name --query 'Stacks[].Outputs' --output text 2>&1)
if [[ "$cfn_output" == *"does not exist"* ]]; then
    echo 'Creating base resources CFN stack'
    aws cloudformation create-stack \
        --stack-name $stack_name \
        --template-body 'file://infra.yaml' \
        --capabilities CAPABILITY_IAM \
        --parameters ParameterKey=AssetPropertyIdS3Key,ParameterValue="$asset_property_s3_key"

    aws cloudformation wait stack-create-complete --stack-name $stack_name
    cfn_output=$(aws cloudformation describe-stacks --stack-name $stack_name --query 'Stacks[].Outputs' --output text)
else
    echo 'Base resources CFN stack already created'
fi


meas_gen_function_name=$(echo "$cfn_output" | awk '/MeasurementGenLambdaName/ {print $2}')
meas_gen_invoker_rule=$(echo "$cfn_output" | awk '/MeasurementGenInvokerRuleName/ {print $2}')
bucket_name=$(echo "$cfn_output" | awk '/BucketName/ {print $2}')

package_file='lambda-package.zip'
zip $package_file gen_measurement.py
aws lambda update-function-code --function-name $meas_gen_function_name --zip-file "fileb://$package_file" > /dev/null
echo 'Uploaded MeasurementGenerator to Lambda'
rm $package_file

echo 'Create your AssetModels and Assets, if not done already and write the'
echo 'assetId/propertyId pairs to a CSV file (with a header row) and upload to S3:'
echo 'Note the Lambda will only generate double values for the asset properties'
echo "> aws s3 cp <asset property IDs file> s3://$bucket_name/$asset_property_s3_key"

echo 'And now start the measurement generator, by enabling the AWS Events Rule'
echo 'which will run the Lambda function every minute.'
echo 'Initial values will be generated automatically on the first run.'
echo "> aws events enable-rule --name $meas_gen_invoker_rule"

