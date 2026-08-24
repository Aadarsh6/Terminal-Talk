import socket
import threading
import json

from protocol import send_message, recv_message


HOST = "127.0.0.1"
PORT = 9999

peers = {}

def handle_peer(client, address):
    print("Peer connected", address)

    try:
        data = recv_message(client)

        if data is None:
            return

        request = json.loads(data.decode())

        if request["type"] == "register":
            peer_id = request["id"]

            peers[peer_id] = address
            print(f"Registered {peer_id} --> {address}")
            response = {
                "status": "registered"
            }

            send_message(
                client, 
                json.dumps(response).encode()
            )
        elif request["type"] == "lookup":
            peer_id = request["id"]

            if peer_id in peers:
                ip, port = peers[peer_id]
                response = {
                    "status" : "found",
                    "ip" : ip,
                    "port": port
                }

                print(f"Lookup {peer_id} --> {address}")

            else:
                response = {
                    "status": "not_found"
                }

            send_message(
                client,
                json.dumps(response).encode()
            )

    finally:
        client.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((HOST, PORT))
server.listen()

print(f"Rendezvous server listening on {HOST}:{PORT}")

while True:
    client, address = server.accept()

    thread = threading.Thread(
        target = handle_peer,
        args = (client, address),
        daemon = True
    )

    thread.start()