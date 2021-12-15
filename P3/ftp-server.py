from os import system, name, popen
import threading
import selectors
import database
import sqlite3
import logging
import socket
import time
import sys
import re

buffer_size = 8192

sel = selectors.DefaultSelector()


clients_connection = []
end_connection = []
clients_ready = []
port_numbers = []
reply_from = []
messages = []
users = []

all_clients_ready = False

HOST = "192.168.0.13"
DATA_PORTS = 8081
PORT = 8080
CLIENTS = 1

book = ""

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

def codes(x):
	return {
		"220": "220 Service ready",
		"330": "330 User response",
		"331": "331 User name ok, need password",
		"332": "332 Password sent",
		"230": "230 User logged in",
		"001": "ls",
		"002": "get",
		"003": "003 Data connection port request",
		"004": "004 Data connection response",
	}.get(x, 500)
def clients_thread(conn, id):
	global clients_connection, port_numbers
	port_numbers.append(conn.getpeername()[1])
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	logging.debug(f"{bcolors.OKBLUE}Client connection {id + 1} ready in port: {conn.getpeername()[1]}{bcolors.ENDC}")
	clients_connection[id].set()
	ac = f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKCYAN}Hi! You are client {id + 1}\n{bcolors.ENDC}"
	conn.sendall(str.encode(ac))
	counter = 0
	while not all_connections_ended():
		time.sleep(0.1)
		events = sel.select()
		key, mask = events[id]
		callback = key.data
		callback(key.fileobj, mask)
		if reply_from[id].isSet() and mask & selectors.EVENT_READ:
			reply_from[id].clear()
			counter += 1
			if counter == 1:
				messages[id] = f"Authenticate your self. Type your user"
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
		users.append("")
		messages.append("220 Service ready")
		reply_from.append(threading.Event())
		clients_ready.append(threading.Event())
		end_connection.append(threading.Event())
		clients_connection.append(threading.Event())
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
def get_command(client, data_port):
	global book, DATA_PORTS
	DATA_PORTS += 1
	lines_total = 0
	with open(f"./books/{book}", "r") as file:
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_connection:
			data_connection.bind((HOST, data_port))
			logging.debug(f"Waiting for client connection... ")
			data_connection.listen()
			data_conn, data_addr = data_connection.accept()
			with data_conn:
				logging.debug(f"Waiting for client to be ready... ")
				data = data_conn.recv(buffer_size)
				if "Ready to recieve data" in data.decode("utf-8"):
					logging.debug(f"Client ready")
				for line in file.readlines():
					lines_total += 1
				data_conn.sendall(str.encode(f"lines_total: {lines_total}"))
				i = 0 
				file.seek(0, 0)
				for line in file.readlines():
					percentage = "{:.0f}".format(i*100/lines_total)
					clear()
					print(f"Progress in client {client}: {percentage}%")
					data_conn.sendall(str.encode(line))
					i += 1
					time.sleep(0.001)
				data_conn.sendall(str.encode("BOOK_TRANSMITION_ENDED"))
				logging.debug("End book transmition...")
				logging.debug("Waiting for commands...")
def read_write(conn, mask):
	global users, messages, port_numbers, clients_ready, all_clients_ready, book, DATA_PORTS
	client = port_numbers.index(conn.getpeername()[1])
	gc = threading.Thread(
				name="Get command",
				target=get_command,
				args=(client, DATA_PORTS,)
			)
	if mask & selectors.EVENT_READ:
		data = conn.recv(buffer_size) 
		if data:
			sdata = data.decode()
			logging.debug(f"{bcolors.OKGREEN}Recieved from client {client + 1}: {sdata} {bcolors.ENDC}")
			if f"I'm a client" in sdata:
				logging.debug(f"Replying...")
				conn.sendall(str.encode(f"Hi! You are client {client + 1}"))
				clients_ready[client].set()
			elif codes("330") in sdata:
				user = sdata.replace(f"{codes('330')} ", "")
				con = sqlite3.connect('example.db')
				cur = con.cursor()
				query = cur.execute("SELECT * FROM users WHERE name=?", (user,)).fetchall()
				if not query:
					logging.debug(f"{bcolors.FAIL}[E] Error to find user{bcolors.ENDC}")
					exit()
				logging.debug(f"{bcolors.OKGREEN}User found: {query[0][0]}{bcolors.ENDC}")
				users[client] = query[0][0]
				con.commit()
				con.close()
				messages[client] = codes("331")
			elif codes("332") in sdata:
				password = sdata.replace(f"{codes('332')} ", "")
				con = sqlite3.connect('example.db')
				cur = con.cursor()
				query = cur.execute("SELECT * FROM users WHERE name=?", (users[client],)).fetchall()
				if not query:
					logging.debug(f"{bcolors.FAIL}[E] Error to find user for logging in password{bcolors.ENDC}")
					exit()
				if not query[0][1] in password:
					logging.debug(f"{bcolors.FAIL}[E] Incorrect password{bcolors.ENDC}")
					exit()
				logging.debug(f"{bcolors.OKGREEN}[I] User logged succesful!{bcolors.ENDC}")
				con.commit()
				con.close()
				messages[client] = codes("230")
			elif codes("001") in sdata:
				logging.debug(f"Command List directory")
				messages[client] = f"{codes('001')} {popen('ls books').read()}"
			elif codes("002") in sdata:
				split = re.split("get", sdata)
				book = split[1].replace(" ", "")
				logging.debug(f"Command get file")
				messages[client] = f"{codes('002')} {book}"
			elif codes("003") in sdata:
				logging.debug(f"{codes('004')} {DATA_PORTS}")
				messages[client] = f"{codes('004')} {DATA_PORTS}"
				gc.start()
			elif "END_CONNECTION" in sdata:
				logging.debug(f"{bcolors.FAIL} END CONNECTION {bcolors.ENDC}")
				end_connection[client].set()
			else:
				logging.debug(f"Command not found")
				messages[client] = f"Command not found"
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
		conn.sendall(str.encode(messages[client]))
def all_connections_ended():
	global end_connection
	for ec in end_connection:
		if not ec.isSet():
			return False
		return True
def connections_manager():
	global all_clients_ready, CLIENTS
	sock_accept = socket.socket()
	sock_accept.bind((HOST, PORT))
	sock_accept.listen(100)
	sock_accept.setblocking(False)
	sel.register(sock_accept, selectors.EVENT_READ, accept)
	logging.debug(f"Socket bound {HOST}:{PORT}")
	logging.debug("Listening connections...")
	while not all_connections_ended():
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
	users.append("")
	messages.append("220 Service ready")
	reply_from.append(threading.Event())
	clients_ready.append(threading.Event())
	end_connection.append(threading.Event())
	clients_connection.append(threading.Event())
	sm = threading.Thread(
			name="Connections Manager",
			target=connections_manager
		)
	sm.start()
	sm.join()