#!/usr/bin/env python3

import click
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


def encrypt_aes_cbc(data):
    key = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(data, AES.block_size))
    return key, cipher.iv, ciphertext


def decrypt_aes_cbc(key, iv, ciphertext):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return data


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-e', '--encrypt', is_flag=True, help='Encrypt the string')
@click.option('-d', '--decrypt', is_flag=True, help='Decrypt the string')
@click.option('-s', '--input-string', '--input', help='String to encrypt (or base64 ciphertext)', required=True)
@click.option('-k', '--key', help='AES key (base64)')
@click.option('-i', '--initial-value', '--iv', help='AES initial value (base64)')
def main(encrypt, decrypt, input_string, key, initial_value):
    if not encrypt and not decrypt:
        raise click.UsageError('Must specify either --encrypt or --decrypt')

    if decrypt:
        if not initial_value or not key:
            raise click.UsageError('Must specify --key and --initial-value when decrypting')

    if encrypt:
        key, iv, ciphertext = encrypt_aes_cbc(input_string.encode('utf-8'))
        print(f"AES key:    {b64encode(key).decode('utf-8')}")
        print(f"iv:         {b64encode(iv).decode('utf-8')}")
        print(f"ciphertext: {b64encode(ciphertext).decode('utf-8')}")

    elif decrypt:
        data = decrypt_aes_cbc(b64decode(key.encode('utf-8')),
                               b64decode(initial_value.encode('utf-8')),
                               b64decode(input_string.encode('utf-8')))
        print(data.decode('utf-8'))


if __name__ == '__main__':
    main()
