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
players_connection = []
players_ready = []
level_selection = threading.Event()
turns = []
reply_from = []
messages = []
port_numbers = []
gameover = threading.Event()
level = False
all_players_ready = False

HOST = "192.168.0.13"
PORT = 8080
CLIENTS = 2

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
	port_numbers.append(conn.getpeername()[1])
	first_player_connection.wait()
	players_ready[0].set()
	logging.debug(f"{bcolors.FAIL} Ready from first_player: {conn}{bcolors.ENDC}")
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	counter = 0
	while not gameover.isSet():
		time.sleep(1)
		turns[0].wait()
		logging.debug("=> FIRST player turn")
		clear_turns(0)
		events = sel.select()
		key, mask = events[0]
		callback = key.data
		callback(key.fileobj, mask)
		# logging.debug(f"{bcolors.WARNING}HERE READ IS {mask & selectors.EVENT_READ} AND reply_from[0] IS {reply_from[0].isSet()}{bcolors.ENDC}")
		if reply_from[0].isSet() and mask & selectors.EVENT_READ:
			messages[0] = f"FIRST PLAYER, make a movement ({counter})"
			counter += 1
			turns[0].clear()
			reply_from[0].clear()
			turns[1].set()
		else:
			logging.debug("Update gameboard")
			continue
	else:
		messages[0] = f"END_GAME"
		events = sel.select()
		key, mask = events[0]
		callback = key.data
		callback(key.fileobj, mask)
def players_thread(conn, id):
	global players_connection
	port_numbers.append(conn.getpeername()[1])
	logging.debug(f"{bcolors.FAIL} Ready: {conn}{bcolors.ENDC}")
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	players_ready[id].wait()
	counter = 0
	while not gameover.isSet():
		time.sleep(1)
		turns[id].wait()
		logging.debug(f"=> Player {id + 1} turn gotten")
		clear_turns(id)
		events = sel.select()
		key, mask = events[id]
		callback = key.data
		callback(key.fileobj, mask)
		# logging.debug(f"{bcolors.WARNING}HERE READ IS {mask & selectors.EVENT_READ} AND reply_from[1] IS {reply_from[1].isSet()}{bcolors.ENDC}")
		if reply_from[id].isSet() and mask & selectors.EVENT_READ:
			messages[id] = f"PLAYER {id}, make a movement ({counter})"
			counter += 1
			turns[id].clear()
			reply_from[id].clear()
			n = next_player(id)
			turns[n].set()
		else:
			logging.debug("Update gameboard")
			continue
	else:
		messages[id] = f"END_GAME"
		events = sel.select()
		key, mask = events[id]
		callback = key.data
		callback(key.fileobj, mask)
def next_player(id):
	if id >= CLIENTS - 1:
		return 0
	return id + 1
def clear_turns(id):
	for i, turn in enumerate(turns):
		if i == id:
			continue
		turn.clear()
def players_connection_ready():
	global players_connection
	for pc in players_connection:
		if not pc.isSet():
			return False
	return True
def game_initializer():
	global first_player_connection, level_selection, players_connection, players_ready
	first_player_connection.wait()
	logging.debug(f"First player connected")
	level_selection.wait()
	logging.debug(f"==> level_selected")
	for i, pr in enumerate(players_ready):
		pr.wait()
		logging.debug(f"Player {i + 1} connected")
	logging.debug(f"All players ready!")
	logging.debug(f"{bcolors.OKBLUE}We can start to play now!{bcolors.ENDC}")
	turns[0].set()
def accept(sock_a, mask):
	global first_player_connection, players_connection, players_ready
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
	if first_player_connection.isSet() and not players_connection_ready():
		logging.debug(f"Waiting for other players")
		for i, pc in enumerate(players_connection):
			if not pc.isSet():
				pt = threading.Thread(
					name=f"Player {i + 2}",
					target=players_thread,
					args=(conn,i + 1)
				)
				pt.start()
				pc.set()
				return
def read_write(conn, mask):
	global level, level_selection, messages, port_numbers, players_ready, all_players_ready
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
			if f"Im player" in sdata:
				logging.debug(f"Replying...")
				conn.sendall(str.encode(f"Hi! You are player {player + 1}"))
				players_ready[player].set()
			if "END_GAME" in sdata:
				logging.debug(f"{bcolors.FAIL} GAME OVER {bcolors.ENDC}")
				gameover.set()
			for index, pr in enumerate(players_ready):
				if pr.isSet():
					all_players_ready = True
				else:
					all_players_ready = False
			if level and all_players_ready:
				# logging.debug(f"{bcolors.WARNING}Executing reply_from[{player}].set(){bcolors.ENDC}")
				reply_from[player].set()
		else:
			logging.debug(f"Closing connection")
			sel.unregister(conn)
			conn.close()
	if mask & selectors.EVENT_WRITE:
		logging.debug (f"Replying to PLAYER {player + 1}")
		conn.sendall(str.encode(messages[player]))
		# conn.sendall(str.encode("END_GAME"))
		# logging.debug("Data sent")
def socket_manager():
	global first_player_connection, all_players_ready
	sock_accept = socket.socket()
	sock_accept.bind((HOST, PORT))
	sock_accept.listen(10)
	sock_accept.setblocking(False)
	sel.register(sock_accept, selectors.EVENT_READ, accept)
	logging.debug(f"Socket bound {HOST}:{PORT}")
	logging.debug("Listening connections...")
	while not all_players_ready:
		events = sel.select()
		for key, mask in events:
			if mask & selectors.EVENT_READ:
				callback = key.data
				callback(key.fileobj, mask)
	logging.debug(f"{bcolors.OKBLUE}Exiting from socket manager{bcolors.ENDC}")
	for i, rp in enumerate(reply_from):
		rp.clear()
	sock_accept.close()
if __name__ == '__main__':
	if len(sys.argv) >= 2:
		CLIENTS = int(sys.argv[1])
	else:
		print("[E] Program usage: python test.py <CLIENTS>")
		exit()
	for c in range(CLIENTS):
		messages.append("Message number 1")
		reply_from.append(threading.Event())
		turns.append(threading.Event())
		players_connection.append(threading.Event())
		players_ready.append(threading.Event())
	players_connection.pop()
	gi = threading.Thread(
			name="Game initializer",
			target=game_initializer,
		)
	sm = threading.Thread(
			name="Socket Manager",
			target=socket_manager
		)
	gi.start()
	sm.start()
	gi.join()
	sm.join()