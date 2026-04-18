#!/usr/bin/env bash

USAGE="Usage:
$0 [-h] [--start|--stop]"

state=
while [[ $# -gt 0 ]]; do
    case "$1" in
        --start)    state='ENABLED'  ;;
        --stop)     state='DISABLED' ;;
        -h|--help)  echo "$USAGE" ; exit 0 ;;
    esac
    shift
done

[[ -z "$AWS_ACCESS_KEY_ID" ]] && { echo "Missing AWS creds"; exit 1; }
[[ -z "$AWS_DEFAULT_REGION" ]] && { echo "Missing AWS region"; exit 1; }
[[ -z "$state" ]] && { printf "Missing scheduler state\n$USAGE\n"; exit 1; }


STACK_NAME='WordleStartWordGen'

SCHEDULE_NAME=$(aws cloudformation describe-stacks \
                    --stack-name $STACK_NAME \
                    --query 'Stacks[0].Outputs[?OutputKey==`DailyThreadScheduleName`].OutputValue' \
                    --output text)

CURRENT_CONFIG=$(aws scheduler get-schedule --name "$SCHEDULE_NAME")

aws scheduler update-schedule \
    --name "$SCHEDULE_NAME" \
    --state $state \
    --schedule-expression "$(echo "$CURRENT_CONFIG" | jq -r .ScheduleExpression)" \
    --schedule-expression-timezone "$(echo "$CURRENT_CONFIG" | jq -r .ScheduleExpressionTimezone)" \
    --flexible-time-window "$(echo "$CURRENT_CONFIG" | jq '{Mode: .FlexibleTimeWindow.Mode}')" \
    --target "$(echo "$CURRENT_CONFIG" | jq '{Arn: .Target.Arn, RoleArn: .Target.RoleArn}')"
