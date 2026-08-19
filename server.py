import socket
import threading

from protocol import recv_message, send_message

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("127.0.0.1", 9999))
server.listen()

print("Server is waiting for a connection...")

client, address = server.accept() # wont continue unless client connect to it


print("Client address:", address)


def receive_message():
    while True:
        message = recv_message(client)

        if message is None:
            print("Client disconnected")
            break

        message = message.decode() #? 4. decode the message you get before printing
        print("Client:", message)

#Create listening thread
thread = threading.Thread(
    target=receive_message,
    daemon=True
)

thread.start()



#main thread for handling typing ans sending


while True:
    message = input("Server: ") #? 1. Take the message
    if message == "quit":
        break


    data = message.encode() #? 2. Encode the message
    send_message(client, data) #? 3. Send the encoded message/data


client.close()
server.close()