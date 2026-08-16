import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(("127.0.0.1", 9999))

print("connected to server")

# client.send(b"Hello world!")

while True:
    data = client.recv(1024)

    if not data: 
        break

    print("Server said:", data.decode())

    #client typs and send

    message = input("Client: ")
    client.send(message.encode())

client.close()