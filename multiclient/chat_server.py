from socket import socket
from dotenv import load_dotenv
import os
from threading import Thread, Lock
from types import SimpleNamespace


consts = SimpleNamespace()
load_dotenv()

consts.ADDRESS = os.getenv('ADDRESS')
consts.DISCONNECT = os.getenv('DISCONNECT')
consts.ENCODING = os.getenv('ENCODING')
consts.AUTH_OK = os.getenv('AUTH_OK')
consts.GREETING = os.getenv('GREETING')
consts.SHUTDOWN: str = os.getenv('SHUTDOWN', default='/shutdown')
consts.HELP: str = os.getenv('HELP', default='/help')
consts.LIST: str = os.getenv('LIST', default='/list')
try:
    consts.PORT = int(os.getenv('PORT'))
except Exception as error:
    print(f'Error occured while loading PORT:{error} \n, defaults to 8001')
    consts.PORT = 8001


def encode(text: str, coding=consts.ENCODING) -> bytes:
    return text.encode(coding)


def decode(msg: bytes, coding=consts.ENCODING) -> str:
    return msg.decode(coding)


def users_enum():
    global users, users_lock
    with users_lock:
        return '\n'.join([f'{num}. {user}' for num, user in enumerate(list(users.keys()))])


def parse_msg(msg: str, name: str, client: socket) -> bool:
    global users, users_lock
    match msg:
        case str(consts.DISCONNECT):
            client.send(encode(consts.DISCONNECT))
            client.close()
            with users_lock:
                if name in users.keys():
                    del users[name]
            print(f'Client {name} has disconnected')
            return False
        case str(consts.LIST):
            client.send(encode(users_enum()))
        case _:
            msg = f'{name}: {msg}'
            print(msg)
            with users_lock:
                for client in users.values():
                    client.send(encode(msg))
    return True


def receiver(client: socket, name: str):
    while True:
        msg = decode(client.recv(1024))
        if not parse_msg(msg, name, client):
            break


def new_client(client: socket, cl_address: tuple) -> str:
    global users, users_lock
    client.send(encode(consts.GREETING))
    while True:
        msg = decode(client.recv(1024))
        if not parse_msg(msg, str(cl_address), client):
            return
        with users_lock:
            if msg in users.keys():
                client.send(encode('Username is taken'))
            else:
                client.send(encode(consts.AUTH_OK))
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
    server.bind((consts.ADDRESS, consts.PORT))
    server.listen()
    Thread(target=accept_client, args=(server,), daemon=True).start()

    helper_msg = f'\nAvailiable commands: \n{consts.HELP}\n{consts.SHUTDOWN}\n{consts.LIST}'
    while True:
        match input():
            case str(consts.SHUTDOWN):
                print('Shutdown!')
                with users_lock:
                    for user in users.values():
                        user.send(encode(consts.DISCONNECT))
                        user.close()
                    break
            case str(consts.LIST):
                print(users_enum())
            case str(consts.HELP):
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
