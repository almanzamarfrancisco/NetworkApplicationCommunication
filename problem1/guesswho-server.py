from os import system, name
import speech_recognition as sr
import threading
import selectors
import logging
import socket
import random
import json
import time
import re

buffer_size = 8192

sel = selectors.DefaultSelector()

first_player_connection = threading.Event()
gameover = threading.Event()

players_connection = []
players_ready = []
port_numbers = []
reply_from = []
messages = []
turns = []

character_names = []
characters = []
keywords = []


all_players_ready = False
level = False

selected_number = 0

first_gameboard = ""
gameover_string = ""

HOST = "192.168.0.13"
PORT = 8080
CLIENTS = 2
ATTEMPTS = 3
PROMPT_LIMIT = 5

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
	GRAY = '\u001b[38;5;240m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

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
class PlayerGameBoard():
	def __init__(self, characters):
		self.character_choosed = {}
		self.characters = characters.copy()
		self.clock = ClockThread()
		self.current_question = ""
		self.current_answer = ""
		# n = random.randint(0,len(characters))
		n = 14
		self.character_choosed = characters[n].copy()
		logging.debug(f"Choosed character: {bcolors.OKGREEN}{self.character_choosed['name']}{bcolors.ENDC}")
	def showGameBoard(self, cts):
		for i, c in enumerate(cts):
			if not i%8:
				print()
			if c in self.characters:
				print(f"{bcolors.OKCYAN}{bcolors.BOLD}{c['name'] : <10}{bcolors.ENDC}", end="")
			else:
				print(f"{bcolors.GRAY}{c['name'] : <10}{bcolors.ENDC}", end="")
		print()
		print(f"Current question: {self.current_question}")
		print(f"Current answer: {self.current_answer}")
	def getGameBoard(self, cts):
		s = ""
		for i, c in enumerate(cts):
			if not i%8:
				s += "\n"
			if c in self.characters:
				s += f"{bcolors.OKCYAN}{bcolors.BOLD}{c['name'] : <10}{bcolors.ENDC}"
			else:
				s += f"{bcolors.GRAY}{c['name'] : <10}{bcolors.ENDC}"
		s += "\n"
		s += f"Current question: {self.current_question}\n"
		s += f"Current answer: {self.current_answer}\n"
		s += "\n"
		return s
	def startClock(self):
		self.clock.start()
	def stopClock(self):
		a = self.clock.stop()
		self.clock.join()
		return a
def players_thread(conn, id):
	global first_player_connection, port_numbers, characters
	port_numbers.append(conn.getpeername()[1])
	sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	if id == 0:
		first_player_connection.wait()
		players_ready[0].set()
		logging.debug(f"{bcolors.OKBLUE}First player ready in port: {conn.getpeername()[1]}{bcolors.ENDC}")
		#Select level
		hello = f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKCYAN}Hi! You are player 1\n {bcolors.ENDC}"
		conn.sendall(str.encode(hello))
	else:
		logging.debug(f"{bcolors.OKBLUE}Player {id + 1} ready in port: {conn.getpeername()[1]}{bcolors.ENDC}")
		ac = f"{bcolors.BOLD}{bcolors.UNDERLINE}{bcolors.OKCYAN}Hi! You are player {id + 1}\n{bcolors.ENDC}"
		conn.sendall(str.encode(ac))
		players_ready[id].wait()
	counter = 0
	while not gameover.is_set():
		time.sleep(1)
		turns[id].wait()
		logging.debug(f"Player {id + 1} turn")
		clear_turns(id)
		events = sel.select()
		key, mask = events[id]
		callback = key.data
		callback(key.fileobj, mask)
		if reply_from[id].is_set() and mask & selectors.EVENT_READ:
			# messages[id + 1] = f"{first_gameboard.getGameBoard()} Your turn"
			messages[id] = f"Update gameboard"
			turns[id].clear()
			reply_from[id].clear()
			counter += 1
			n = next_player(id)
			turns[n].set()
		else:
			messages[id] = f"{first_gameboard.getGameBoard(characters)} Your turn {counter}"
	else:
		logging.debug(f"GAME ENDED: {gameover_string}")
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
		if not pc.is_set():
			return False
	return True
