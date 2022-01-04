from os import system, name
import threading
import selectors
import logging
import socket
import time

bufferSize = 1024

sel = selectors.DefaultSelector()

HOST = "192.168.0.13"
PORT = 8080
cache = []
known_clients = []

def clear():
	if name == 'nt': # for windows
		_ = system('cls')
	else: # for mac and linux(here, os.name is 'posix')
		_ = system('clear')

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

logging.basicConfig(level=logging.DEBUG,format=f'{bcolors.OKCYAN}(%(threadName)-10s){bcolors.ENDC} %(message)s',)

def resolver(sock_a, address_port, id):
	for i in range(5):
		logging.debug(f"Waiting: {5 - i}")
		time.sleep(1)
	logging.debug("Sending response to client")
	message = "Hi UDP client"
	bytesToSend = str.encode(message)
	sock_a.sendto(bytesToSend, address_port)

def accept(sock_a, mask):
	global known_clients
	data, address_port = sock_a.recvfrom(bufferSize)
	# logging.debug(f"Connected to {addr}")
	logging.debug(f"Message from client: {data.decode()}")
	logging.debug(f"Client ip and port: {address_port}")
	known_clients.append(address_port)
	i = len(known_clients)
	r = threading.Thread(
		name=f"Resolver {i}",
		target=resolver,
		args=(sock_a, address_port, i)
	)
	r.start()

def connections_manager():
	sock_accept = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock_accept.bind((HOST, PORT))
	sock_accept.setblocking(False)
	sel.register(sock_accept, selectors.EVENT_READ, accept)
	logging.debug(f"Socket bound {HOST}:{PORT}")
	logging.debug("Listening connections...")
	while (True):
		events = sel.select()
		for key, mask in events:
			if mask & selectors.EVENT_READ and key.data.__name__ == "accept":
				callback = key.data
				callback(key.fileobj, mask)
	logging.debug(f"{bcolors.OKBLUE}Exiting from socket manager{bcolors.ENDC}")
	sock_accept.close()

if __name__ == '__main__':
	# if len(sys.argv) >= 2:
	# 	PORT = int(sys.argv[1])
	# else:
	# 	print("[E] Program usage: python ftp-server.py <PORT>")
	# 	exit()
	cm = threading.Thread(
			name="Connections Manager",
			target=connections_manager
		)
	cm.start()
	cm.join()
	