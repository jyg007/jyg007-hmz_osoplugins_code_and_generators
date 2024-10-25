#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import base64

ALGORITHM = "AES"
KEY_SIZE = 32  # 256 bits
ITERATION_COUNT = 100000
TAG_LENGTH = 16  # 128 bits

def encrypt(plaintext, password):
    salt = os.urandom(16)
    key = derive_key_from_password(password, salt)

    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

    encoded_ciphertext = base64.b64encode(ciphertext).decode('utf-8')
    encoded_nonce = base64.b64encode(nonce).decode('utf-8')
    encoded_salt = base64.b64encode(salt).decode('utf-8')

    return f"{encoded_salt}:{encoded_nonce}:{encoded_ciphertext}"

def decrypt(ciphertext, password):
    parts = ciphertext.split(':')
    encoded_salt, encoded_nonce, encoded_ciphertext = parts

    ciphertext = base64.b64decode(encoded_ciphertext)
    nonce = base64.b64decode(encoded_nonce)
    salt = base64.b64decode(encoded_salt)

    key = derive_key_from_password(password, salt)

    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    return plaintext.decode('utf-8')

def derive_key_from_password(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATION_COUNT,
        backend=default_backend()
    )
    return kdf.derive(password.encode())
