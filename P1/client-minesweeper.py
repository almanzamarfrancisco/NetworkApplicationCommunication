#!/usr/bin/env python3

from os import system, name
import socket
import sys
import re

buffer_size = 8192

def clear():
	if name == 'nt': # for windows
		_ = system('cls')
	else: # for mac and linux(here, os.name is 'posix')
		_ = system('clear')

if __name__ == '__main__':
	if len(sys.argv) >= 3:
		HOST = sys.argv[1]
		PORT = sys.argv[2]
		if int(PORT) < 1023:
			print("[E] Port must be reather than 2024")
			exit()
	else:
		print("[E] Program usage: python client-minesweeper.py [HOST] [PORT]")
		exit()
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		first_message = True
		s.connect((HOST, int(PORT)))
		clear()
		data = s.recv(buffer_size)
		level = input(f"{data.decode()}: ")
		s.sendall(str.encode(level))
		gameboard = ''
		while True:
			if "You lose!" in gameboard or "You Win!!!" in gameboard:
				exit()
				break
			if first_message:
				message = "Gameboard request"
				first_message = False
			else:
				message = input("Your movement: ")
			s.sendall(str.encode(message))
			data = s.recv(buffer_size)
			gameboard = data.decode()
			clear()
			print(gameboard)
		print(gameboard)

