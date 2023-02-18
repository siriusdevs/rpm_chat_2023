from socket import socket
from squaring_server.server import ADDRESS, PORT, DISCONNECT, decode, encode


client = socket()
client.connect((ADDRESS, PORT))

while True:
    msg = input('Your msg: ')
    client.send(encode(msg))
    if msg == DISCONNECT:
        break
    print(f'Server: {decode(client.recv(1024))}')

client.close()
