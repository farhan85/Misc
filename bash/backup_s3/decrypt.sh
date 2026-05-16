#!/usr/bin/env bash

set -e

if [[ "$#" -ne 2 ]]; then
    echo "Error: Missing args"
    echo "Usage: $(basename $0) <enc filename S3 URI> <private RSA key file>"
    exit 1
fi

ENC_FILE_S3_URI="$1"
RSA_PRIV_KEY="$2"

S3_PREFIX=$(dirname "$ENC_FILE_S3_URI")
ENC_FILE=$(basename "$ENC_FILE_S3_URI")
# Remove .enc suffix
OUTPUT_FILE="${ENC_FILE%.enc}"

AES_KEY='key.bin'
ENC_AES_KEY='key.bin.enc'
ENC_AES_KEY_S3_URI="${S3_PREFIX}/${ENC_AES_KEY}"

echo 'Downloading encrypted files from S3'
aws s3 cp "$ENC_FILE_S3_URI" "$ENC_FILE"
aws s3 cp "$ENC_AES_KEY_S3_URI" "$ENC_AES_KEY"

echo 'Decrypting AES key with RSA Private Key'
openssl pkeyutl -decrypt -inkey "$RSA_PRIV_KEY" -in "$ENC_AES_KEY" -out "$AES_KEY"

echo 'Decrypting file with AES key'
openssl enc -d -aes-256-cbc -salt -pbkdf2 -in "$ENC_FILE" -out "$OUTPUT_FILE" -pass "file:$AES_KEY"

echo 'Cleaning up temp files'
rm -f "$ENC_FILE"
rm -f "$ENC_AES_KEY"
rm -f "$AES_KEY"
