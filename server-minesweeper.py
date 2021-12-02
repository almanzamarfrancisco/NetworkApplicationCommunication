#!/usr/bin/env python3

from os import system, name
import threading
import selectors
import logging
import random
import signal
import socket
import ctypes
import time
import sys
import re

buffer_size = 8192

sel = selectors.DefaultSelector()

first_player_connection = threading.Event()
level_selection = threading.Event()
gameover = threading.Event()

players_connection = []
players_ready = []
port_numbers = []
reply_from = []
messages = []
turns = []

all_players_ready = False
level = False

selected_number = 0

first_gameboard = ""
gameover_string = ""

HOST = "192.168.0.13"
PORT = 8080
CLIENTS = 2

# Clear screen
def clear():
	if name == 'nt': # for windows
		_ = system('cls')
	else: # for mac and linux(here, os.name is 'posix')
		_ = system('clear')
# Console colors
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
# Game levels
class levels():
	# Begginer 9x9  => 10 mines
	# Intermediate 16x16 => 40 mines
	# Expert 30x16 => 99 mines
	begginer = {
		"base": 9,
		"heigth": 9,
		"mines": 1,
		"slug": "begginer"
	}
	expert = {
		"base": 16,
		"heigth": 16,
		"mines": 40,
		"slug": "expert"
	}

logging.basicConfig(level=logging.DEBUG,format=f'{bcolors.OKCYAN}(%(threadName)-10s){bcolors.ENDC} %(message)s',)

class ClockThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.stopped = threading.Event()
		self.time = 0
		self.string = ""
	def run(self):
		while not self.stopped.wait(1):
			mins, secs = divmod(self.time, 60)
			self.string = '{:02d}:{:02d}'.format(mins, secs)
			print(self.string, end="\r")
			self.time += 1
	def getTime(self):
		return self.time
	def getString(self):
		return self.string
	def stop(self):
		self.stopped.set()
		return self.time
class Cell:
	def __init__(self, location, cell_type):
		self.cell_type = cell_type
		self.location = {"x": location["x"], "y": location["y"]}
		self.mine_counter = 0
		self.hidden = True
		self.flagged = False
	def setLocation(x, y):
		print("Hello my location is ({x}, {y})")
		self.x = x
		self.y = y
	def setType(self, cell_type):
		self.cell_type = cell_type
	def info(self):
			print(f"Type:  {self.cell_type}; Location:  ({self.location['x']}, {self.location['y']})")
	def oneMineClose(self):
		self.cell_type = "flag"
		self.mine_counter = self.mine_counter + 1
	def setMineCounter(self, mines):
		self.mine_counter = mines
	def setVisible(self):
		self.hidden = False
class PositiveList(list):
	def __getitem__(self, ind):
		if ind < 0:
			raise IndexError("Expected a positive index, instead got {}.".format(ind))
		return super(PositiveList, self).__getitem__(ind)
