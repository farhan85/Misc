#!/usr/bin/env bash

if [[ "$#" != 2 ]]; then
    echo >&2 "Missing args"
    echo >&2 "Usage: $(basename $0) <public RSA key file> <file to encrypt>"
    exit 2
fi

set -e

PUBLIC_KEY_FILE="$1"
PLAINTEXT_FILE="$2"

AES_KEY='key'
AES_KEY_ENC="${AES_KEY}.enc"
PLAINTEXT_FILE_ENC="${PLAINTEXT_FILE}.enc"
COMBINED_FILE="${PLAINTEXT_FILE_ENC}.tar"


# New random key to encrypt the plaintext file
openssl rand 192 -out $AES_KEY

# Encrypt the file with AES using the key
openssl enc -e -aes256 -in "$PLAINTEXT_FILE" -out "$PLAINTEXT_FILE_ENC" -pass "file:$AES_KEY"

# Encrypt the new key with the public RSA key
openssl rsautl -encrypt -in $AES_KEY -out $AES_KEY_ENC -pubin -inkey "$PUBLIC_KEY_FILE"

# Keep the encrypted key with the encrypted file
tar -cf $COMBINED_FILE "$PLAINTEXT_FILE_ENC" $AES_KEY_ENC

file_size=$(ls -lah $COMBINED_FILE | cut -d' ' -f5)
echo "File: $COMBINED_FILE, Size: $file_size"

# Cleanup
rm $AES_KEY $AES_KEY_ENC $PLAINTEXT_FILE_ENC
