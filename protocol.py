import struct

def send_message(sock, data):

    #get no of length of data
    length = len(data)

    #convert length in 4 bytes
    header = struct.pack("!I", length)

    #send header first
    sock.sendall(header)    #!sendall() keeps sending until all the provided data has been sent, or an error occurs.

    #send the real meaasge
    sock.sendall(data)


def recv_message(sock):
    try:
        header = b""
        while len(header) < 4:
            chunk = sock.recv(4 - len(header))
            if not chunk:
                return None
            header += chunk

        length = struct.unpack("!I", header)[0]

        data = b""
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                return None
            data += chunk

        return data

    except OSError:
        # ConnectionResetError (WinError 10054), BrokenPipeError,
        # timeouts — connection is dead or unusable. Report it
        # exactly like a clean EOF so callers have ONE convention.
        return None