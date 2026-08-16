import socket
import threading

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(("127.0.0.1", 9999))

print("connected to server")

def receive_message():
    while True:
        data = client.recv(1024)

        if not data: 
            break

        print("Server said:", data.decode())

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

        client.send(message.encode())


client.close()