def recognize_speech_from_mic(recognizer, microphone):
	"""Transcribe speech from recorded from `microphone`.

	Returns a dictionary with three keys:
	"success": a boolean indicating whether or not the API request was
			   successful
	"error":   `None` if no error occured, otherwise a string containing
			   an error message if the API could not be reached or
			   speech was unrecognizable
	"transcription": `None` if speech could not be transcribed,
			   otherwise a string containing the transcribed text
	"""
	# check that recognizer and microphone arguments are appropriate type
	if not isinstance(recognizer, sr.Recognizer):
		raise TypeError("`recognizer` must be `Recognizer` instance")

	if not isinstance(microphone, sr.Microphone):
		raise TypeError("`microphone` must be `Microphone` instance")

	# adjust the recognizer sensitivity to ambient noise and record audio
	# from the microphone
	with microphone as source:
		recognizer.adjust_for_ambient_noise(source)
		audio = recognizer.listen(source)

	# set up the response object
	response = {
		"success": True,
		"error": None,
		"transcription": None
	}

	# try recognizing the speech in the recording
	# if a RequestError or UnknownValueError exception is caught,
	#     update the response object accordingly
	try:
		response["transcription"] = recognizer.recognize_google(audio)
	except sr.RequestError:
		# API was unreachable or unresponsive
		response["success"] = False
		response["error"] = "API unavailable"
	except sr.UnknownValueError:
		# speech was unintelligible
		response["error"] = "Unable to recognize speech"

	return response
def attempt_to_guess(name):
	global gameover_string
	if name == first_gameboard.character_choosed["name"]:
		print(f"{bcolors.OKGREEN}Yeah! You win!! :D Time: {first_gameboard.stopClock()}{bcolors.ENDC}")
		end_game = True
	else:
		ATTEMPTS -= 1
		if ATTEMPTS <= 0:
			gameover_string = f"{bcolors.FAIL}You lose!! xD Time:{first_gameboard.stopClock()}{bcolors.ENDC}"
			end_game = True
		else:
			print(f"{bcolors.WARNING}Nope! you have {ATTEMPTS} attemps:| {bcolors.ENDC}")
def get_keywords(s):
	global character_names
	keywords_asked = []
	for k in keywords:
		match = re.search(f" {k}", s) # There are cases that keywords are in Character names
		if bool(match) and k not in keywords_asked:
				keywords_asked.append(k)
	# Exception in male and female
	if "female" in keywords_asked and "male" in keywords_asked:
		keywords_asked.remove("male")
	if len(keywords_asked) == 0:
		name_found = False
		for cn in character_names:
			if cn in s:
				name_found = True
				attempt_to_guess(cn["name"])
		if not name_found:
			print(f"{bcolors.WARNING}I didn't catch that, try asking with the keywords suggested :){bcolors.ENDC}")
		return ""
	if len(keywords_asked) > 2:
		print(f"{bcolors.WARNING}I didn't catch that, try asking one feature at time :){bcolors.ENDC}")
		return ""
	logging.debug(f"keywords_asked: {keywords_asked}")
	return keywords_asked
def ask_question(question):
	global first_gameboard, characters
	# create recognizer and mic instances
	# recognizer = sr.Recognizer()
	# microphone = sr.Microphone()
	# while not gameover.is_set():
	# for j in range(PROMPT_LIMIT):
	# 	print(f"Ask your question: ")
	# 	question = recognize_speech_from_mic(recognizer, microphone)
	# 	if question["transcription"]:
	# 		break
	# 	if not question["success"]:
	# 		break
	# 	print(f"{bcolors.WARNING}I didn't catch that. What did you say?{bcolors.ENDC}")
	# # if there was an error, stop the game
	# if question["error"]:
	# 	print(f"{bcolors.FAIL}ERROR: {question['error']}{bcolors.ENDC}")
	# 	break
	# print(f"You said: {question['transcription']}")
	# confirmation = input("Press ENTER if it is correct and type no if not: ")
	# if confirmation.lower() == "no":
	# 	continue
	keywords_asked = get_keywords(question)
	# keywords = get_keywords(question['transcription'])

	# There are 2 types of features yes/no feature and specific feature
	feature = ""
	has_feature = False # This variable says if the choosed_character has the yes/no feature
	specific_feature = False # This variable says if a specific feature is asked
	has_specific_feature = False # This variable says if a specific feature is asked
	# logging.debug(f"Physical Characteristics you can ask for: {character_keys}")
	# logging.debug(f"Key words: {keywords}")
	first_gameboard.current_question = question
	# Discard characters
	for c_feature in characters[0].keys():
		for k in keywords_asked:
			if c_feature == k:
				logging.debug(f"{bcolors.WARNING}key_word: {k} and feature: {c_feature}{bcolors.ENDC}")
				feature = c_feature
				# Yes/no features
				if first_gameboard.character_choosed[c_feature] == "yes":
					logging.debug(f"{bcolors.OKGREEN}YES{bcolors.ENDC}")
					first_gameboard.current_answer = f"{bcolors.OKGREEN}YES{bcolors.ENDC}"
					has_feature = True
				elif first_gameboard.character_choosed[c_feature] == "no":
					logging.debug(f"{bcolors.OKGREEN}NO{bcolors.ENDC}")
					first_gameboard.current_answer = f"{bcolors.OKGREEN}NO{bcolors.ENDC}"
					has_feature = False
				# Specific feature
				else:
					specific_feature = True
					feature = keywords_asked[1]
					if first_gameboard.character_choosed[feature] == keywords_asked[0]:
						logging.debug(f"{bcolors.OKGREEN}YES{bcolors.ENDC}")
						first_gameboard.current_answer = f"{bcolors.OKGREEN}YES{bcolors.ENDC}"
						has_specific_feature = True
					else:
						logging.debug(f"{bcolors.OKGREEN}NO{bcolors.ENDC}")
						first_gameboard.current_answer = f"{bcolors.OKGREEN}NO{bcolors.ENDC}"
						has_specific_feature = False
	for c in first_gameboard.characters.copy():
		if has_feature and c[feature] == "no":
		 first_gameboard.characters.remove(c)
		elif not has_feature and c[feature] == "yes":
		 first_gameboard.characters.remove(c)
		elif specific_feature and has_specific_feature and c[feature] != keywords_asked[0]:
		 first_gameboard.characters.remove(c)
		elif specific_feature and not has_specific_feature and c[feature] == keywords_asked[0]:
		 first_gameboard.characters.remove(c)
	first_gameboard.showGameBoard(characters)
	has_feature = False # Reinit
	specific_feature = False # Reinit
	has_specific_feature = False # Reinit
