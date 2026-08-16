import socket
import threading

from protocol import send_message, recv_message

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(("127.0.0.1", 9999))

print("connected to server")

def receive_message():  
    while True:
        message = recv_message(client)    

        if message is None:
            print("Server disconnected")
            break

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

        send_message(client,message)


client.close()