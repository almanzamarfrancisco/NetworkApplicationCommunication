from os import system, name
import threading
import selectors
import database
import logging
import socket
import time
import sys

buffer_size = 8192

sel = selectors.DefaultSelector()

end_connection = threading.Event()

clients_connection = []
clients_ready = []
port_numbers = []
reply_from = []
messages = []

all_clients_ready = False

HOST = "192.168.0.13"
PORT = 8080
CLIENTS = 1

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

def clients_thread(conn, id):
	global clients_connection, port_numbers
	port_numbers.append(conn.getpeername()[1])
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	logging.debug(f"{bcolors.OKBLUE}Client connection {id + 1} ready in port: {conn.getpeername()[1]}{bcolors.ENDC}")
	clients_connection[id].set()
	ac = f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKCYAN}Hi! You are client {id + 1}\n{bcolors.ENDC}"
	conn.sendall(str.encode(ac))
	counter = 0
	while not end_connection.isSet():
		time.sleep(0.2)
		events = sel.select()
		key, mask = events[id]
		callback = key.data
		callback(key.fileobj, mask)
		# logging.debug(f"{bcolors.WARNING}Client {id + 1} CONDITION {reply_from[id].isSet()} && {mask & selectors.EVENT_READ}{bcolors.ENDC}")
		if reply_from[id].isSet() and mask & selectors.EVENT_READ:
			messages[id] = f"Update..."
			reply_from[id].clear()
			counter += 1
			n = next_client(id)
		else:
			messages[id] = f"Your turn {counter}"
	else:
		logging.debug(f"END: END_CONNECTION")
		conn.sendall(str.encode("END_CONNECTION"))
def next_client(id):
	if id >= CLIENTS - 1:
		return 0
	return id + 1
def accept(sock_a, mask):
	global clients_connection, clients_ready, CLIENTS
	conn, addr = sock_a.accept()
	logging.debug(f"Connected to {addr}")
	conn.setblocking(False)
	if clients_connection[0].isSet():
		logging.debug(f"{bcolors.WARNING}ADDING A CLIENT... {bcolors.ENDC}")
		messages.append("Message number 1")
		reply_from.append(threading.Event())
		clients_connection.append(threading.Event())
		clients_ready.append(threading.Event())
		CLIENTS += 1
	for i, cc in enumerate(clients_connection):
		if not cc.isSet():
			ct = threading.Thread(
				name=f"Client {i + 1}",
				target=clients_thread,
				args=(conn,i)
			)
			ct.start()
			cc.set()
			return
def read_write(conn, mask):
	global messages, port_numbers, clients_ready, all_clients_ready
	client = port_numbers.index(conn.getpeername()[1])
	if mask & selectors.EVENT_READ:
		data = conn.recv(buffer_size) 
		if data:
			sdata = data.decode()
			logging.debug(f"{bcolors.OKGREEN}Recieved from client {client + 1}: {sdata} {bcolors.ENDC}")
			if f"I'm a client" in sdata:
				logging.debug(f"Replying...")
				conn.sendall(str.encode(f"Hi! You are client {client + 1}"))
				clients_ready[client].set()
			if "END_CONNECTION" in sdata:
				logging.debug(f"{bcolors.FAIL} END CONNECTION {bcolors.ENDC}")
				end_connection.set()
			for cr in clients_ready:
				if cr.isSet():
					all_clients_ready = True
				else:
					all_clients_ready = False
			reply_from[client].set()
		else:
			logging.debug(f"Closing connection")
			sel.unregister(conn)
			conn.close()
	if mask & selectors.EVENT_WRITE:
		logging.debug(f"Replying to CLIENT {client + 1}")
		conn.sendall(str.encode(messages[client]))
def connections_manager():
	global all_clients_ready, CLIENTS
	sock_accept = socket.socket()
	sock_accept.bind((HOST, PORT))
	sock_accept.listen(10)
	sock_accept.setblocking(False)
	sel.register(sock_accept, selectors.EVENT_READ, accept)
	logging.debug(f"Socket bound {HOST}:{PORT}")
	logging.debug("Listening connections...")
	while not end_connection.isSet():
		events = sel.select()
		for key, mask in events:
			if mask & selectors.EVENT_READ and key.data.__name__ == "accept":
				callback = key.data
				callback(key.fileobj, mask)
	logging.debug(f"{bcolors.OKBLUE}Exiting from socket manager{bcolors.ENDC}")
	sock_accept.close()
if __name__ == '__main__':
	messages.append("Message number 1")
	reply_from.append(threading.Event())
	clients_connection.append(threading.Event())
	clients_ready.append(threading.Event())
	sm = threading.Thread(
			name="Connections Manager",
			target=connections_manager
		)
	sm.start()
	sm.join()