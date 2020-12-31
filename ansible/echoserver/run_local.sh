#!/usr/bin/env bash

export AWS_DEFAULT_REGION=us-west-2

export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export AWS_SESSION_TOKEN=

export ANSIBLE_CONFIG='./ansible_local.cfg'

BASE_DIR='...'
VENV_DIR="$BASE_DIR/venv"
HOSTS_FILE="$BASE_DIR/hosts.txt"

echo "Installing Ansible"
python3 -m venv $VENV_DIR
$VENV_DIR/bin/pip install ansible
#$VENV_DIR/bin/ansible-galaxy install <collections...>

echo "Creating hosts file"
echo "[servers]" > $HOSTS_FILE

aws ec2 describe-instances \
        --filters 'Name=tag:Name,Values=test-stack-priv-inst' \
                  'Name=instance-state-name,Values=running' \
        --query 'Reservations[*].Instances[*].PrivateIpAddress' \
        --output text \
        >> $HOSTS_FILE

echo "Running ansible, updating hosts"
$VENV_DIR/bin/ansible-playbook --inventory-file $HOSTS_FILE playbook.yml
