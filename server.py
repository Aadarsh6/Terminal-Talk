import socket
import threading
import sys
import hashlib

from nacl.public import PrivateKey, PublicKey, Box
from nacl.secret import SecretBox
from protocol import recv_message, send_message
from identity import load_or_create_key, load_or_create_secret_key
from storage import init_db, save_message, load_messages

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #!OS-side route lookup only
# !It's only a clever way to ask the operating system:
# !"Which network interface/IP would you use to reach this outside address?"
    try:
        # *8.8.8.8 is Google's public DNS server.

        s.connect(("8.8.8.8", 80))  # UDP "connect": no packet sent, OS just picks a route  
        ip = s.getsockname()[0]     #getsockname() asks: "What local address is this socket using?"
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", PORT))  # all interfaces — other machines can reach us now
server.listen()

# load key early so we can show our own fingerprint before anyone connects
server_private = load_or_create_key("server_key.bin")
server_public = server_private.public_key

own_fp = hashlib.sha256(bytes(server_public)).hexdigest()
own_fp = ":".join(own_fp[i:i + 4] for i in range(0, len(own_fp), 4))
print("Your fingerprint:", own_fp)

print(f"Server listening on 0.0.0.0:{PORT}")
print(f"Other machine connects with: python client.py {get_lan_ip()} {PORT}")

client, address = server.accept()

print("Client address:", address)


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

if confirmation.lower() not in ( "yes", "y"):

    print("Fingerprint not verified closing the connection.")
    client.close()
    server.close()
    sys.exit()

#local database encryption
storage_key = load_or_create_secret_key(
    "server_storage_key.bin"
    )
Secret_box = SecretBox(storage_key)


db_filename = "server_history.db"

init_db(db_filename)

messages = load_messages(db_filename, fingerprint, Secret_box)

for direction, text, timestamp in messages:
    if direction == "sent":
        print(f"You: {text}")
    else:
        print(f"Them: {text}")

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
        save_message(
            db_filename,
            fingerprint,
            "received",
            message,
            Secret_box
        )
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

    save_message(
        db_filename,
        fingerprint,
        "sent",
        message,
        Secret_box
    )


client.close()
server.close()