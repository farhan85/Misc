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

debug='off'
filename='-'
while getopts ':df:h' OPT; do
    case "$OPT" in
        d)  debug='on'                               ;;
        f)  filename="$OPTARG"                       ;;
        h)  echo "$USAGE"                   ; exit   ;;
        ?)  echo "Invalid option: -$OPTARG" ; exit 1 ;;
        *)  echo "Internal error"           ; exit 2 ;;
    esac
done
shift $((OPTIND - 1))

# Process remaining non-option arguments.
for arg in "$@"; do
    echo "Positional arg: $arg"
done

echo "debug: $debug"
echo "filename: $filename"
