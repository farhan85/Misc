#!/usr/bin/env bash

#ROLE_ARN="arn:aws:iam::$ACCOUNT:role/$ROLE_NAME"
ROLE_ARN="$@"

creds=$(aws sts assume-role --role-arn "$ROLE_ARN" \
                            --role-session-name "session-$(date +%s)" \
                            --query '[Credentials.AccessKeyId, Credentials.SecretAccessKey, Credentials.SessionToken]' \
                            --output text)

echo "export AWS_ACCESS_KEY_ID=$(echo "$creds" | cut -f1)"
echo "export AWS_SECRET_ACCESS_KEY=$(echo "$creds" | cut -f2)"
echo "export AWS_SESSION_TOKEN=$(echo "$creds" | cut -f3)"
