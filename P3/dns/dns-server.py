from os import system, name
import threading
import selectors
import logging
import socket
import random
import json
import time

bufferSize = 1024

sel = selectors.DefaultSelector()

HOST = "192.168.0.13"
PORT = 8080
ROOT_SERVER_HOST = "192.168.0.13"
ROOT_SERVER_PORT = 8090
CCTLD_SERVER_HOST = "192.168.0.13"
CCTLD_SERVER_PORT = 9000
NS_SERVER_HOST = "192.168.0.13"
NS_SERVER_PORT = 9010


cache = [{"host_name": "facebook.com", "ip_address": "66.220.144.0"}]
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

def search_in_cache(data):
	global cache
	logging.debug(f"======>>>>{cache}")
	for c in cache:
		if data == c["host_name"]:
			logging.debug(f"Found {c['host_name']} in ip addres {c['ip_address']}")
			return json.dumps(c)
	return False
def request_ip(data):
	message = ""
	with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock_rs:
		sock_rs.sendto(str.encode(data), (ROOT_SERVER_HOST, ROOT_SERVER_PORT))
		response = sock_rs.recvfrom(bufferSize)
		logging.debug(f"Message from ROOT Server {response[0].decode()}")
		message = response[0].decode()
	logging.debug(f"Searching in CCTLD Server...")
	with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock_cctld:
		sock_cctld.sendto(str.encode(data), (CCTLD_SERVER_HOST, CCTLD_SERVER_PORT))
		response = sock_cctld.recvfrom(bufferSize)
		logging.debug(f"Message from CCTLD Server {response[0].decode()}")
		message = response[0].decode()
	logging.debug(f"Searching in Name Server...")
	with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock_ns:
		sock_ns.sendto(str.encode(data), (NS_SERVER_HOST, NS_SERVER_PORT))
		response = sock_ns.recvfrom(bufferSize)
		logging.debug(f"Message from Name Server {response[0].decode()}")
		message = response[0].decode()
	return message
def resolver(sock_a, address_port, id, data):
	global cache
	logging.debug(f"Searching...")
	message = search_in_cache(data)
	if not message:
		message = "Host not found in cache"
		logging.debug("Host not found in cache")
		with open('root-servers.json') as f:
			root_servers = json.load(f)
			n = random.randint(0,9)
			for i, rs in enumerate(root_servers):
				logging.debug(f"Searching for .mx ip address in {rs['host_name']}")
				time.sleep(0.2)
				if i == n:
					logging.debug(f"{bcolors.OKGREEN}Found!{bcolors.ENDC}")
					break
		message = request_ip(data)
		cache.append(json.loads(message))
	logging.debug(f"Sending response to client... {message}")
	bytesToSend = str.encode(message)
	sock_a.sendto(bytesToSend, address_port)
def accept(sock_a, mask):
	global known_clients
	data, address_port = sock_a.recvfrom(bufferSize)
	# logging.debug(f"Connected to {addr}")
	logging.debug(f"Searching for: {data.decode()}")
	logging.debug(f"Client ip and port: {address_port}")
	known_clients.append(address_port)
	i = len(known_clients)
	r = threading.Thread(
		name=f"Resolver {i}",
		target=resolver,
		args=(sock_a, address_port, i, data.decode())
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
	