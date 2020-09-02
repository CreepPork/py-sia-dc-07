import json
import os
import re
import socket
import sys
import threading
import time
from datetime import datetime

import crccheck
import requests
from dotenv import find_dotenv, load_dotenv

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
            print('Accepted connection from {}:{} at: {}'.format(
                address[0], address[1], time.asctime(time.localtime(time.time()))))

            client_handler = threading.Thread(
                target=handle_client_connection,
                args=(client_sock,)
            )

            client_handler.start()
        except Exception as e:
            print('{} in accept_connections'.format(e))
            if client_sock:
                print('Closing client socket in accept_connections.')
                # client_sock.close()
            break


def handle_client_connection(client_socket: socket.create_connection):
    try:
        request = client_socket.recv(1024)
        result = process_request_data(request)

        if isinstance(result, dict):
            send_ack_message(client_socket, result)
        elif result == True:
            # Ignore message because it is a NULL message
            pass
        else:
            send_nak_message(client_socket)
            # client_socket.close()

        # Don't close the socket, let it be closed by the client
    except Exception as e:
        print('{} in handle_client_connection'.format(e))
        if client_socket:
            print('Closing client socket in handle_client_connection')
            # client_socket.close()

        raise Exception


def process_request_data(request: bytes) -> bool and dict:
    # example payload: b'\n9EC40027"ADM-CID"0001L0#1002[#1002|1602 00 001]\r'
    print(request)
    payload = request.decode('ASCII')

    # \n
    lf = payload[0]

    # \r
    cr = payload[-1]

    if lf != '\n' or cr != '\r':
        print('LF or CR characers were missing from the payload.')
        return False

    # 4 bytes in Hex-ASCII (e.g. 9EC4)
    crc = payload[1:5]

    if crc != calculate_crc(request):
        print('CRCs are invalid and do not match.')
        return False

    # <0LLL> (e.g. 0027)
    packet_length_payload = payload[5:9]

    if packet_length_payload != calculate_message_length_secolink(request):
        print(packet_length_payload, calculate_message_length_secolink(request))
        print('Packet length does not match, ignoring check.')

    # Split the payload into managable chunks later
    split_payload = payload.split('"')
    payload_end = split_payload[2]

    # "<ID>" (e.g. "ADC-CID")
    message_protocol_id = split_payload[1]

    # Sequential number generated by the transmitter
    sequence_number = payload_end[:4]

    # Reciever number (sometimes omitted)
    reciever_number = None

    try:
        reciever_number = re.findall(r'R[0-9]*#', payload_end)[0]
        reciever_number = re.findall(r'[0-9]+', reciever_number)[0]
    except IndexError:
        reciever_number = '0'

    # Line number
    line_number = None

    try:
        line_number = re.findall(r'L[0-9]*#', payload_end)[0]
        line_number = re.findall(r'[0-9]+', line_number)[0]
    except IndexError:
        line_number = '0'

    # All data starts with [ and ends with ]
    message_block = re.findall(r'\[(.*?)\]', payload_end)[0]

    # Parse the message into a JSON format
    parsed_message_json = None

    if message_protocol_id == 'ADM-CID':
        parsed_message_json = parse_adc_cid_message(
            message_block,
            sequence_number,
            reciever_number,
            line_number
        )
    elif message_protocol_id == 'NULL':
        print('Recieved a NULL message')

        return True
    else:
        print('Unsupported message protocol ID, cannot parse: got {}'.format(
            message_protocol_id
        ))
        return False

    relay_message_contents(parsed_message_json)

    return parsed_message_json


def parse_adc_cid_message(message: str, seq_num: str, rec_num: str, ln_num: str) -> dict:
    message_blocks = message.split('|')

    # starts with a #ACCT, so we drop the pound
    account_number = int(message_blocks[0][1:], 10)

    contact_id = message_blocks[1].split(' ')

    # 1 = New Event or Opening,
    # 3 = New Restore or Closing,
    # 6 = Previously reported condition still present (Status report)
    event_qualifier = int(contact_id[0][0], 10)

    # 3 decimal(!) digits XYZ (e.g. 602)
    event_code = int(contact_id[0][1:], 10)

    # 2 decimal(!) digits GG, 00 if no info (e.g. 01)
    group_or_partition_number = contact_id[1]

    # 3 decimal(!) digits CCC, 000 if no info (e.g. 001)
    zone_number_or_user_number = contact_id[2]

    return {
        'sequence_number': seq_num,
        'reciever_number': rec_num,
        'line_number': ln_num,
        'account_number': account_number,
        'event_qualifier': event_qualifier,
        'event_code': event_code,
        'group_or_partition_number': group_or_partition_number,
        'zone_number_or_user_number': zone_number_or_user_number
    }


def relay_message_contents(data: dict):
    print('Received {}'.format(data))

    headers = {'Authorization': 'Bearer {}'.format(MESSAGE_RELAY_BEARER_TOKEN)}

    r = requests.post(MESSAGE_RELAY_ADDR, json=data, headers=headers)

    print('Sent HTTP request to relay, got {} status'.format(r.status_code))


def get_message_contents_with_id(request: bytes) -> bytes:
    split_payload = request[:-1].decode('ASCII').split('"')

    payload = '"{}"'.format(split_payload[1]) + split_payload[2]

    return payload.encode('ASCII')


def calculate_crc(request: bytes) -> str:
    message = get_message_contents_with_id(request)

    return crccheck.crc.CrcArc().process(message).finalhex().upper()


def calculate_message_length(request: bytes) -> str:
    # This should be per the standard, but my PE doesn't like this (see below function)
    message = get_message_contents_with_id(request)

    return f'{len(message):04}'


def calculate_message_length_secolink(request: bytes) -> str:
    # Secolink has a broken implementation of this on their LAN800
    message = request[:-1].decode('ASCII').split('"')[2][3:].encode('ASCII')

    return f'{len(message):04}'


def generate_timestamp() -> str:
    now = datetime.now()

    return now.strftime('_%H:%M:%S,%m-%d-%Y')


def send_ack_message(client_socket: socket.create_connection, result: dict):
    message = '"ACK"{}R{}L{}#{}[]\r'.format(
        result['sequence_number'],
        result['reciever_number'],
        result['line_number'],
        result['account_number']
    )

    message = '\n' \
        + calculate_crc(message.encode('ASCII')) \
        + calculate_message_length_secolink(message.encode('ASCII')) \
        + message

    print('Sending message {} back to socket'.format(message.encode('ASCII')))

    client_socket.send(message.encode('ASCII'))


def send_nak_message(client_socket: socket.create_connection):
    message = '"NAK"0000R0L0A0[]{}\r'.format(
        generate_timestamp()
    )

    message = '\n' \
        + calculate_crc(message.encode('ASCII')) \
        + calculate_message_length_secolink(message.encode('ASCII')) \
        + message

    print('Sending message {} back to socket'.format(message.encode('ASCII')))

    client_socket.send(message.encode('ASCII'))


if __name__ == "__main__":
    sys.exit(main())
