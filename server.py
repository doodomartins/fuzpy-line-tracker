import socket

HOST = '127.0.0.1'
PORT = 4321

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
server = s.makefile()

while True:
    rules = []
    fuzpy = Fuzpy(rules)

    left = server.readline()
    right = server.readline()
    left_motor = fuzpy.fuzzy_magic(left)
    right_motor = fuzpy.fuzzy_magic(right)

    s.sendall((left_motor+'\n').encode())
    s.sendall((right_motor+'\n').encode())
s.close()