class GameBoard(PositiveList):
	def __init__(self, level):
		self.flags = []
		mine_setter = []
		mine_locations = []
		cell_counter = 0
		cells_total = level["base"] * level["heigth"]
		for y in range(level["heigth"]):
			self.append(PositiveList([]))
			for x in range(level["base"]):
				c = Cell({"x":x, "y":y}, "empty")
				self[y].append(c)
		for i in range(cells_total):
			if len(mine_setter) < level["mines"]:
				mine_setter.append(random.randint(0, cells_total))
		for y in range(level["heigth"]):
			for x in range(level["base"]):
				if cell_counter in mine_setter:
					cell_selected_type = "mine"
					mine_locations.append({"x":x, "y":y})
					self[x][y].setType("mine")
				else:
					cell_selected_type = "empty"
				cell_counter = cell_counter + 1
		for mine in mine_locations: # Set flags
			x = mine["x"]
			y = mine["y"]
			# print(f"mine: {x}, {y} <= {self[x][y].cell_type}")
			try:
				if self[x-1][y-1].cell_type != "mine":
					self[x-1][y-1].oneMineClose()
					self[x-1][y-1].setType("flag")
			except IndexError:
				pass
			try:
				if self[x][y-1].cell_type != "mine":
					self[x][y-1].oneMineClose()
					self[x][y-1].setType("flag")
			except IndexError:
				pass
			try:
				if self[x+1][y-1].cell_type != "mine":
					self[x+1][y-1].oneMineClose()
					self[x+1][y-1].setType("flag")
			except IndexError:
				pass
			try:
				if self[x-1][y].cell_type != "mine":
					self[x-1][y].oneMineClose()
					self[x-1][y].setType("flag")
			except IndexError:
				pass
			try:
				if self[x+1][y].cell_type != "mine":
					self[x+1][y].oneMineClose()
					self[x+1][y].setType("flag")
			except IndexError:
				pass
			try:
				if self[x-1][y+1].cell_type != "mine":
					self[x-1][y+1].oneMineClose()
					self[x-1][y+1].setType("flag")
			except IndexError:
				pass
			try:
				if self[x][y+1].cell_type != "mine":
					self[x][y+1].oneMineClose()
					self[x][y+1].setType("flag")
			except IndexError:
				pass
			try:
				if self[x+1][y+1].cell_type != "mine":
					self[x+1][y+1].oneMineClose()
					self[x+1][y+1].setType("flag")
			except IndexError:
				pass
		print(f"Set mine Total: {len(mine_locations)}")
		self.mine_locations = mine_locations
		self.first_movement = False
		self.clock = ClockThread()
	def showGameBoard(self):
		print("   ", end="")
		for y in range(len(self[0])):
			print(f"{bcolors.UNDERLINE}{bcolors.OKCYAN}{y:0=2d}{bcolors.ENDC}", end=" ")
		print()
		for x in range(len(self)):
			print(f"{bcolors.UNDERLINE}{bcolors.OKCYAN}{x:0=2d}{bcolors.ENDC}", end=" ")
			for y in range(len(self[0])):
				if self[x][y].cell_type == "mine":
					print(f"{bcolors.FAIL}x {bcolors.ENDC}", end=" ")
				elif self[x][y].cell_type == "flag":
					print(f"{self[x][y].mine_counter} ", end=" ")
				else:
					print("■ ", end=" ")
			print()
	def getSolvedGameBoard(self):
		string = "   "
		for y in range(len(self[0])):
			string += f"{bcolors.UNDERLINE}{bcolors.OKCYAN}{y:0=2d}{bcolors.ENDC} "
		string += "\n"
		for x in range(len(self)):
			string += f"{bcolors.UNDERLINE}{bcolors.OKCYAN}{x:0=2d}{bcolors.ENDC} "
			for y in range(len(self[0])):
				if self[x][y].cell_type == "mine":
					string += f"{bcolors.FAIL}x {bcolors.ENDC} "
				elif self[x][y].cell_type == "flag":
					string += f"{self[x][y].mine_counter}  "
				else:
					string += "■  "
			string += "\n"
		return string
	def printGameBoard(self):
		print("   ", end="")
		for y in range(len(self[0])):
			print(f"{bcolors.UNDERLINE}{bcolors.OKCYAN}{y:0=2d}{bcolors.ENDC}", end=" ")
		print()
		for x in range(len(self)):
			print(f"{bcolors.UNDERLINE}{bcolors.OKCYAN}{x:0=2d}{bcolors.ENDC}", end=" ")
			for y in range(len(self[0])):
				if not self[x][y].hidden and not self[x][y].flagged:
					if self[x][y].cell_type == "mine":
						print(f"{bcolors.FAIL}x {bcolors.ENDC}", end=" ")
					elif self[x][y].cell_type == "flag":
						print(f"{self[x][y].mine_counter} ", end=" ")
					else:
						print("■ ", end=" ")
				elif self[x][y].flagged:
					print(f"{bcolors.OKGREEN}x {bcolors.ENDC}", end=" ")
				else:
					print(f"{bcolors.OKBLUE}■ {bcolors.ENDC}", end=" ")
			print()
		print(f"\nMine total = {len(self.mine_locations)}")
		print(f"Cels flagged = {len(self.flags)}")
		print(f"{bcolors.UNDERLINE}Flags left = {len(self.mine_locations) - len(self.flags)}{bcolors.ENDC}")
	def getGameBoard(self):
		string = f"{bcolors.UNDERLINE}{bcolors.OKCYAN}MinesWeeper{bcolors.ENDC}\n\n"#Title
		string += "   "
		for y in range(len(self[0])):
			string += f"{bcolors.UNDERLINE}{bcolors.OKCYAN}{y:0=2d}{bcolors.ENDC} "
		string += "\n"
		for x in range(len(self)):
			string += f"{bcolors.UNDERLINE}{bcolors.OKCYAN}{x:0=2d}{bcolors.ENDC} "
			for y in range(len(self[0])):
				if not self[x][y].hidden and not self[x][y].flagged:
					if self[x][y].cell_type == "mine":
						string += f"{bcolors.FAIL}x {bcolors.ENDC} "
					elif self[x][y].cell_type == "flag":
						string += f"{self[x][y].mine_counter}  "
					else:
						string += "■  "
				elif self[x][y].flagged:
					string += f"{bcolors.OKGREEN}x {bcolors.ENDC} "
				else:
					string += f"{bcolors.OKBLUE}■ {bcolors.ENDC} "
			string += "\n"
		# Information
		string += f"\nMine total = {len(self.mine_locations)}\n"
		string += f"Cels flagged = {len(self.flags)}\n"
		string += f"{bcolors.UNDERLINE}Flags left = {len(self.mine_locations) - len(self.flags)}{bcolors.ENDC}\n"
		# Instructions
		string += f"\n{bcolors.OKCYAN}{bcolors.UNDERLINE}Input format: 'h' for hit and 'f' for flag a cell and 'u' for unflag {bcolors.ENDC}\n"
		string += f"{bcolors.OKCYAN}{bcolors.UNDERLINE}Example: h3, 2 {bcolors.ENDC}\n"
		return string
	def hitCell(self, x, y):
		# print(f"hitCell ({x}, {y})")
		flags = [False, False, False, False, False, False, False]
		self[x][y].setVisible()
		print(f"{bcolors.UNDERLINE}{bcolors.OKCYAN}MinesWeeper{bcolors.ENDC}")
		if not self.first_movement:
			self.startClock()
			self.first_movement = True
		if self[x][y].cell_type == "empty":
			for j in range(y+1): # Case above and behind
				for i in range(x+1):
					try:
						if not flags[0] and self[x-i][y].cell_type != "mine":
							self[x-i][y].setVisible()
						else:
							flags[0] = True
					except IndexError as e:
						# print(f"{bcolors.FAIL}[E] Out of range (1){bcolors.ENDC}")
						pass
					try:
						if not flags[1] and self[x][y-j].cell_type != "mine":
							self[x][y-j].setVisible()
						else:
							flags[1] = True
					except IndexError as e:
						# print(f"{bcolors.FAIL}[E] Out of range (2){bcolors.ENDC}")
						pass
					try:
						if not flags[2] and self[x-i][y-j].cell_type != "mine":
							# print(f"{x-i}, {y+j} => {i}, {j}")
							self[x-i][y-j].setVisible()
						else:
							flags[2] = True
					except IndexError as e:
						# print(f"{bcolors.FAIL}[E] Out of range (3){bcolors.ENDC}")
						pass
			for j in range(len(self)-y-1): # Below and forward
				for i in range(len(self[0])-x-1):
					try:
						if not flags[3] and self[x+i][y].cell_type != "mine":
							self[x+i][y].setVisible()
						else:
							flags[3] = True
					except IndexError as e:
						# print(f"{bcolors.FAIL}[E] Out of range (4){bcolors.ENDC}")
						pass
					try:
						if not flags[4] and self[x][y+j].cell_type != "mine":
							self[x][y+j].setVisible()
						else:
							flags[4] = True
					except IndexError as e:
						# print(f"{bcolors.FAIL}[E] Out of range (5){bcolors.ENDC}")
						pass
					try:
						if not flags[5] and self[x+i][y+j].cell_type != "mine":
							self[x+i][y+j].setVisible()
						else:
							flags[5] = True
					except IndexError as e:
						# print(f"{bcolors.FAIL}[E] Out of range (6){bcolors.ENDC}")
						pass
			for j in range(len(self)-y-1): # Below and behind
				for i in range(x):
					try:
						if not flags[6] and self[y-j][x+i].cell_type != "mine":
							self[y-j][x+i].setVisible()
						else:
							flags[6] = True
					except IndexError as e:
						# print(f"{bcolors.FAIL}[E] Out of range (7){bcolors.ENDC}")
						pass
		elif self[x][y].cell_type == "mine":
			return True
		return False
	def flagCell(self, x, y):
		print(f"flagCell ({x}, {y})")
		if not self.first_movement:
			self.startClock()
			self.first_movement = True
		self.flags.append({"x":x, "y":y})
		self[x][y].flagged = True
	def unflagCell(self, x, y):
		print(f"unflagCell ({x}, {y})")
		try:
			self[x][y].flagged = False
			if {"x":x, "y":y} in self.flags:
				for i in range(len(self.flags)):
					if self.flags[i]['x'] == x and self.flags[i]['y'] == y:
						del self.flags[i]
						break
		except ValueError as e:
			print(e)
			pass
	def startClock(self):
		self.clock.start()
	def stopClock(self):
		a = self.clock.stop()
		self.clock.join()
		return a
