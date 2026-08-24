import socket
import json

from protocol import send_message, recv_message

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.connect(("127.0.0.1", 9999))

print("Connected to Rendezvous server")

#Register ourself

register_request = {
    "type": "register",
    "id": "aadarsh"
}

send_message(
    server,
    json.dumps(register_request).encode()
)

response = recv_message(server)

print("Register response:", json.loads(response.decode()))
server.close()

# Look up peer that is not registered


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.connect(("127.0.0.1", 9999))

print("Connected to Rendezvous server for lookup")



lookup_request = {
    "type": "lookup",
    "id": "aadarsh"
}

send_message(
    server,
    json.dumps(lookup_request).encode()
)

response = recv_message(server)


print("Lookup response:", json.loads(response.decode()))


server.close()

