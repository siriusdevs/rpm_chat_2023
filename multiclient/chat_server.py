from socket import socket
from dotenv import load_dotenv
from os import getenv
from threading import Thread, Lock
from types import SimpleNamespace


consts = SimpleNamespace()
load_dotenv()

consts.ADDRESS = getenv('ADDRESS')
consts.DISCONNECT = getenv('DISCONNECT')
consts.ENCODING = getenv('ENCODING')
consts.AUTH_OK = getenv('AUTH_OK')
consts.GREETING = getenv('GREETING')
consts.SHUTDOWN: str = getenv('SHUTDOWN', default='/shutdown')
consts.HELP: str = getenv('HELP', default='/help')
consts.LIST: str = getenv('LIST', default='/list')
consts.WHISPER = getenv('WHISPER', default='/whisper')
try:
    consts.PORT = int(getenv('PORT'))
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
            if msg.startswith(consts.WHISPER):
                parts = msg.split()
                if len(parts) >= 3:
                    target_msg = ' '.join(parts[2:])
                    with users_lock:
                        target_socket: socket = users.get(parts[1])
                        if target_socket:
                            target_socket.send(encode(f'{name} whispered: {target_msg}'))
                else:
                    client.send(encode(f'Usage: {consts.WHISPER} user message'))
            else:
                msg = f'{name}: {msg}'
                print(msg)
                with users_lock:
                    if not name in users.keys():
                        return True
                    for username in users.keys():
                        if username == name:
                            continue
                        user_socket: socket = users.get(username)
                        if user_socket:
                            user_socket.send(encode(msg))
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
