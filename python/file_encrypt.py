#!/usr/bin/env python3

import click
import os
import struct
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes


CHUNK_SIZE = 64 * 1024


def read_from_file(filename):
    with open(filename) as f:
        return f.read()


def rsa_encrypt(public_key_s, data):
    public_key = RSA.importKey(public_key_s)
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data)


def rsa_decrypt(private_key_s, data):
    private_key = RSA.importKey(private_key_s)
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(data)


def encrypt_file_aes_cbc(input_filename, output_filename, key_encrypter):
    key = get_random_bytes(16)
    encrypted_key = key_encrypter(key)
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


def decrypt_file_aes_cbc(input_filename, output_filename, key_decrypter):
    with open(input_filename, 'rb') as input_file, open(output_filename, 'wb') as output_file:
        int_len = struct.calcsize('Q')
        filesize = struct.unpack('<Q', input_file.read(int_len))[0]
        enc_key_len = struct.unpack('<Q', input_file.read(int_len))[0]
        enc_key = input_file.read(enc_key_len)
        iv = input_file.read(16)

        key = key_decrypter(enc_key)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        while True:
            chunk = input_file.read(CHUNK_SIZE)
            if len(chunk) == 0:
                break
            output_file.write(cipher.decrypt(chunk))
        output_file.truncate(filesize)


@click.command(context_settings={'help_option_names': ['-h', '--help']})
@click.option('-e', '--encrypt', is_flag=True, help='Encrypt the input file')
@click.option('-d', '--decrypt', is_flag=True, help='Decrypt the input file')
@click.option('-b', '--rsa-public-key-file', help='RSA public key file')
@click.option('-v', '--rsa-private-key-file', help='RSA private key file')
@click.option('-f', '--input-file', '--file', help='File to encrypt', required=True)
@click.option('-o', '--output', help='Output filename')
def main(encrypt, decrypt, rsa_public_key_file, rsa_private_key_file, input_file, output):
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

    if encrypt and rsa_public_key_file is None:
        raise click.UsageError('Must specify --rsa-public-key-file when encrypting')

    if decrypt and rsa_private_key_file is None:
        raise click.UsageError('Must specify --rsa-private-key-file when decrypting')

    if encrypt:
        output = output or f'{input_file}.enc'
        public_key = read_from_file(rsa_public_key_file)
        encrypt_file_aes_cbc(input_file, output, lambda k: rsa_encrypt(public_key, k))
    elif decrypt:
        output = output or os.path.splitext(input_file)[0]
        private_key = read_from_file(rsa_private_key_file)
        decrypt_file_aes_cbc(input_file, output, lambda k: rsa_decrypt(private_key, k))


if __name__ == '__main__':
    main()
