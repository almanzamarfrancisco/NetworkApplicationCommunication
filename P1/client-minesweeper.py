#!/usr/bin/env python3

from os import system, name
import socket

# HOST = "192.168.0.9"  # El hostname o la IP del servidor
HOST = "192.168.0.10"  # El hostname o la IP del servidor
PORT = 6061  # El puerto que usa el servidor
buffer_size = 2048

def clear():
	if name == 'nt': # for windows
		_ = system('cls')
	else: # for mac and linux(here, os.name is 'posix')
		_ = system('clear')

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
	first_message = True
	s.connect((HOST, PORT))
	clear()
	# data = s.recv(buffer_size)
	# print(data.decode())
	while True:
		if first_message:
			message = "Gameboard request"
			first_message = False
		else:
			message = input("Your movement: ")
		s.sendall(str.encode(message))
		data = s.recv(buffer_size)
		print(data.decode())