def players_thread(conn, id):
	global players_connection, first_player_connection, port_numbers
	port_numbers.append(conn.getpeername()[1])
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	if id == 0:
		first_player_connection.wait()
		players_ready[0].set()
		logging.debug(f"{bcolors.OKBLUE}First player ready in port: {conn.getpeername()[1]}{bcolors.ENDC}")
		#Select level
		select_level = f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKCYAN}Hi! You are player 1\n Please select level: \n1: Begginer\n2: Expert\n{bcolors.ENDC}"
		conn.sendall(str.encode(select_level))
	else:
		logging.debug(f"{bcolors.OKBLUE}Player {id + 1} ready in port: {conn.getpeername()[1]}{bcolors.ENDC}")
		ac = f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKCYAN}Hi! You are player {id + 1}\n{bcolors.ENDC}"
		conn.sendall(str.encode(ac))
		players_ready[id].wait()
	counter = 0
	while not gameover.isSet():
		time.sleep(1)
		turns[id].wait()
		logging.debug(f"Player {id + 1} turn")
		clear_turns(id)
		events = sel.select()
		key, mask = events[id]
		callback = key.data
		callback(key.fileobj, mask)
		if reply_from[id].isSet() and mask & selectors.EVENT_READ:
			# messages[id + 1] = f"{first_gameboard.getGameBoard()} Your turn"
			messages[id] = f"Update gameboard"
			turns[id].clear()
			reply_from[id].clear()
			counter += 1
			n = next_player(id)
			turns[n].set()
		else:
			messages[id] = f"{first_gameboard.getGameBoard()} Your turn {counter}"
	else:
		logging.debug(f"GAME ENDED GS: {gameover_string}")
		conn.sendall(str.encode(gameover_string))
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
	logging.debug(f"==> Level selected")
	for i, pr in enumerate(players_ready):
		pr.wait()
		logging.debug(f"Player {i + 1} ready!")
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
			target=players_thread,
			args=(conn,0)
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
	global level, level_selection, messages, port_numbers, players_ready, all_players_ready, selected_number, gameover_string
	player = port_numbers.index(conn.getpeername()[1])
	if mask & selectors.EVENT_READ:
		data = conn.recv(buffer_size)  # Should be ready
		if data:
			sdata = data.decode("utf-8")
			logging.debug(f"{bcolors.OKGREEN}Recieved from player {player + 1}: {sdata} {bcolors.ENDC}")
			if "level" in sdata:
				level = True
				m = re.search("\d", sdata)
				selected_number = int(m.group()) - 1 
				logging.debug(f"Replying...")
				conn.sendall(str.encode("First message from server for FIRST player"))
				level_selection.set()
			if f"I'm a player" in sdata:
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
				s  = re.match(r"(h|f|u) ?(\d+), ?(\d+)", sdata)
				if s is not None and len(s.groups()) == 3:
					cx, cy = map(int, s.groups()[1:])
					if s.groups()[0] == "f":
						first_gameboard.flagCell(cy,cx)
					elif s.groups()[0] == "u":
						first_gameboard.unflagCell(cy,cx)
					elif s.groups()[0] == "h":
						hit_a_mine = first_gameboard.hitCell(cy, cx)
						if hit_a_mine:
							gameover_string = f"\n{bcolors.FAIL}{first_gameboard.getSolvedGameBoard()}\nYou lose!\n Time:{first_gameboard.stopClock()}{bcolors.ENDC}\n"
							final = first_gameboard.getSolvedGameBoard()
							first_gameboard.showGameBoard()
							gameover.set()
					else:
						logging.debug("Incorrect input format")
						# conn.sendall(str.encode(first_gameboard.getGameBoard()+"\n401 Incorrect format\n"))
					# clear()
					first_gameboard.printGameBoard()
					first_gameboard.showGameBoard()
					# conn.sendall(str.encode(first_gameboard.getGameBoard()))
					print(f"Flags: {first_gameboard.flags}")
					print(f"Mines: {first_gameboard.mine_locations}")
					if len(first_gameboard.flags) == len(first_gameboard.mine_locations):
						coincidences = 0
						for i in first_gameboard.flags:
							if i in first_gameboard.mine_locations:
								coincidences = coincidences + 1
						if len(first_gameboard.mine_locations) == coincidences:
							win = True
							gameover_string = f"\n{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.HEADER}{first_gameboard.getSolvedGameBoard()}\nYou Win!!!\n Time: {first_gameboard.stopClock()} seconds{bcolors.ENDC}\n"
							gameover.set()
				elif "END_GAME" in sdata:
					gameover_string = f"\n{bcolors.FAIL}{bcolors.BOLD}GAME TERMINATED\n Time:{first_gameboard.stopClock()}{bcolors.ENDC}\n"
					final = first_gameboard.getSolvedGameBoard()
					first_gameboard.showGameBoard()
					gameover.set()
				else:
					logging.debug("Incorrect input format")
					cx = cy = None
				reply_from[player].set()
		else:
			logging.debug(f"Closing connection")
			sel.unregister(conn)
			conn.close()
	if mask & selectors.EVENT_WRITE:
		# logging.debug (f"Replying to PLAYER {player + 1}")
		if gameover.isSet():
			logging.debug (f"gameover_string: {gameover_string}")
			conn.sendall(str.encode(gameover_string))
		else:
			conn.sendall(str.encode(messages[player]))
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
		print("[E] Program usage: python server-minesweeper.py <CLIENTS>")
		exit()
	for c in range(CLIENTS):
		messages.append("\t")
		reply_from.append(threading.Event())
		turns.append(threading.Event())
		players_connection.append(threading.Event())
		players_ready.append(threading.Event())
	players_connection.pop()

	gameover_string = ""

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

	# Gameboard init
	level_selection.wait()
	selected_level = levels.begginer
	if selected_number == 1:
		selected_level = levels.expert
	logging.debug(f"Level selected: {bcolors.OKGREEN}{bcolors.BOLD}{selected_level['slug']}{bcolors.ENDC}")
	first_gameboard = GameBoard(selected_level)
	first_gameboard.showGameBoard()
	gi.join()
	sm.join()