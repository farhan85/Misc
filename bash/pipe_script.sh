#!/usr/bin/env bash

# An example of a script where you can pipe output into this script

if [[ "$#" -eq 1 ]]; then
    input=$(cat "$1")

elif [[ "$#" -eq 0 ]]; then
    input=$(</dev/stdin)

fi

echo "$input"
