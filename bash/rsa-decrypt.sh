#!/usr/bin/env bash

if [[ "$#" != 2 ]]; then
    echo >&2 "Missing args"
    echo >&2 "Usage: $(basename $0) <private RSA key file> <tar file>"
    echo >&2
    echo >&2 "The tar file is expected to have only two files:"
    echo >&2 " - The encrypted AES key (named key.enc)"
    echo >&2 " - The encrypted file (named with .enc extension)"
    exit 2
fi

set -e

PRIVATE_KEY_FILE="$1"
COMBINED_FILE="$2"

AES_KEY='key'
AES_KEY_ENC="${AES_KEY}.enc"

# Get the name of the encrypted file
ENCRYPTED_FILE=$(tar -tf "$COMBINED_FILE" | grep -v $AES_KEY_ENC)
PLAINTEXT_FILE=$(basename $ENCRYPTED_FILE '.enc')


# Extract encrypted files
tar -xf "$COMBINED_FILE"

# Decrypt AES key
openssl rsautl -decrypt -in $AES_KEY_ENC -out $AES_KEY -inkey "$PRIVATE_KEY_FILE"

# Decrypt the encrypted file with the AES key
openssl enc -d -aes256 -in "$ENCRYPTED_FILE" -out $PLAINTEXT_FILE -pass "file:$AES_KEY"

# Cleanup
rm $AES_KEY $AES_KEY_ENC $ENCRYPTED_FILE
