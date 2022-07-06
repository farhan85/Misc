#!/usr/bin/env bash

read -r -d '' USAGE << EOF
Encrypt/Decrypt a file

Usage: $(basename $0)  [-h] [-d|-e] -i <filename> -o <filename> -p <passphrase>

Options:
    -d  Decrypt the file
    -e  Encrypt the file
    -i  Input filename
    -p  Passphrase
    -o  Output filename
    -h  Displays this help
EOF

operation=
input_filename=
output_filename=
passphrase=
while getopts ':dehi:o:p:' OPT; do
    case "$OPT" in
        d)  operation='decrypt' ;;
        e)  operation='encrypt' ;;
        i)  input_filename="$OPTARG" ;;
        o)  output_filename="$OPTARG" ;;
        p)  passphrase="$OPTARG" ;;
        h)  echo "$USAGE" ; exit 0 ;;
        ?)  echo "Invalid option: -$OPTARG" ; exit 2 ;;
        *)  echo "Internal error" ; exit 2 ;;
    esac
done
shift $((OPTIND - 1))

if [[ -z "$operation" || -z "$input_filename" || -z "$output_filename" || -z "$passphrase" ]]; then
    echo -e "Missing args\n\n$USAGE"
    exit 1
fi

if [[ "$input_filename" == "$output_filename" ]]; then
    echo "Input and output filename should be different"
    exit 1
fi


if [[ "$operation" == "decrypt" ]]; then
    openssl enc -d -base64 -aes-256-cbc \
        -in "$input_filename" \
        -out "$output_filename" \
        -k "$passphrase"
fi

if [[ "$operation" == "encrypt" ]]; then
    openssl enc -base64 -aes-256-cbc \
        -in "$input_filename" \
        -out "$output_filename" \
        -k "$passphrase"
fi

