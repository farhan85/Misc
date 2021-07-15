#!/usr/bin/env python3

import click
import os
import struct
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes


CHUNK_SIZE = 64 * 1024


def rsa_encrypt(public_key_filename, data):
    with open(public_key_filename) as f:
        public_key = RSA.importKey(f.read())
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data)


def rsa_decrypt(private_key_filename, data):
    with open(private_key_filename) as f:
        private_key = RSA.importKey(f.read())
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(data)


def encrypt_file_aes_cbc(input_filename, output_filename, key_encryptor):
    key = get_random_bytes(16)
    encrypted_key = key_encryptor(key)
    filesize = os.path.getsize(input_filename)
    cipher = AES.new(key, AES.MODE_CBC)
    with open(input_filename, 'rb') as input_file, open(output_filename, 'wb') as output_file:
        output_file.write(struct.pack('<Q', filesize))
        output_file.write(struct.pack('<Q', len(encrypted_key)))
        output_file.write(encrypted_key)
        output_file.write(cipher.iv)
        while True:
            chunk = input_file.read(CHUNK_SIZE)
            if len(chunk) == 0:
                break
            if len(chunk) % 16 != 0:
                chunk += b' ' * (16 - (len(chunk) % 16))
            output_file.write(cipher.encrypt(chunk))


def decrypt_file_aes_cbc(input_filename, output_filename, key_decryptor):
    with open(input_filename, 'rb') as input_file:
        int_len = struct.calcsize('Q')
        filesize = struct.unpack('<Q', input_file.read(int_len))[0]
        enc_key_len = struct.unpack('<Q', input_file.read(int_len))[0]
        enc_key = input_file.read(enc_key_len)
        iv = input_file.read(16)

        key = key_decryptor(enc_key)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        with open(output_filename, 'wb') as output_file:
            while True:
                chunk = input_file.read(CHUNK_SIZE)
                if len(chunk) == 0:
                    break
                output_file.write(cipher.decrypt(chunk))
            output_file.truncate(filesize)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-e', '--encrypt', is_flag=True, help='Encrypt the input file')
@click.option('-d', '--decrypt', is_flag=True, help='Decrypt the input file')
@click.option('-b', '--rsa-public-key', help='RSA public key file')
@click.option('-v', '--rsa-private-key', help='RSA private key file')
@click.option('-f', '--filename', '--file', help='File to encrypt', required=True)
@click.option('-o', '--output', help='Output filename')
def main(encrypt, decrypt, rsa_public_key, rsa_private_key, filename, output):
    """
    Encrypts a given file, storing the relevent keys in the same binary file, and can decrypt
    the file as well.

    This script will generate a one-time AES key to encrypt the file. A public RSA key must
    be provided which is used to encrypt the AES key. The encrypted AES key is appended to
    the encrypted file.

    When decrypting, the corresponding private RSA key must be provided, and this script will
    extract the AES key from the encrypted file and decrypt it.

    If no output filename is given, the encrypted file will be named "<input filename>.enc"
    and when decrypting, the input filename with its last extension (e.g. .enc) stripped off
    is used as the name of the output file.
    """

    if not encrypt and not decrypt:
        raise click.UsageError('Must specify either --encrypt or --decrypt')

    if encrypt and rsa_public_key is None:
        raise click.UsageError('Must specify --rsa-public-key when encrypting')

    if decrypt and rsa_private_key is None:
        raise click.UsageError('Must specify --rsa-private-key when decrypting')

    if encrypt:
        output = output or f'{filename}.enc'
        encrypt_file_aes_cbc(filename, output, lambda k: rsa_encrypt(rsa_public_key, k))
    elif decrypt:
        output = output or os.path.splitext(filename)[0]
        decrypt_file_aes_cbc(filename, output, lambda k: rsa_decrypt(rsa_private_key, k))


if __name__ == '__main__':
    main()
