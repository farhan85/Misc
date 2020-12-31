#!/usr/bin/env bash

FILENAME=$(basename "${BASH_SOURCE[0]}")
CONTROL_HOST='...'

rsync --recursive \
      --exclude "$FILENAME" \
      --exclude 'ansible_local.cfg' \
      --exclude 'ssh.cfg' \
      --exclude 'run_local.sh' \
      . ec2-user@$CONTROL_HOST:/home/ec2-user/deploy
