from os import system, name
import threading
import selectors
import logging
import socket
import types
import time
import sys

buffer_size = 8192

sel = selectors.DefaultSelector()
e = threading.Event()
first_connection = True
level = False

HOST = "192.168.0.13"
PORT = 8080

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

def first_player():
	global level, e
	with socket.socket() as sock:
		sock.bind((HOST, PORT))
		sock.listen(10)
		sock.setblocking(False)
		sel.register(sock, selectors.EVENT_READ, accept)
		logging.debug("Selector set")
		while not e.isSet():
			logging.debug("Waiting event... ")
			events = sel.select()
			for key, mask in events:
				callback = key.data
				callback(key.fileobj, mask)
		# conn, addr = sock.accept()
		# with conn:
		# 	logging.debug(f"Connected to {addr}")
		# 	while True:
		# 		logging.debug("Waiting for data... ")
		# 		data = conn.recv(buffer_size)
		# 		logging.debug(f"Recieved: {data}")
		# 		if not data:
		# 			level = True
		# 			logging.debug(f"{bcolors.OKBLUE}Event initialized{bcolors.ENDC}")
		# 			e.set()
		# 			break
		# 		logging.debug("Sending reply ...")
		# 		conn.sendall(str.encode("Yeah baby!!"))

def wait_for_event():
	"""Wait for the event to be set before doing anything"""
	global e
	logging.debug("Waiting for initial event")
	event_is_set = e.wait()
	logging.debug(f"event_is_set : {event_is_set}")
	logging.debug(f"{bcolors.OKBLUE}We can start to play now!{bcolors.ENDC}")
	


def wait_for_event_timeout(t):
	"""Wait t seconds and then timeout"""
	global level, e
	while not e.isSet():
		# logging.debug("Esperando evento inicio a destiempo")
		event_is_set = e.wait(t)
		logging.debug(f"Event: {event_is_set}, level: {level}")
		if event_is_set and level:
			logging.debug("==> Processing event")
		else:
			logging.debug("==> Doing other thing...")

def accept(sock_a, mask):
	conn, addr = sock_a.accept()  # Should be ready
	logging.debug(f"Connected to {addr}")
	conn.setblocking(False)
	time.sleep(3)
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	#sel.register(conn,selectors.EVENT_WRITE, read_write)

def read_write(sock_c, mask):
	global level, e
	if mask & selectors.EVENT_READ:
		data = sock_c.recv(1024)  # Should be ready
		if data:
			sdata = data.decode()
			logging.debug(f"{bcolors.OKGREEN}Recieved: {sdata} {bcolors.ENDC}")
			if 'level' in sdata:
				e.set()
				level = True
			logging.debug(f"Replying...")
			sock_c.sendall(str.encode("Alllllvvvvvvvv"))  # Hope it won't block
		else:
			logging.debug(f"Closing connection")
			sel.unregister(sock_c)
			sock_c.close()
	if mask & selectors.EVENT_WRITE:
		logging.debug ("Sending data")
		sock_c.sendall(str.encode("END_GAME"))  # Hope it won't block
		logging.debug("Selector END_GAME")
		time.sleep(3)

if __name__ == '__main__':
	# with socket.socket() as sock_accept:
	# 	sock_accept.bind((HOST, PORT))
	# 	sock_accept.listen(100)
	# 	sock_accept.setblocking(False)
	# 	sel.register(sock_accept, selectors.EVENT_READ, accept)
	# 	while True:
	# 		logging.debug("Waiting for event...")
	# 		events = sel.select()
	# 		logging.debug(len(events))
	# 		for key, mask in events:
	# 			callback = key.data
	# 			callback(key.fileobj, mask)
	t1 = threading.Thread(
			name="B",
			target=wait_for_event,
			# args=(,)
		)
	t2 = threading.Thread(
			name="NB",
			target=wait_for_event_timeout,
			args=(2,)
		)
	fp = threading.Thread(
			name="first_player",
			target=first_player,
			# args=(,)
		)
	t1.start()
	t2.start()
	time.sleep(3)
	fp.start()
	t1.join()
	t2.join()
	fp.join()