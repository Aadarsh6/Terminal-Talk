import os

from nacl.public import PrivateKey

def load_or_create_key(filename):
    if os.path.exists(filename):
        with open(filename, "rb") as file:
            key_bytes = file.read()

        return PrivateKey(key_bytes)

    privateKey = PrivateKey.generate() 

    with open(filename, "wb") as file:
        file.write(bytes(privateKey))

    return privateKey