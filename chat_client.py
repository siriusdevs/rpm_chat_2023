from socket import socket
from chat_server import ADDRESS, PORT, DISCONNECT, AUTH_OK, decode, encode

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
        
def main(client: socket) -> None:
    client.connect((ADDRESS, PORT))
    if auth(client):
        while True:
            msg = input('Your msg: ')
            client.send(encode(msg))
            if msg == DISCONNECT:
                break

client = socket()
try:
    main(client)
except KeyboardInterrupt:
    print('Мог дисконнект написать?')
    client.send(encode(DISCONNECT))
except BrokenPipeError as error:
    print(f'Всё сломалось {error.strerror}')
except Exception as error:
    print('Какаята ещё ошибка', error)
finally:
    client.close()