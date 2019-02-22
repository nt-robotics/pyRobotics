import socket

HOST = '178.252.218.46'
PORT = 9090

PACKET_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.connect((HOST, PORT))

print("Connected to ", HOST)

# sock.sendall(str.encode("Hello\n"))

# data = 'Hello from client\r\n'
# data = input("Input message:")

# sock.send(str.encode(data + '\n'))
# sock.send(str.encode("Hello" + '\n'))
# sock.send(b'Hello\r\n')
print("Hello\r\n".encode())
sock.send("Hello\r\n".encode())

try:
    data = sock.recv(PACKET_SIZE)
except socket.error as err:
    print("Error: ", err)
else:
    print("Server send:", data)