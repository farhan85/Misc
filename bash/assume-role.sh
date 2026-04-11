#!/usr/bin/env bash

#ROLE_ARN="arn:aws:iam::$ACCOUNT:role/$ROLE_NAME"
ROLE_ARN="$@"

INIT_CMDS=$(cat <<EOF
update-creds() {
    NEW_CREDS=\$(aws sts assume-role \
        --role-arn "$ROLE_ARN" \
        --role-session-name "session-\$(date +%s)" \
        --query '[Credentials.AccessKeyId, Credentials.SecretAccessKey, Credentials.SessionToken]' \
        --output text)
    if [ \$? -eq 0 ]; then
        export AWS_ACCESS_KEY_ID=\$(echo \$NEW_CREDS | awk '{print \$1}')
        export AWS_SECRET_ACCESS_KEY=\$(echo \$NEW_CREDS | awk '{print \$2}')
        export AWS_SESSION_TOKEN=\$(echo \$NEW_CREDS | awk '{print \$3}')
        echo "Updated credentials for $ROLE_ARN"
    else
        echo "Failed to load credentials."
    fi
}

# Load creds on startup
update-creds
PS1='\[\e[33m\]assumed-role \[\e[m\]\w > '
EOF
)

bash --init-file <(echo "$INIT_CMDS") -i
