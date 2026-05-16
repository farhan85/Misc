#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
NAME=$(basename $0)
read -r -d '' USAGE << EOF
Usage: $NAME [-d|--debug] [-f|--file <filename>] [-h|--help] ARG1 ARG2 ...

Options:
    -d, --debug  Enable debugging
    -f, --file   Input filename
    -h, --help   Displays this help
EOF

options=$(getopt -o df:h -l debug,file:,help -n "$NAME" -- "$@") || exit
eval set -- "$options"

debug='off'
filename='-'
while true; do
    case "$1" in
        -d|--debug) debug='on'    ; shift   ;;
        -f|--file)  filename="$2" ; shift 2 ;;
        -h|--help)  echo "$USAGE" ; exit    ;;
        --)         shift         ; break   ;;
    esac
done

# Process remaining non-option arguments.
for arg in "$@"; do
    echo "Positional arg: $arg"
done

echo "debug: $debug"
echo "filename: $filename"
