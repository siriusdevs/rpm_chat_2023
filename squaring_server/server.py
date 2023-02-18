from socket import socket
from dotenv import load_dotenv
import os

load_dotenv()

ADDRESS = os.getenv('ADDRESS')
DISCONNECT = os.getenv('DISCONNECT')
ENCODING = os.getenv('ENCODING')
try:
    PORT = int(os.getenv('PORT'))
except Exception as error:
    print(f'Error occured while loading PORT:{error} \n, defaults to 8001')
    PORT = 8001


def encode(text: str, coding=ENCODING) -> bytes:
    return text.encode(coding)


def decode(msg: bytes, coding=ENCODING) -> str:
    return msg.decode(coding)


def main(server: socket) -> None:
    server.bind((ADDRESS, PORT))
    server.listen()

    client, cl_address = server.accept()
    print(f'Client connected from {cl_address}')

    while True:
        msg = decode(client.recv(1024))
        if msg == DISCONNECT:
            client.close()
            break
        try:
            num = float(msg)
        except ValueError:
            out_msg = 'Pls numbers only'
        else:
            out_msg = str(num ** 2)
        client.send(encode(out_msg))
        print(f'Message from {cl_address}: {msg}')


if __name__ == '__main__':
    server = socket()
    try:
        main(server)
    except KeyboardInterrupt:
        print('Goodbye!')
    except BrokenPipeError as error:
        print(f'Server shut down due to {error.strerror}')
    finally:
        server.close()
