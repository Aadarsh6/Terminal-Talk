from nacl.public import PrivateKey, Box

#aadarsh key

aadarsh_Private = PrivateKey.generate()
aadarsh_Public = aadarsh_Private.public_key

#mishra key

mishra_private = PrivateKey.generate()
mishra_public = mishra_private.public_key


#aadarsh user
#aadarsh private + mishra public

aadarsh_Box = Box(aadarsh_Private, mishra_public)

#mishra box
#mishra private + aadarsh public

mishra_box = Box(mishra_private, aadarsh_Public)

#aadarsh encrypt

message = "Hello!"

encrypted = aadarsh_Box.encrypt(message.encode())

print("Orignal: ", message)
print("Encrypted: ", encrypted)

#mishra decrypt

decrypted = mishra_box.decrypt(encrypted)

print("Decrypted:", decrypted.decode())

