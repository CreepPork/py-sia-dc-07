import os
import random
import socket

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

BIND_PORT = int(os.getenv('BIND_PORT'))

# create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
client.connect(('127.0.0.1', BIND_PORT))

ex_data = [
    b'\n9EC40027"ADM-CID"0001L0#1002[#1002|1602 00 001]\r',
    b'\n75140027"ADM-CID"0001L0#1002[#1002|3354 00 004]\r',
    b'\nBE780027"ADM-CID"0041L0#1001[#1001|1602 00 030]\r',
    b'\n4B540027"ADM-CID"0037L0#1001[#1001|3354 00 004]\r',
    b'\n20BD0027"ADM-CID"0028L0#1001[#1001|1406 03 004]\r'
]

selected_data = random.choice(ex_data)

print('Selected data: {}'.format(selected_data))

# Send some test data
client.send(selected_data)

# receive the response data (4096 is recommended buffer size)
response = client.recv(4096)

print('Received data: {}'.format(response))
