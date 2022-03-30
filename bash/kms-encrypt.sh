
RSA_KEY_ID='...'
AES_KEY_ID='...'

# Encrypt/Decrypt text

aws kms encrypt --key-id $RSA_KEY_ID --encryption-algorithm RSAES_OAEP_SHA_256 \
    --plaintext 'example string' \
    --query CiphertextBlob --output text \
| base64 --decode \
> rsa_example.enc

aws kms decrypt --key-id $RSA_KEY_ID --encryption-algorithm RSAES_OAEP_SHA_256 \
    --ciphertext-blob fileb://rsa_example.enc \
    --query Plaintext --output text \
| base64 --decode


# Encrypt/Decrypt files

aws kms encrypt --key-id $AES_KEY_ID --encryption-algorithm SYMMETRIC_DEFAULT \
    --plaintext fileb://testfile.txt \
    --query CiphertextBlob --output text \
| base64 --decode \
> testfile.txt.enc

aws kms decrypt --key-id $AES_KEY_ID --encryption-algorithm SYMMETRIC_DEFAULT \
    --ciphertext-blob fileb://testfile.txt.enc \
    --query Plaintext --output text \
| base64 --decode \
> decrypted_testfile.txt
