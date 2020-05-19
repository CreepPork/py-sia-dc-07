import socket

# create an ipv4 (AF_INET) socket object using the tcp protocol (SOCK_STREAM)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the client
client.connect(('0.0.0.0', 5002))

ex_data_1 = b'\n9EC40027"ADM-CID"0001L0#1002[#1002|1602 00 001]\r'
ex_data_2 = b'\n75140027"ADM-CID"0001L0#1002[#1002|3354 00 004]\r'

# Send some test data
client.send(ex_data_2)

# receive the response data (4096 is recommended buffer size)
response = client.recv(4096)

print(response)
