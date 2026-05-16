# Uploading backups to AWS S3

These scripts are for uploading daily backups to an S3 bucket.

Each encrypted archive file will have a corresponding encrypted AES key which will be uploaded
to the same location in S3:
```
S3_BUCKET/
  S3_BACKUP_KEY_PREFIX/
    YEAR/
      MONTH/
        DAY/
          backup-YEAR-MONTH-DAY.tar.gz.enc
          key.bin.enc
```

## Summary

When creating a backup, the scripts will:
 - tar/gz the files to be backed up
 - Encrypt the archive using a randomly generated AES key
 - Encrypt the AES key using the provided RSA public key
 - Uploads the encrypted archive and AES key to S3

When retrieving a backup, the scripts will:
 - Download the specified encrypted archive file (and the corresponding key stored alongside it)
 - Decrypt the AES key using the provided RSA private key
 - Decrypt the encrypted archive using the AES key

## Usage

Prerequisites:
 - Update the constants in `manage_backup.sh`:
     - `S3_BUCKET`/`S3_BACKUP_KEY_PREFIX`: The S3 destination for all backups
     - `RSA_PUBLIC_KEY`/`RSA_PRIVATE_KEY`: The RSA keys to use when encrypting/decrypting the AES key
 - Update `archive.sh` to specify which files should be in the backup
 - Environment variables are set up with AWS credentials
 - The `AWS_DEFAULT_REGION` environment variable is set


Creating a new backup file:
```
./manage_backup.sh -e
```

Retrieving a backup file
```
./manage_backup.sh -d -s s3://bucketname/backups/2026/05/15/backup-2026-05-15.tar.gz.enc
```
