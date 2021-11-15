#!/usr/bin/env python3

import socket

HOST = "192.168.0.13"
PORT = 8080
buffer_size = 8192

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("Enviando mensaje...")
    s.sendall(b"Im player two")
    sdata = ""
    while not "END_GAME" in sdata:
        print("Waiting for answer...")
        data = s.recv(buffer_size)
        sdata = data.decode()
        print("Recieved,", sdata, " de", s.getpeername())