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
counter = 1
message = ""
stuff = ""

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
		
def codes(x):
	return {
		"220": "220 Service ready",
		"330": "330 User response",
		"331": "331 User name ok, need password",
		"332": "331 Password sent",
		"230": "230 User logged in",
		"149": "149 initializing testing",
	}.get(x, 500)

logging.basicConfig(level=logging.DEBUG,format=f'{bcolors.OKCYAN}(%(threadName)-10s){bcolors.ENDC} %(message)s',)

def receive(sock_a):
	data = sock_a.recv(buffer_size)
	return str(data, errors='ignore')
def printer(sock_a):
	global stuff, message
	# logging.debug(f"Printer initialized")
	while True:
		if "You lose!" in stuff or "You Win!!!" in stuff:
			exit()
		elif f"Your turn {counter}" in stuff:
			if not turn_gotten.isSet():
				turn_gotten.set()
				stuff = ""
		elif codes("220") in stuff:
			logging.debug(f"[I] {codes('220')}")
			logging.debug(f"[I] Type user:")
			message = codes("330")
		elif codes("331") in stuff:
			logging.debug(f"[I] {codes('331')}")
			message = codes("332")
		elif codes("230") in stuff:
			logging.debug(f"[I] {codes('230')}")
			message = codes("149")
		elif "END_CONNECTION" in stuff:
			exit()
		if not turn_gotten.isSet():
			stuff = receive(sock_a)
			# logging.debug(f"Stuff: {stuff}")
			# clear()
			s = re.sub(f"Your turn {counter}", "", stuff)
			# print(s)
		# time.sleep(1)

def make_movement(sock_a):
	global turn_gotten, stuff, counter, message
	while True:
		# logging.debug(f"Waiting for turn")
		turn_gotten.wait()
		# logging.debug("Input message: ")
		input_message = input()
		sock_a.sendall(str.encode(f"{message} {input_message}"))
		message = ""
		turn_gotten.clear()
		counter += 1
		stuff = ""
if __name__ == '__main__':
	# if len(sys.argv) >= 3:
	# 	HOST = sys.argv[1]
	# 	PORT = sys.argv[2]
	# 	if int(PORT) < 1023:
	# 		print("[E] Port must be reather than 2024")
	# 		exit()
	# else:
	# 	print("[E] Program usage: python ftp-client.py [HOST] [PORT]")
	# 	exit()
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		first_message = ""
		s.connect((HOST, int(PORT)))
		# clear()
		data = s.recv(buffer_size)
		first_message = f"I'm a client"
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