def game_initializer():
	global first_player_connection, players_ready, characters, character_names, keywords, first_gameboard
	with open("characters.json") as f:
			characters = json.load(f)
	for i, c in enumerate(characters):
		ql = c.copy()
		ql.pop("name")
		for v in ql.values():
			if v not in keywords and "yes" not in v and "no" not in v:
				keywords.append(v)
	character_keys = list(characters[0].keys())
	character_names = [(c['name']) for c in characters]
	keywords += character_keys
	first_gameboard = PlayerGameBoard(characters)
	first_player_connection.wait()
	logging.debug(f"First player connected")
	for i, pr in enumerate(players_ready):
		pr.wait()
		logging.debug(f"Player {i + 1} ready!")
	logging.debug(f"All players ready!")
	
	first_gameboard.showGameBoard(characters)
	logging.debug(f"{bcolors.OKBLUE}We can start to play now!{bcolors.ENDC}")
	turns[0].set()
def accept(sock_a, mask):
	global first_player_connection, players_connection
	conn, addr = sock_a.accept()  # Should be ready
	logging.debug(f"Connected to {addr}")
	conn.setblocking(False)
	if not first_player_connection.is_set():
		fp = threading.Thread(
			name="first_player",
			target=players_thread,
			args=(conn,0)
		)
		fp.start()
		first_player_connection.set()
		return
	if first_player_connection.is_set() and not players_connection_ready():
		logging.debug(f"Waiting for other players")
		for i, pc in enumerate(players_connection):
			if not pc.is_set():
				pt = threading.Thread(
					name=f"Player {i + 2}",
					target=players_thread,
					args=(conn,i + 1)
				)
				pt.start()
				pc.set()
				return
def read_write(conn, mask):
	global messages, port_numbers, players_ready, all_players_ready, gameover_string, characters, first_gameboard
	player = port_numbers.index(conn.getpeername()[1])
	if mask & selectors.EVENT_READ:
		data = conn.recv(buffer_size)  # Should be ready
		if data:
			sdata = data.decode("utf-8")
			logging.debug(f"{bcolors.OKGREEN}Recieved from player {player + 1}: {sdata} {bcolors.ENDC}")
			if f"I'm first player" in sdata:
				first_gameboard.startClock()
			if f"I'm a player" in sdata:
				logging.debug(f"Replying...")
				conn.sendall(str.encode(f"Hi! You are player {player + 1}"))
				players_ready[player].set()
			for index, pr in enumerate(players_ready):
				if pr.is_set():
					all_players_ready = True
				else:
					all_players_ready = False
			if all_players_ready and "?" in sdata:
				ask_question(sdata)
				if "END_GAME" in sdata:
					gameover_string = f"\n{bcolors.FAIL}{bcolors.BOLD}GAME TERMINATED\n Time:{first_gameboard.stopClock()}{bcolors.ENDC}\n"
					gameover.set()
				reply_from[player].set()
		else:
			logging.debug(f"Closing connection")
			sel.unregister(conn)
			conn.close()
	if mask & selectors.EVENT_WRITE:
		# logging.debug (f"Replying to PLAYER {player + 1}")
		if gameover.is_set():
			logging.debug (f"gameover_string: {gameover_string}")
			conn.sendall(str.encode(gameover_string))
		else:
			conn.sendall(str.encode(messages[player]))
def connections_manager():
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
	# if len(sys.argv) >= 2:
	# 	CLIENTS = int(sys.argv[1])
	# else:
	# 	print("[E] Program usage: python guesswho.py <CLIENTS>")
	# 	exit()
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
			name="Connections Manager",
			target=connections_manager
		)
	gi.start()
	sm.start()

	gi.join()
	sm.join()