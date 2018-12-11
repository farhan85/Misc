#!/usr/bin/env bash

# Encrypting/Decrypting with openssl
#
# With symmetric key/pass
#   openssl enc -e -aes256 -in plaintext.txt -out encrypted.dat -pass "[pass|file|env]:password"
#   openssl enc -d -aes256 -in encrypted.dat -out decrypted.txt -pass "[pass|file|env]:password"
#
# With RSA key (small files)
#   openssl rsautl -encrypt -in plaintext.txt -out encrypted.dat -pubin -inkey ~/.ssh/backup_rsa.openssl.pub
#   openssl rsautl -decrypt -in encrypted.dat -out decrypted.txt -inkey ~/.ssh/backup_rsa.private
#
# With RSA key (large files)
#   openssl rand 192 -out key
#   openssl enc -e -aes256 -in plaintext.txt -out encrypted.dat -pass file:key
#   openssl rsautl -encrypt -in key -out key.enc -pubin -inkey ~/.ssh/backup_rsa.openssl.pub
#   tar -zcvf encrypted.tar.gz encrypted.dat key.enc

# Example crontab
# 0 1 * * * { ${HOME}/bin/create-backup.sh }


OPENSSL="/.../openssl"

PUBKEY="${HOME}/.ssh/backup_rsa.openssl.pub"

# Working directory
WDIR="${HOME}/tmp"

function log() {
    echo "$(date +"%F %T") -- $@"
}

function cleanup() {
    set +e

    log "Cleaning up files"
    cd $WDIR

    rm -f backup-daily* backup-weekly* backup-monthly* key key.enc

    # Display the running of this script before exiting
    times
}
trap cleanup EXIT

function filesize() {
    fname="$1"
    fsize=$(ls -lah $fname | cut -d' ' -f5)
    log "File: $fname, Size: $fsize"
}


# Files and directories to backup
read -r -d '' filesToArchive<<EOF
    ${HOME}/.zshrc
    ${HOME}/.zsh_plugins
    ${HOME}/.vimrc
    ${HOME}/.vim
    ${HOME}/.gitconfig
    ${HOME}/.tmux.conf
    ${HOME}/bin
    ${HOME}/Documents
    ${HOME}/ws/*/src
EOF
filesToArchive=$(echo "$filesToArchive" | tr '\n' ' ' | tr -s ' ')

# Backup type
dayOfMonth=$(date +%d)
dayOfWeek=$(date +%u)
extraPrefix=''
if [ "${dayOfMonth}" = "02" ]; then
    # I'm not going to delete monthy backups anymore.
    # Organise these so that they are easier to sort/find
    year=$(date +%Y)
    extraPrefix="$year/"
    backupType="monthly"

elif [ "${dayOfWeek}" = "7" ]; then # Sunday
    backupType='weekly'

else
    backupType='daily'

fi

# Backup the files
cd $WDIR

set -e

# Setup the different filenames
dateStr=$(date +\%EY-\%m-\%d)
backupName="backup-${backupType}-${dateStr}"
backupTarFile="${backupName}.tar"
backupGzipFile="${backupTarFile}.gz"
backupEncFile="${backupGzipFile}.enc"
# This backup file contains the encrypted backup file along with
# its corresponding encrypted key
backupFile="${backupName}.tar"

log "Archiving files"
tar -cf $backupTarFile $filesToArchive
filesize $backupTarFile

log "Compressing files"
gzip --force $backupTarFile
filesize $backupGzipFile

log "Encrypting files"
# New random key to encrypt the backups
$OPENSSL rand 192 -out key
# Encrypt the backups with the new key
$OPENSSL enc -e -aes256 -in $backupGzipFile -out $backupEncFile -pass file:key
# Encrypt the new key with my public RSA key
$OPENSSL rsautl -encrypt -in key -out key.enc -pubin -inkey $PUBKEY
# Keep the key with the encrypted archive
tar -cf "$backupFile" $backupEncFile key.enc
filesize $backupFile

# TODO: Upload the backup file to S3 or somewhere
