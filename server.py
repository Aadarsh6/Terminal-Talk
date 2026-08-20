import socket
import threading
import sys
import hashlib

from nacl.public import PrivateKey, PublicKey, Box
from protocol import recv_message, send_message
from indentity import load_or_create_key
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("127.0.0.1", 9999))
server.listen()

print("Server is waiting for a connection...")

client, address = server.accept() # wont continue unless client connect to it


print("Client address:", address)

# !Key change 

#Generate server key pair
server_private = load_or_create_key("server_key.bin")
server_public = server_private.public_key

#?Server receives client private key first before client get server public key
client_public_bytes = recv_message(client)

if client_public_bytes is None:
    print("Client disconnected during public private handshake")
    client.close()
    server.close()
    sys.exit()

# Convert bytes back into a PublicKey object
client_public = PublicKey(client_public_bytes)

#* server send ist public key

send_message(client, bytes(server_public))

#The box

box = Box(server_private, client_public)

# !Creating fingerprint of clients public key
fingerprint = hashlib.sha256(client_public_bytes).hexdigest()

# Group into 4 character chunks

fingerprint = ":".join(
    fingerprint[i:i + 4]
    for i in range(0, len(fingerprint), 4)
)
print("Client fingerprint: ", fingerprint)

confirmation = input(
    f"Fingerprint: {fingerprint} - Confirm this matches (yes/no): "
)

if confirmation.lower() != "yes":

    print("Fingerprint not verified closing the connection.")
    client.close()
    server.close()
    sys.exit()


print("Secure connection established!")




def receive_message():
    while True:
        data = recv_message(client)

        if data is None:
            print("Client disconnected")
            break
        #decrypt encrypted bytes
        decrypt = box.decrypt(data)

        # Convert plaintext bytes to string
        message = decrypt.decode() #? 4. decode the message you get before printing
        print("Client:", message)

#Create listening thread
thread = threading.Thread(
    target=receive_message,
    daemon=True
)

thread.start()



#? main thread for handling typing ans sending


while True:
    message = input("Server: ") #? 1. Take the message
    if message == "quit":
        break

    #string to bytes
    data = message.encode() #? 2. Encode the message

    #Encrypt the bytes
    encrypted = box.encrypt(data)


    # Send encrypted bytes through framing
    send_message(client, encrypted) #? 3. Send the encoded message/data
    # print(encrypted)
    # print(data)

client.close()
server.close()