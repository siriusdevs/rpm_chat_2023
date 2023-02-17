from socket import socket
from dotenv import load_dotenv
import os
from threading import Thread, Lock, Event

load_dotenv()

ADDRESS = os.getenv('ADDRESS')
DISCONNECT = os.getenv('DISCONNECT')
ENCODING = os.getenv('ENCODING')
AUTH_OK = os.getenv('AUTH_OK')
try:
    PORT = int(os.getenv('PORT'))
except:
    PORT = 8001

def encode(text: str, coding=ENCODING) -> bytes:
    return text.encode(coding)

def decode(data: bytes, coding=ENCODING) -> str:
    return data.decode(coding)


def receiver(client: socket, name: str):
    while True:
        print(f'{name}: {decode(client.recv(1024))}')

def new_client(client: socket, cl_address: tuple) -> str:
    global users, users_lock
    greeting = 'Greeting weary traveller!\n\
        Welcome to our server! It does absolutely nothing.\n\
        Send /disconnect to disconnect from server.\
        \n\n Please tell us your name, hero!'
    client.send(encode(greeting))
    while True:
        data = decode(client.recv(1024))
        if data == DISCONNECT:
            client.send(encode(DISCONNECT))
            print(f'Client {cl_address} has disconnected')
            return
        with users_lock:
            if data in users.keys():
                client.send(encode('Username is taken'))
            else:
                client.send(encode(AUTH_OK))
                print(f'Client {cl_address} authenticated by name {data}')
                users[data] = client
                Thread(target=receiver, args=(client, data)).start()
                return

def accept_client(server: socket):
    while True:
        client, cl_address = server.accept()
        print(f'Client connected from {cl_address}')
        Thread(target=new_client, args=(client, cl_address), daemon=True).start()

def main(server: socket) -> None:
    server.bind((ADDRESS, PORT))
    server.listen()
    Thread(target=accept_client, args=(server,), daemon=True).start()

    while True:
        command = input()
        if command == 'q':
            for user in users.values():
                user.send(encode(DISCONNECT))
                user.close()
            break

if __name__ == '__main__':
    users: dict = {}
    users_lock = Lock()
    server = socket()
    try:
        main(server)
    except KeyboardInterrupt:
        print('Goodbye!')
    except BrokenPipeError as error:
        print(f'Server shut down due to {error.strerror}')
    finally:
        server.close()