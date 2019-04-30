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




function is-git-repo() {
    git status 1>/dev/null 2>&1
}

function is-up-to-date() {
    # Run the command that lists which files have been modified
    if [[ $(git status --porcelain  --untracked-files=no | wc -l) -gt 0 ]]; then
        return 1
    fi
    return 0
}

function is-master-behind-origin() {
    # Get commit IDs to check if they are the same
    head_commit=$(git rev-parse master)
    origin_latest_commit=$(git rev-parse origin/master)
    if [[ "$head_commit" != "$origin_latest_commit" ]]; then
        return 1
    fi
    return 0
}

for d in $(find $BASE_DIR -maxdepth 1 -type d); do
    cd $d
    is-git-repo
    if [[ $? -eq 0 ]]; then
        is-up-to-date
        if [[ $? -ne 0 ]]; then
            echo "$(basename $d) has changes"
        fi

        is-master-behind-origin
        if [[ $? -ne 0 ]]; then
            echo "$(basename $d) master branch is not up to date"
        fi
    fi
done
