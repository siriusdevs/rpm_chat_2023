from socket import socket
from chat_server import decode, encode
from threading import Thread
from dotenv import load_dotenv
from os import getenv
from argparse import ArgumentParser
from sys import argv


load_dotenv()
DISCONNECT = getenv('DISCONNECT')
AUTH_OK = getenv('AUTH_OK')


def auth(client: socket) -> bool:
    print(decode(client.recv(1024)))
    while True:
        while True:
            name = input('Your name: ')
            if name:
                break
            print('Pls non-empty string input!')
        client.send(encode(name))
        answer = decode(client.recv(1024))
        if answer == DISCONNECT:
            return False
        if answer == AUTH_OK:
            return True
        print(f'Server response: {answer}')


def sender(client: socket):
    while True:
        msg = input()
        client.send(encode(msg))
        if msg == DISCONNECT:
            break


def get_args():
    parser = ArgumentParser()
    parser.add_argument('-a', '--address', default='127.0.0.1')
    parser.add_argument('-p', '--port', default='8001')
    args = parser.parse_args(argv[1:])
    try:
        port = int(args.port)
    except Exception as error:
        print(f'Error occured while parsing args: {error}')
        port = 8001
    return args.address, port


def main(client: socket) -> None:
    client.connect(get_args())
    if auth(client):
        Thread(target=sender, args=(client,), daemon=True).start()
        while True:
            server_msg = decode(client.recv(1024))
            if server_msg == DISCONNECT:
                break
            print(server_msg)


client = socket()
try:
    main(client)
except KeyboardInterrupt:
    print(f'use {DISCONNECT} next time')
    client.send(encode(DISCONNECT))
except BrokenPipeError as error:
    print(f'error (BrokenPipe) occured: {error.strerror}')
except Exception as error:
    print(f'error occured: {error}')
finally:
    client.close()
