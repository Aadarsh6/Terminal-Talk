import socket
import threading
import json
import time
import hashlib
import base64

from protocol import send_message, recv_message

HOST = "0.0.0.0"
PORT = 7000
TTL = 90  # seconds — peers refresh every 30s

peers = {}  # peer_id -> record
registry_lock = threading.Lock()


def prune_expired():
    now = time.time()
    for pid in [p for p, r in peers.items() if now - r["last_seen"] > TTL]:
        del peers[pid]
        print(f"[expiry] {pid} removed (stale > {TTL}s)")


def handle(conn, addr):
    try:
        data = recv_message(conn)
        if data is None:
            return

        try:
            request = json.loads(data.decode())
        except (UnicodeDecodeError, json.JSONDecodeError):
            send_message(conn, json.dumps({"status": "bad_request"}).encode())
            return

        rtype = request.get("type")

        if rtype == "register":
            peer_id = request.get("id")
            listen_port = request.get("listen_port")
            public_key_b64 = request.get("public_key")

            if not peer_id or not listen_port or not public_key_b64:
                send_message(conn, json.dumps({"status": "bad_request"}).encode())
                return

            fp = hashlib.sha256(base64.b64decode(public_key_b64)).hexdigest()
            fingerprint = ":".join(fp[i:i + 4] for i in range(0, len(fp), 4))

            with registry_lock:
                peers[peer_id] = {
                    "ip": addr[0],               # OBSERVED: who we see connecting
                    "listen_port": listen_port,  # ADVERTISED: where they accept P2P
                    "public_key": public_key_b64,
                    "fingerprint": fingerprint,
                    "last_seen": time.time(),
                }
            print(f"[register] {peer_id} {addr[0]}:{listen_port} fp={fingerprint[:19]}...")
            send_message(conn, json.dumps({"status": "registered", "ttl": TTL}).encode())

        elif rtype == "lookup":
            with registry_lock:
                prune_expired()
                rec = peers.get(request.get("id"))
            if rec:
                response = {
                    "status": "found",
                    "ip": rec["ip"],
                    "port": rec["listen_port"],
                    "fingerprint": rec["fingerprint"],
                }
            else:
                response = {"status": "not_found"}
            send_message(conn, json.dumps(response).encode())

        else:
            send_message(conn, json.dumps({"status": "unknown_type"}).encode())

    finally:
        conn.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # restart without TIME_WAIT errors
    server.bind((HOST, PORT))
    server.listen()
    print(f"Rendezvous server on {HOST}:{PORT} (TTL {TTL}s)")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()