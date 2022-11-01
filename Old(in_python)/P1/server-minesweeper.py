#!/usr/bin/env python3

from os import system, name
from threading import Thread,Event
import random
import signal
import socket
import ctypes
import time
import sys
import re

buffer_size = 8192

class levels():
	# Begginer 9x9  => 10 mines
	# Intermediate 16x16 => 40 mines
	# Expert 30x16 => 99 mines
	begginer = {
		"base": 9,
		"heigth": 9,
		"mines": 2,
	}
	expert = {
		"base": 16,
		"heigth": 16,
		"mines": 40,
	}
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
class ClockThread(Thread):
	def __init__(self, event, start_time):
		Thread.__init__(self)
		self.stopped = event
		self.time = start_time
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

if __name__ == '__main__':	
	# HOST = "192.168.0.10"
	# PORT = 6061
	if len(sys.argv) >= 3:
		HOST = sys.argv[1]
		PORT = sys.argv[2]
		if int(PORT) < 1023:
			print("[E] Port must be reather than 2024")
			exit()
		PORT = int(PORT)
	else:
		print("[E] Program usage: python client-minesweeper.py [HOST] [PORT]")
		exit()
	gameover_string = ""
	# Socket init
	tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp_socket.bind((HOST, PORT))
	tcp_socket.listen()
	print("[I] Listening... ")
	# Connection accept
	conn, addr = tcp_socket.accept()
	print("Conectado a", addr)
	#Select level
	select_level = f"\n{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKCYAN}Select level: \n1: Begginer\n2: Expert\n{bcolors.ENDC}"
	conn.sendall(str.encode(select_level))
	data = conn.recv(buffer_size)
	selected_number = int(data.decode()) - 1 
	if selected_number == 0:
		selected_level = levels.begginer
	elif selected_number == 1:
		selected_level = levels.expert
	# Gameboard init
	first_gameboard = GameBoard(selected_level)
	first_gameboard.showGameBoard()

	stopFlag = Event()
	clock = ClockThread(stopFlag, 0)
	clock.start()

	while True:	
		data = conn.recv(buffer_size)
		if not data:
			break
		movement = data.decode("utf-8")
		s  = re.match(r"(h|f|u) ?(\d+), ?(\d+)", movement)
		if s is not None and len(s.groups()) == 3:
			cx, cy = map(int, s.groups()[1:])
			if s.groups()[0] == "f":
				first_gameboard.flagCell(cy,cx)
			elif s.groups()[0] == "u":
				first_gameboard.unflagCell(cy,cx)
			elif s.groups()[0] == "h":
				hit_a_mine = first_gameboard.hitCell(cy, cx)
				if hit_a_mine:
					gameover_string = f"\n{bcolors.FAIL}You lose!{bcolors.ENDC}\n"
					final = first_gameboard.getSolvedGameBoard()
					first_gameboard.showGameBoard()
					break
			else:
				print("Incorrect input format")
				conn.sendall(str.encode(first_gameboard.getGameBoard()+"\n401 Incorrect format\n"))
			clear()
			first_gameboard.printGameBoard()
			first_gameboard.showGameBoard()
			conn.sendall(str.encode(first_gameboard.getGameBoard()))
			print(f"Flags: {first_gameboard.flags}")
			print(f"Mines: {first_gameboard.mine_locations}")
			if len(first_gameboard.flags) == len(first_gameboard.mine_locations):
				coincidences = 0
				for i in first_gameboard.flags:
					if i in first_gameboard.mine_locations:
						coincidences = coincidences + 1
				if len(first_gameboard.mine_locations) == coincidences:
					win = True
					gameover_string = f"\n{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.HEADER}You Win!!!{bcolors.ENDC}\n"
					break
		else:
			if movement == "Gameboard request":
				conn.sendall(str.encode(first_gameboard.getGameBoard()))
				continue
			print("Incorrect input format")
			conn.sendall(str.encode(first_gameboard.getGameBoard()+"\n401 Incorrect format\n"))
			data = None
			action = cx = cy = None
	final = first_gameboard.getSolvedGameBoard()
	# this will stop the timer
	stopFlag.set()
	print(f" ======> Clock: {clock.string}")
	conn.sendall(str.encode(final + gameover_string + f"\n{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKCYAN}=> Time: {clock.string}{bcolors.ENDC}"))
	tcp_socket.close()