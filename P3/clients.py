#!/usr/bin/env python3

from os import system, name
import threading
import logging
import socket
import time
import sys
import re

HOST = "192.168.0.13"
PORT = 8080
buffer_size = 8192
gameboard = ""
counter = 0
turn_gotten = threading.Event()

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
def clear():
	if name == 'nt': # for windows
		_ = system('cls')
	else: # for mac and linux(here, os.name is 'posix')
		_ = system('clear')

logging.basicConfig(level=logging.DEBUG,format=f'{bcolors.OKCYAN}(%(threadName)-10s){bcolors.ENDC} %(message)s',)

def receive(sock_a):
	data = sock_a.recv(buffer_size)
	return str(data, errors='ignore')
def printer(sock_a):
	global gameboard
	logging.debug(f"Printer initialized")
	while True:
		if "You lose!" in gameboard or "You Win!!!" in gameboard:
			exit()
		elif f"Your turn {counter}" in gameboard:
			gameboard.replace("Your turn {counter}", "")
			if not turn_gotten.isSet():
				turn_gotten.set()
				gameboard = ""
		elif "GAME TERMINATED" in gameboard:
			exit()
		if not turn_gotten.isSet():
			gameboard = receive(sock_a)
			# logging.debug(f"Gameboard: {gameboard}")
			# clear()
			print(gameboard)
		# time.sleep(1)

def make_movement(sock_a):
	global turn_gotten, gameboard, counter
	while True:
		logging.debug(f"Waiting for turn")
		turn_gotten.wait()
		logging.debug("Your movement: ")
		message = input()
		sock_a.sendall(str.encode(message))
		turn_gotten.clear()
		counter += 1
		gameboard = ""
		time.sleep(1)
if __name__ == '__main__':
	# if len(sys.argv) >= 3:
	# 	HOST = sys.argv[1]
	# 	PORT = sys.argv[2]
	# 	if int(PORT) < 1023:
	# 		print("[E] Port must be reather than 2024")
	# 		exit()
	# else:
	# 	print("[E] Program usage: python client-minesweeper.py [HOST] [PORT]")
	# 	exit()
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		first_message = ""
		s.connect((HOST, int(PORT)))
		# clear()
		data = s.recv(buffer_size)
		sdata = data.decode("utf-8")
		if "Hi! You are player 1" in sdata:
			logging.debug(sdata)
			level = input()
			first_message = f"level{level}"
		else:
			logging.debug(sdata)
			first_message = f"I'm a player"
		s.sendall(str.encode(first_message))
		data = s.recv(buffer_size)
		sdata = data.decode('utf-8')
		logging.debug(sdata)
		p = threading.Thread(
			name="Printer",
			target=printer,
			args=(s,)
		)
		p.start()
		m = threading.Thread(
			name="Input",
			target=make_movement,
			args=(s,)
		)
		m.start()
		m.join()
		p.join()
