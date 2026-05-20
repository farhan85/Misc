#!/usr/bin/env bash

S3_BUCKET='...'
S3_BACKUP_KEY_PREFIX='backups'
RSA_PUBLIC_KEY='...'
RSA_PRIVATE_KEY='...'

operation=
s3_file_uri=
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -e) operation='encrypt' ;;
        -d) operation='decrypt' ;;
        -s) s3_file_uri="$2" ; shift ;;
        -h) echo "Args: [-d] [-e] [-s <s3 uri>]"
            echo
            echo "-d  Retrieve backup from S3 and decrypt"
            echo "-e  Create backup, encrypt and upload to S3"
            echo "-s  S3 URI of backup file to retrieve/decrypt"
            echo "-h  Display this help"
            exit 0 ;;
    esac
    shift
done

if [[ "$operation" == "encrypt" ]]; then
    YEAR=$(date +%Y)
    MONTH=$(date +%m)
    DAY=$(date +%d)
    S3_LOCATION="s3://${S3_BUCKET}/${S3_BACKUP_KEY_PREFIX}/${YEAR}/${MONTH}/${DAY}"
    ARCHIVE_FILE="/tmp/backup-${YEAR}-${MONTH}-${DAY}.tar.gz"

    ./archive.sh $ARCHIVE_FILE
    ./encrypt.sh $ARCHIVE_FILE $RSA_PUBLIC_KEY $S3_LOCATION
    rm $ARCHIVE_FILE

    # Better alternative: use GnuPG to create an encrypted .gpg file.
    # It already handles the logic of envelope encryption with RSA/AES keys
    # gpg --encrypt --recipient your-email@example.com "$ARCHIVE_FILE"

elif [[ "$operation" == "decrypt" ]]; then
    [[ -z "$s3_file_uri" ]] && { echo "Missing S3 URI"; exit 1; }

    ./decrypt.sh "$s3_file_uri" $RSA_PRIVATE_KEY

    # Better alternative: use GnuPG to manage encrypted .gpg files
    # aws s3 cp s3://... $ARCHIVE_FILE_ENC
    # gpg --decrypt --recipient your-email@example.com "$ARCHIVE_FILE_ENC"
fi
