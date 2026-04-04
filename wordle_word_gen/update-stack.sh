#!/usr/bin/env bash

export AWS_ACCESS_KEY_ID='...'
export AWS_SECRET_ACCESS_KEY='...'
export AWS_DEFAULT_REGION='...'

stack_name='WordleStartWordGen'
#cfn_template='file://infra_signal.yaml'
cfn_template='file://infra_no_ec2.yaml'
script_name='gen_word.py'
words_file_url='https://gist.githubusercontent.com/dracos/dd0668f281e685bad51479e5acaadb93/raw/6bfa15d263d6d5b63840a8e5b64e04b382fdb079/valid-wordle-words.txt'
words_file_s3key='all_words.txt'

operation=''
while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--create-stack)
            operation='create-stack' ;;
        -u|--update-stack)
            operation='update-stack' ;;
        -e|--ec2-instance)
            operation='display-ec2-instance' ;;
        -w|--upload-word-file)
            operation='upload-word-file' ;;
        -d|--deploy-script)
            operation='deploy-script' ;;
        -l|--save-slack-params)
            operation='save-slack-params'
            slack_webhook="$2"
            shift ;;
        -s|--save-signal-params)
            operation='save-signal-params'
            signal_account="$2"
            signal_group_id="$3"
            shift 2 ;;
        -t|--save-telegram-params)
            operation='save-telegram-params'
            telegram_bot_token="$2"
            telegram_chat_id="$3"
            shift 2 ;;
    esac
    shift
done


if [[ "$operation" == "create-stack" ]]; then
    aws cloudformation create-stack \
        --stack-name $stack_name \
        --capabilities CAPABILITY_IAM \
        --template-body $cfn_template
    aws cloudformation wait stack-create-complete --stack-name $stack_name

elif [[ "$operation" == "update-stack" ]]; then
    aws cloudformation update-stack \
        --stack-name $stack_name \
        --capabilities CAPABILITY_IAM \
        --template-body $cfn_template
    aws cloudformation wait stack-update-complete --stack-name $stack_name

elif [[ "$operation" == "display-ec2-instance" ]]; then
    aws ec2 describe-instances \
        --filters 'Name=instance-state-name,Values=running' \
        --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value|[0], InstanceId, PublicIpAddress]' \
        --output table

    echo "Command to connect to instance: aws ec2-instance-connect ssh --instance-id <instance id>"

elif [[ "$operation" == "upload-word-file" ]]; then
    cfn_output=$(aws cloudformation describe-stacks --stack-name $stack_name --query 'Stacks[].Outputs' --output text 2>&1)
    data_bucket=$(echo "$cfn_output" | awk '/DataBucket/ {print $2}')
    curl -fSL "$words_file_url" | aws s3 cp - "s3://$data_bucket/$words_file_s3key"

elif [[ "$operation" == "deploy-script" ]]; then
    cfn_output=$(aws cloudformation describe-stacks --stack-name $stack_name --query 'Stacks[].Outputs' --output text 2>&1)
    function_name=$(echo "$cfn_output" | awk '/DailyThreadLambda/ {print $2}')

    zip function.zip gen_word.py
    aws lambda update-function-code --function-name $function_name --zip-file fileb://function.zip
    rm function.zip

elif [[ "$operation" == "save-slack-params" ]]; then
    aws ssm put-parameter --name /slack/webhook --value "$slack_webhook" --overwrite

elif [[ "$operation" == "save-signal-params" ]]; then
    aws ssm put-parameter --name /signal/account --value "$signal_account" --overwrite
    aws ssm put-parameter --name /signal/groupId --value "$signal_group_id" --overwrite

elif [[ "$operation" == "save-telegram-params" ]]; then
    aws ssm put-parameter --name /telegram/botToken --value "$telegram_bot_token" --overwrite
    aws ssm put-parameter --name /telegram/chatId --value "$telegram_chat_id" --overwrite

else
    echo "Error: Missing args"
    exit 1
fi
