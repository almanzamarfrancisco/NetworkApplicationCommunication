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
reply_from = [threading.Event(), threading.Event()]
messages = ["Message number 1", "Message number 1"]
port_numbers = []
gameover = threading.Event()
level = False
second_player_ready = threading.Event()

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
	global first_player_connection, port_numbers
	first_player_connection.wait()
	logging.debug(f"{bcolors.FAIL} Ready from first_player: {conn}{bcolors.ENDC}")
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	port_numbers.append(conn.getpeername()[1])
	counter = 0
	while True:
		turn[0].wait()
		logging.debug("=> FIRST player turn")
		messages[0] = f"FIRST PLAYER, make a movement ({counter})"
		counter += 1
		events = sel.select()
		key, mask = events[0]
		callback = key.data
		time.sleep(1)
		logging.debug(f"{bcolors.WARNING}HERE READ IS {mask & selectors.EVENT_READ} AND reply_from[0] IS {reply_from[0].isSet()}{bcolors.ENDC}")
		if reply_from[0].isSet() and mask & selectors.EVENT_READ:
			turn[0].clear()
			reply_from[0].clear()
			turn[1].set()
		callback(key.fileobj, mask)
def second_player(conn):
	global second_player_connection
	logging.debug(f"{bcolors.FAIL} Ready from second_player: {conn}{bcolors.ENDC}")
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	port_numbers.append(conn.getpeername()[1])
	second_player_connection.wait()
	counter = 0
	while True:
		turn[1].wait()
		logging.debug("=> SECOND player turn")
		messages[1] = f"SECOND PLAYER, make a movement ({counter})"
		counter += 1
		events = sel.select()
		key, mask = events[1]
		callback = key.data
		time.sleep(1)
		logging.debug(f"{bcolors.WARNING}HERE READ IS {mask & selectors.EVENT_READ} AND reply_from[1] IS {reply_from[1].isSet()}{bcolors.ENDC}")
		if reply_from[1].isSet() and mask & selectors.EVENT_READ:
			turn[1].clear()
			reply_from[1].clear()
			turn[0].set()
		callback(key.fileobj, mask)
def game_initializer():
	"""Wait for the event to be set before doing anything"""
	global first_player_connection, level_selection, second_player_connection, second_player_ready
	first_player_connection.wait()
	logging.debug(f"First player connected")
	level_selection.wait()
	logging.debug(f"==> level_selected")
	second_player_connection.wait()
	logging.debug(f"Second player connected")
	while not second_player_ready.isSet():
		events = sel.select()
		key, mask = events[1]
		callback = key.data
		callback(key.fileobj, mask)
	logging.debug(f"Second player ready")
	logging.debug(f"{bcolors.OKBLUE}We can start to play now!{bcolors.ENDC}")
	turn[0].set()
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
def read_write(conn, mask):
	global level, level_selection, messages, port_numbers, second_player_ready
	player = port_numbers.index(conn.getpeername()[1])
	if mask & selectors.EVENT_READ:
		data = conn.recv(buffer_size)  # Should be ready
		if data:
			sdata = data.decode()
			logging.debug(f"{bcolors.OKGREEN}Recieved from player {player + 1}: {sdata} {bcolors.ENDC}")
			if "level" in sdata:
				level_selection.set()
				level = True
				logging.debug(f"Replying...")
				conn.sendall(str.encode("First message from server for FIRST player"))
			if "Im player two" in sdata:
				logging.debug(f"Replying...")
				conn.sendall(str.encode("First message from server for SECOND player"))
				second_player_ready.set()
			if level and second_player_ready.isSet():
				logging.debug(f"{bcolors.WARNING}Executing reply_from[{player}]{bcolors.ENDC}")
				reply_from[player].set()
		else:
			logging.debug(f"Closing connection")
			sel.unregister(conn)
			conn.close()
	if mask & selectors.EVENT_WRITE:
		logging.debug (f"Sending data to PLAYER {player + 1}: {messages[player]}")
		conn.sendall(str.encode(messages[player]))
		# conn.sendall(str.encode("END_GAME"))
		logging.debug("Data sent")
def socket_manager():
	global first_player_connection, second_player_connection, gameover
	sock_accept = socket.socket()
	sock_accept.bind((HOST, PORT))
	sock_accept.listen(100)
	sock_accept.setblocking(False)
	sel.register(sock_accept, selectors.EVENT_READ, accept)
	logging.debug("Listening connections...")
	while not first_player_connection.isSet() or not second_player_connection.isSet():
		events = sel.select()
		for key, mask in events:
			if mask & selectors.EVENT_READ:
				callback = key.data
				callback(key.fileobj, mask)
	sock_accept.close()
if __name__ == '__main__':
	t1 = threading.Thread(
			name="Game initializer",
			target=game_initializer,
			# args=(,)
		)
	lc = threading.Thread(
			name="Socket Manager",
			target=socket_manager
		)
	t1.start()
	lc.start()
	t1.join()
	lc.join()