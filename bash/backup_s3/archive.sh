#!/usr/bin/env bash

set -e

if [[ "$#" -ne 1 ]]; then
    echo "Error: Missing args"
    echo "Usage: $(basename $0) <archive filename>"
    echo "Will create the file <archive filename>.gz"
    exit 1
fi

ARCHIVE_FILE="$1"

[[ "$ARCHIVE_FILE" != *.tar.gz ]] && { echo 'Filename must end in .tar.gz'; exit 1; }

BACKUP_FILES=$(cat <<EOF
    $HOME/.zshrc
    $HOME/.vimrc
    $HOME/.vim
    $HOME/.gitconfig
    $HOME/.tmux.conf
    $HOME/Documents
EOF
)
BACKUP_FILES=$(echo "$BACKUP_FILES" | tr '\n' ' ' | tr -s ' ')

echo 'Archiving files'
tar --exclude='.git' \
    --exclude='venv' \
    --exclude='.eggs' \
    --exclude='.pytest_cache' \
    --exclude='__pycache__' \
    --exclude='*/build' \
    --gzip \
    -cf $ARCHIVE_FILE $BACKUP_FILES

gzip --list "$ARCHIVE_FILE"
