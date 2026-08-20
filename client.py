import socket
import threading
import sys
import hashlib

from nacl.public import PublicKey, Box
from protocol import recv_message, send_message
from indentity import load_or_create_key

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(("127.0.0.1", 9999))

print("connected to server")

# !KEY EXCHANGE

# Generating clients key pair
client_private = load_or_create_key("client_key.bin")
client_public = client_private.public_key

# Client sends its public key first
send_message(client, bytes(client_public))

# Client receives server's public key
server_public_bytes = recv_message(client)

if server_public_bytes is None:
    print("Server disconnected during handshake")
    client.close()
    sys.exit()


# Convert bytes back into a PublicKey object
server_public = PublicKey(server_public_bytes)

# Create the Box
box = Box(client_private, server_public)

#* Creating fingerprint of server's public key

fingerprint = hashlib.sha256(server_public_bytes).hexdigest()

#* Group into 4 character chunks

fingerprint = ":".join(
    fingerprint[i:i + 4]
    for i in range(0, len(fingerprint), 4)
)
print("Server fingerprint: ", fingerprint)

confirmation = input(f"Fingerprint:{fingerprint} - confirm this matches (yes/no):"
)

if confirmation.lower() != "yes":
    print("Fingerprint not verified closing connection")
    client.close()
    sys.exit()

print("Secure connection established!")


# !RECEIVE THREAD

def receive_message():  
    while True:
        data = recv_message(client)    

        if data is None:
            print("Server disconnected")
            break

        #Decrypt encrypted bytes
        decrypted = box.decrypt(data)

        # convert pliantext bytes to string
        message = decrypted.decode()
        print("Server: ", message)


#! Creating the listening thread

thread = threading.Thread(
     target = receive_message,
     daemon = True
)

thread.start()

# Main thread handles typing and sending
while True:
        message = input("Client: ")

        if message == "quit":
            break

        # String -> bytes
        data = message.encode()

        # Encrypt bytes
        encrypted = box.encrypt(data)

        # Send encrypted bytes through framing
        send_message(client, encrypted)
        # print(encrypted)
        # print(data)


client.close()