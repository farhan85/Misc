#!/usr/bin/env bash

BASE_DIR='...'

for d in $(find $BASE_DIR -maxdepth 1 -type d); do
    cd $d
    git status 1>/dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        # $d is a git repo
        if [[ $(git status --porcelain  --untracked-files=no | wc -l) -gt 0 ]]; then
            echo "$d has changes"
        fi
    fi
done
