#!/usr/bin/env bash

# This script should be run from the control host (running AL2 EC2 hosts)
# and will run the ansible tasks to deploy the echo server to the webserver hosts

REGION_NAME=$(ec2-metadata --availability-zone | cut -d' ' -f2 | sed 's/[a-z]$//')
export AWS_DEFAULT_REGION=$REGION_NAME

BASE_DIR="$HOME/deploy"
VENV_DIR="$BASE_DIR/venv"
HOSTS_FILE="$BASE_DIR/hosts.txt"


echo "Installing dependencies"
#sudo yum install -y pssh  # for debugging
sudo yum install -y python3


echo "Installing Ansible"
python3 -m venv $VENV_DIR
$VENV_DIR/bin/pip install ansible
#$VENV_DIR/bin/ansible-galaxy install <collections...>


echo "Creating hosts file"
echo "[servers]" > $HOSTS_FILE

aws ec2 describe-instances \
        --filters 'Name=tag:Name,Values=webserver' \
                  'Name=instance-state-name,Values=running' \
        --query 'Reservations[*].Instances[*].PrivateIpAddress' \
        --output text \
        >> $HOSTS_FILE


echo "Running Ansible, updating hosts"
$VENV_DIR/bin/ansible-playbook --inventory-file $HOSTS_FILE playbook.yml
