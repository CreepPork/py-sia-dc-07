import json
import socket
import threading
import os
import requests
import sys

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

BIND_IP = os.getenv('BIND_IP')
BIND_PORT = int(os.getenv('BIND_PORT'))
MESSAGE_RELAY_ADDR = os.getenv('MESSAGE_RELAY_ADDR')
MESSAGE_RELAY_BEARER_TOKEN = os.getenv('MESSAGE_RELAY_BEARER_TOKEN')


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((BIND_IP, BIND_PORT))
    server.listen(5)

    print('Listening on {}:{}'.format(BIND_IP, BIND_PORT))

    accept_connections(server)

    server.close()


def accept_connections(server):
    while True:
        client_sock = None

        try:
            client_sock, address = server.accept()

            print('')
            print('Accepted connection from {}:{}'.format(
                address[0], address[1]))

            client_handler = threading.Thread(
                target=handle_client_connection,
                args=(client_sock,)
            )

            client_handler.start()
        except Exception as e:
            print('{} in accept_connections'.format(e))
            if client_sock:
                print('Closing client socket in accept_connections.')
                client_sock.close()
            break


def handle_client_connection(client_socket):
    try:
        request = client_socket.recv(1024)

        process_request_data(request)

        client_socket.close()
    except Exception as e:
        print('{} in handle_client_connection'.format(e))
        if client_socket:
            print('Closing client socket in handle_client_connection')
            client_socket.close()

        raise Exception


def process_request_data(request: bytes):
    print(request)
    contents = request.decode('ASCII').split(',')

    username, password, asd_id, message = contents
    message = message.rstrip('\x00')

    message_format = message[0:2]

    if message_format != '18':
        print('Message format not supported, need 18, got {}'.format(message_format))
        return

    # 1 = new event or opening, 3 = new restore or closing, 6 = previous event
    event_qualifier = message[2]

    # 3 hex digits
    event_code = message[3:6]

    # 2 hex digits
    group_number = message[6:9]

    # 3 hex digits or can be 0 for no info
    device_or_sensor_number = message[9:13]

    csv_data = {
        'username': username,
        'password': password,
        'asd_id': asd_id,
        'event_qualifier': event_qualifier,
        'event_code': event_code,
        'group_number': group_number,
        'device_or_sensor_number': device_or_sensor_number,
    }

    relay_message_contents(csv_data)


def relay_message_contents(csv_data: dict):
    print('Received {}'.format(csv_data))

    headers = {'Authorization': 'Bearer {}'.format(MESSAGE_RELAY_BEARER_TOKEN)}

    r = requests.post(MESSAGE_RELAY_ADDR, json=csv_data,
                      headers=headers)

    print('Sent HTTP request to relay, got {} status'.format(r.status_code))


if __name__ == "__main__":
    sys.exit(main())
