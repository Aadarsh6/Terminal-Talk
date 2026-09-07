import socket
import threading
import sys
import hashlib
from nacl.public import PublicKey, Box
from nacl.secret import SecretBox
from protocol import recv_message, send_message
from identity import load_or_create_key, load_or_create_secret_key
from storage import init_db, save_message, load_messages

host = sys.argv[1] if len(sys.argv) > 1 else"127.0.0.1"
port = int(sys.argv[0]) if len(sys.argv) > 2 else 9999

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

print(f"Connected to server at ${host}:${port}")



# !KEY EXCHANGE

# Generating clients key pair
client_private = load_or_create_key("client_key.bin")
client_public = client_private.public_key

own_fp = hashlib.sha256(bytes(client_public)).hexdigest()
own_fp = ":".join(own_fp[i:i + 4] for i in range(0, len(own_fp), 4))
print("Your fingerprint:", own_fp)


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

#local database encryption
storage_key = load_or_create_secret_key(
    "client_storage_key.bin"
    )
Secret_box = SecretBox(storage_key)

db_filename = "client_history.db"

init_db(db_filename)

messages = load_messages(db_filename, fingerprint, Secret_box)
for direction, text, timestamp in messages:
    if direction == "sent":
        print(f"You: {text}")
    else:
        print(f"Them: {text}")


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
        save_message(
            db_filename,
            fingerprint,
            "received",
            message, 
            Secret_box
        )
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
        save_message(
            db_filename,
            fingerprint,
            "sent",
            message,
            Secret_box
        )

client.close()