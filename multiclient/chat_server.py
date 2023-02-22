from socket import socket
from dotenv import load_dotenv
import os
from threading import Thread, Lock

load_dotenv()

ADDRESS = os.getenv('ADDRESS')
DISCONNECT = os.getenv('DISCONNECT')
ENCODING = os.getenv('ENCODING')
AUTH_OK = os.getenv('AUTH_OK')
GREETING = os.getenv('GREETING')
SHUTDOWN: str = os.getenv('SHUTDOWN', default='/shutdown')
HELP: str = os.getenv('HELP', default='/help')
LIST: str = os.getenv('LIST', default='/list')
try:
    PORT = int(os.getenv('PORT'))
except Exception as error:
    print(f'Error occured while loading PORT:{error} \n, defaults to 8001')
    PORT = 8001


def encode(text: str, coding=ENCODING) -> bytes:
    return text.encode(coding)


def decode(msg: bytes, coding=ENCODING) -> str:
    return msg.decode(coding)


def users_enum():
    global users, users_lock
    with users_lock:
        return '\n'.join([f'{num}. {user}' for num, user in enumerate(list(users.keys()))])


def receiver(client: socket, name: str):
    while True:
        print(f'{name}: {decode(client.recv(1024))}')


def new_client(client: socket, cl_address: tuple) -> str:
    global users, users_lock
    client.send(encode(GREETING))
    while True:
        msg = decode(client.recv(1024))
        if msg == DISCONNECT:
            client.send(encode(DISCONNECT))
            print(f'Client {cl_address} has disconnected')
            return
        with users_lock:
            if msg in users.keys():
                client.send(encode('Username is taken'))
            else:
                client.send(encode(AUTH_OK))
                print(f'Client {cl_address} authenticated by name {msg}')
                users[msg] = client
                Thread(target=receiver, args=(client, msg)).start()
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

    helper_msg = f'\nAvailiable commands: \n{HELP}\n{SHUTDOWN}\n{LIST}'
    while True:
        match input():
            case str(SHUTDOWN):
                print('Shutdown!')
                with users_lock:
                    for user in users.values():
                        user.send(encode(DISCONNECT))
                        user.close()
                    break
            case str(LIST):
                print('LIST')
            case str(HELP):
                print(helper_msg)
            case _:
                print(f'Unknown command!\n{helper_msg}')
    

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
