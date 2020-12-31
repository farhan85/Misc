#!/usr/bin/env bash

FILENAME=$(basename "${BASH_SOURCE[0]}")
CONTROL_HOST='...'

rsync --recursive --exclude "$FILENAME" . ec2-user@$CONTROL_HOST:/home/ec2-user/deploy
