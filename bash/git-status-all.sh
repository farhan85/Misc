#!/usr/bin/env bash

programName=$(echo $0 | sed "s;^.*/;;")

read -r -d '' usage << EOF
Usage: $programName [-h] [-d <directory>]

Scans through the given directory of git repos, and prints out which ones have
any changes.

Options:
    -d   The directory to search in (default: current working directory)
    -h   Displays this help
EOF

BASE_DIR=$(pwd)
while getopts ':d:h' OPT; do
    case "$OPT" in
        d)  BASE_DIR="$OPTARG" ;;
        h)  echo "$usage"
            exit 0
            ;;
        v)  verbose='true' ;;
        ?)  echo "Invalid option given: $OPTARG"
            exit 1
            ;;
        *)  echo "Internal error"
            exit 1
            ;;
    esac
done
shift $((OPTIND - 1))

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
