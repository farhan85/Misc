# Using GPG to manage AWS profile credentials

This tutorial will show how to use GPG to store AWS credentials locally for running
CLI commands, rather than leaving them in a plaintext file.

Tip: Temporary disable your shell history, since some commands will contain credentials/passphrases

```
# bash
set +o history

# zsh
setopt nohistchars
```

## Create GPG key

```
# v2.1.17+
gpg --full-generate-key

# Earlier versions
gpg --gen-key
```

- Kind of key: Choose (1) RSA and RSA (or Ed25519 if available)
- Keysize: Choose 4096 bits for maximum RSA security
- Validity: Choose an expiration date
   - For a non-production system, it might be fine to have it not expire
- Real Name & Email: This defines your User ID (UID)
   - When encrypting files, you can specify the recipient using the name or email
- Passphrase: Self-explanatory

Save the passphrase to a file, it will be used later for accessing your gpg key
```
echo 'your-passphrase' >  ~/.gpg_pass.txt
chmod 600 ~/.gpg_pass.txt
```

## Viewing keys

```
gpg --list-keys --keyid-format LONG
gpg --list-secret-keys --keyid-format LONG
gpg --fingerprint your-email@example.com
```

When you list keys, look for the line starting with _pub_. It will look something like this:
```
pub   rsa4096/1234567890ABCDEF 2025-12-31 [SC] [expires: 2027-12-31]
```

In this example, `1234567890ABCDEF` is the Key ID in Long format (last 16 chars of the key
fingerprint). The short format is 8 chars but now is considered unsafe for verifications.
It's too easy now to create fake keys with the same last 8 chars as a legit one.

## Exporting/importing keys

```
# Export keys to files
gpg --armor --export your-email@example.com > public-key.asc
gpg --armor --export-secret-keys your-email@example.com > private-key.asc

# Copy files to a new host
gpg --import public-key.asc
gpg --import private-key.asc

# Or import to remote host without creating intermediate files
gpg --export-secret-keys your-email@example.com | ssh user@host-b 'gpg --import'
```

## Deleting keys:
```
# Delete private key first
gpg --delete-secret-keys Key-ID-Or-Email
gpg --delete-keys Key-ID-Or-Email
```

## Encrypting files

```
cat << 'EOF' >> aws_creds.txt
export AWS_ACCESS_KEY_ID='AKIAIOSFODNN7EXAMPLE'
export AWS_SECRET_ACCESS_KEY='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
EOF

# Encrypt and create the file aws_creds.txt.gpg
gpg --encrypt --recipient your-email@example.com aws_creds.txt
rm aws_creds.txt
```

Loading the file in a bash script:
```
source <(gpg --decrypt --quiet --batch --passphrase-file /path/to/.gpg_pass.txt /path/to/aws_creds.txt.gpg)
```

It might be easier to define some aliases in your bashrc file:
```
alias gpgenc='gpg --encrypt --recipient your-email@example.com'
alias gpgdec='gpg --decrypt --recipient your-email@example.com --quiet --batch --passphrase-file /path/to/.gpg_pass.txt'
```

## Encrypting AWS profile file

Store creds in an encrypted json file:

```
cat << 'EOF' >> aws_creds.json
{
  "Version": 1,
  "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
  "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
EOF

gpg --encrypt --recipient your-email@example.com aws_creds.json
rm aws_creds.json
```

Update AWS config file so it decrypts to retrieve the creds. Note that you have to
give the absolute path to the files.

```
cat << 'EOF' >> ~/.aws/config
[profile secure-profile]
credential_process = gpg --decrypt --quiet --batch --passphrase-file /path/to/.gpg_pass.txt /path/to/aws_creds.json.gpg
EOF
```

Test using the encrypted creds via profile:

```
aws sts get-caller-identity --profile secure-profile

export AWS_PROFILE='secure-profile'
aws sts get-caller-identity
```
