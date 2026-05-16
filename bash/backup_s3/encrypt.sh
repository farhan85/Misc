#!/usr/bin/env bash

set -e

if [[ "$#" -ne 3 ]]; then
    echo "Error: Missing args"
    echo "Usage: $(basename $0) <file to encrypt> <public RSA key file> <S3 prefix URI>"
    exit 1
fi

INPUT_FILE="$1"
RSA_PUB_KEY="$2"
S3_PREFIX="$3"

# Strip trailing slash
S3_PREFIX="${S3_PREFIX%/}"

AES_KEY='key.bin'
ENC_AES_KEY="key.bin.enc"
INPUT_FILE_BASENAME=$(basename "$INPUT_FILE")
ENC_OUTPUT_FILE="${INPUT_FILE_BASENAME}.enc"

echo 'Generating 256-bit symmetric AES key'
openssl rand 32 > "$AES_KEY"

echo 'Encrypting file with AES key'
openssl enc -aes-256-cbc -salt -pbkdf2 -in "$INPUT_FILE" -out "$ENC_OUTPUT_FILE" -pass "file:$AES_KEY"

echo 'Encrypting AES key with RSA Public Key'
openssl pkeyutl -encrypt -pubin -inkey "$RSA_PUB_KEY" -in "$AES_KEY" -out "$ENC_AES_KEY"

echo 'Uploading encrypted files to S3'
aws s3 cp "$ENC_OUTPUT_FILE" "${S3_PREFIX}/${ENC_OUTPUT_FILE}"
aws s3 cp "$ENC_AES_KEY" "${S3_PREFIX}/${ENC_AES_KEY}" --metadata "backup-file=$ENC_OUTPUT_FILE"

echo 'Cleaning up temp files'
rm -f "$AES_KEY"
rm -f "$ENC_AES_KEY"
rm -f "$ENC_OUTPUT_FILE"
