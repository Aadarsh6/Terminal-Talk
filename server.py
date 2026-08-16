import socket
import threading

from protocol import send_message, recv_message

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("127.0.0.1", 9999))
server.listen()

print("Server is waiting for a connection...")


#! "I won't continue until somebody connects to me.
client, address = server.accept()

print("Client address:", address)


def receive_message():
    while True:
        message = recv_message(client)

        if message is None:
            print("Client disconnected")
            break

        print("Client:", message)

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

    send_message(client, message)


client.close()
server.close()