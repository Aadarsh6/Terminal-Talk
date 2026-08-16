import socket
import threading


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("127.0.0.1", 9999))
server.listen()

print("Server is waiting for a connection...")


#! "I won't continue until somebody connects to me.
client, address = server.accept()

print("Client address:", address)


def receive_message():
    while True:
        data = client.recv(1024)

        if not data:
            break

        print("Client:", data.decode())

#Create listening thread
thread = threading.Thread(
    target=receive_message,
    daemon=True
)

thread.start()



#main thread for handling typing ans sending


while True:
    message = input("Server: ")
    if message == "quit":
        break

    client.send(message.encode())


client.close()
server.close()