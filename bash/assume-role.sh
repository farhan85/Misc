#!/usr/bin/env bash

#ROLE_ARN="arn:aws:iam::$ACCOUNT:role/$ROLE_NAME"
ROLE_ARN="$@"

creds=$(aws sts assume-role --role-arn "$ROLE_ARN" \
                            --role-session-name "session-$(date +%s)" \
                            --query '[Credentials.AccessKeyId, Credentials.SecretAccessKey, Credentials.SessionToken]' \
                            --output text)

access_key_id=$(echo $creds | awk '{print $1}')
secret_access_key=$(echo $creds | awk '{print $2}')
session_token=$(echo $creds | awk '{print $3}')

init_cmds="
export AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION
export AWS_ACCESS_KEY_ID=$access_key_id
export AWS_SECRET_ACCESS_KEY=$secret_access_key
export AWS_SESSION_TOKEN=$session_token
"

# Start a bash shell with the creds pre loaded
bash --init-file <(echo "$init_cmds")
