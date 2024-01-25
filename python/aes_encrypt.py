#!/usr/bin/env python3

import click
from base64 import b64encode, b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


def encrypt_aes_cbc(data, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data = pad(data, AES.block_size)
    ciphertext = cipher.encrypt(data)
    return ciphertext


def decrypt_aes_cbc(ciphertext, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data = cipher.decrypt(ciphertext)
    data = unpad(data, AES.block_size)
    return data


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-e', '--encrypt', is_flag=True, help='Encrypt the given input string')
@click.option('-d', '--decrypt', is_flag=True, help='Decrypt the given ciphertext')
@click.option('-s', '--input-string', '--input', help='String to encrypt (or base64 ciphertext to decrypt)', required=True)
@click.option('-k', '--key', help='AES key (base64). If not given, a new key will be generated for encryption')
@click.option('-i', '--initial-value', '--iv', help='AES initial value (base64). If not given, a new IV will be generated for encryption')
def main(encrypt, decrypt, input_string, key, initial_value):
    if not encrypt and not decrypt:
        raise click.UsageError('Must specify either --encrypt or --decrypt')

    if decrypt:
        if not initial_value or not key:
            raise click.UsageError('Must specify --key and --initial-value when decrypting')

    if encrypt:
        key_b = b64decode(key.encode('utf-8')) if key else get_random_bytes(16)
        iv_b = b64decode(initial_value.encode('utf-8')) if initial_value else get_random_bytes(16)
        data_b = input_string.encode('utf-8')

        ciphertext = encrypt_aes_cbc(data_b, key_b, iv_b)
        print(f"AES key:    {b64encode(key_b).decode('utf-8')}")
        print(f"iv:         {b64encode(iv_b).decode('utf-8')}")
        print(f"ciphertext: {b64encode(ciphertext).decode('utf-8')}")

    elif decrypt:
        data = decrypt_aes_cbc(b64decode(input_string.encode('utf-8')),
                               b64decode(key.encode('utf-8')),
                               b64decode(initial_value.encode('utf-8')))
        print(data.decode('utf-8'))


if __name__ == '__main__':
    main()
