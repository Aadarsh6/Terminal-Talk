import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("127.0.0.1", 9999))
server.listen()

print("Server is waiting for a connection...")


#! "I won't continue until somebody connects to me.
client, address = server.accept()

print("Client address:", address)

while True:
    message = input("Server: ")
    client.send(message.encode())
    data = client.recv(1024)

    if not data:
        break

    print("Client:", data.decode())

# data = client.recv(1024)
# print("Client connected!")

# print("Client said:", data.decode())

# client.send(b"Hello from server!")


client.close()
server.close()