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
first_player_connection = threading.Event()
second_player_connection = threading.Event()
level_selection = threading.Event()
turn = [threading.Event(), threading.Event()]
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

def first_player(conn):
	global first_player_connection
	first_player_connection.wait()
	logging.debug(f"{bcolors.FAIL} Ready from first_player: {conn}{bcolors.ENDC}")
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
def second_player(conn):
	global second_player_connection
	logging.debug(f"{bcolors.FAIL} Ready from second_player: {conn}{bcolors.ENDC}")
	second_player_connection.wait()
	logging.debug(f"{bcolors.FAIL}===> HERE I HAVE TO FOLLOW THE CONNECTION{bcolors.ENDC}")
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
def wait_for_event():
	"""Wait for the event to be set before doing anything"""
	global first_player_connection, level_selection, second_player_connection
	first_player_connected = first_player_connection.wait()
	logging.debug(f"First player connected")
	level_selected = level_selection.wait()
	logging.debug(f"level_selected : {level_selected}")
	second_player_connected = second_player_connection.wait()
	logging.debug(f"Second player connected")
	logging.debug(f"{bcolors.OKBLUE}We can start to play now!{bcolors.ENDC}")


def wait_for_event_timeout(t):
	global level, level_selection, second_player_ready
	while not level_selection.isSet():
		level_selected = level_selection.wait(t)
		second_player_connected = second_player_ready.wait(t)
		logging.debug(f"Event: {level_selected}, level: {level}, second_player_ready: {second_player_connected}")
		if level_selected and level and second_player_connected:
			logging.debug("==> Processing event")
		else:
			logging.debug("==> Doing other thing...")
			if not second_player_connected:
				logging.debug("==> Lets wait for second player...")
			else:
				logging.debug(f"{bcolors.OKGREEN}==> SECONDPLAYER READY...{bcolors.ENDC}")


def accept(sock_a, mask):
	global first_player_connection, second_player_connection
	conn, addr = sock_a.accept()  # Should be ready
	logging.debug(f"Connected to {addr}")
	conn.setblocking(False)
	if not first_player_connection.isSet():
		fp = threading.Thread(
			name="first_player",
			target=first_player,
			args=(conn,)
		)
		fp.start()
		first_player_connection.set()
		return
	if first_player_connection.isSet() and not second_player_connection.isSet():
		sp = threading.Thread(
			name="second_player",
			target=second_player,
			args=(conn,)
		)
		sp.start()
		second_player_connection.set()
	# sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	# sel.register(conn,selectors.EVENT_WRITE, read_write)

def read_write(conn, mask):
	global level, level_selection
	if mask & selectors.EVENT_READ:
		data = conn.recv(buffer_size)  # Should be ready
		if data:
			sdata = data.decode()
			logging.debug(f"{bcolors.OKGREEN}Recieved: {sdata} {bcolors.ENDC}")
			if "level" in sdata:
				level_selection.set()
				level = True
			logging.debug(f"Replying...")
			conn.sendall(str.encode("Message"))  # Hope it won't block
		else:
			logging.debug(f"Closing connection")
			sel.unregister(conn)
			conn.close()
	if mask & selectors.EVENT_WRITE:
		logging.debug ("Sending data")
		time.sleep(3)
		conn.sendall(str.encode("WAIT FOR ME"))  # Hope it won't block
		# conn.sendall(str.encode("END_GAME"))  # Hope it won't block
		logging.debug("Selector END_GAME")

if __name__ == '__main__':
	t1 = threading.Thread(
			name="B",
			target=wait_for_event,
			# args=(,)
		)
	t1.start()
	with socket.socket() as sock_accept:
		sock_accept.bind((HOST, PORT))
		sock_accept.listen(100)
		sock_accept.setblocking(False)
		sel.register(sock_accept, selectors.EVENT_READ, accept)
		while True:
			# Wait for first_player
			# start settings
			# wai for other players
			logging.debug("Listening connections...")
			events = sel.select()
			logging.debug(f"Events length: {len(events)}")
			for key, mask in events:
				callback = key.data
				callback(key.fileobj, mask)
	# t2 = threading.Thread(
	# 		name="NB",
	# 		target=wait_for_event_timeout,
	# 		args=(1,)
	# 	)
	
	# t1.join()
	# fp.join()
	# sp.start()