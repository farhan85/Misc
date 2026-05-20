
KEY_ID='...'

## Encryption

# Generate a data key from KMS
# This returns both a plaintext key and a ciphertext/encrypted key
aws kms generate-data-key \
    --key-id $KEY_ID \
    --key-spec "AES_256" \
    --output json > data_keys.json

# The plaintext key that will be used to encrypt the file
jq -r '.Plaintext' data_keys.json | base64 --decode > plaintext_key.bin

# The encrypted key that will be stored alongside the encrypted file
jq -r '.CiphertextBlob' data_keys.json | base64 --decode > encrypted_key.bin

# Encrypt the file with the plaintext key
openssl enc -aes-256-cbc -salt \
    -in "large_file.txt" \
    -out "large_file.txt.enc" \
    -pass file:./plaintext_key.bin

# Cleanup
rm -f plaintext_key.bin data_keys.json



## Decryption

# Decrypt the encrypted key
# No need to specify the KEY_ID because that info is already contained in the ciphertext blob
aws kms decrypt \
    --ciphertext-blob fileb://encrypted_key.bin \
    --output json > decrypted_key_response.json

# The plaintext key that will be used to decrypt the file
jq -r '.Plaintext' decrypted_key_response.json | base64 --decode > plaintext_key.bin

# Decrypt the file with the plaintext key
openssl enc -d -aes-256-cbc \
    -in "large_file.txt.enc" \
    -out "large_file_restored.txt" \
    -pass file:./plaintext_key.bin

# Cleanup
rm -f plaintext_key.bin decrypted_key_response.json

