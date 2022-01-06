#!/usr/bin/env python3

import speech_recognition as sr
from os import system, name
import threading
import logging
import socket
import time
import sys
import re

HOST = "192.168.0.13"
PORT = 8080
PROMPT_LIMIT = 5
buffer_size = 8192
gameboard = ""
counter = 0
turn_gotten = threading.Event()
gameover = threading.Event()

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

logging.basicConfig(level=logging.DEBUG,format=f'{bcolors.OKCYAN}(%(threadName)-10s){bcolors.ENDC} %(message)s',)

def receive(sock_a):
	data = sock_a.recv(buffer_size)
	return str(data, errors='ignore')
def printer(sock_a):
	global gameboard
	logging.debug(f"Printer initialized")
	while not gameover.is_set():
		if "You lose!" in gameboard or "You Win!!" in gameboard:
			print(gameboard)
			exit()
		elif f"Your turn {counter}" in gameboard:
			clear()
			print(gameboard)
			gameboard.replace(f"Your turn {counter}", "")
			if not turn_gotten.is_set():
				turn_gotten.set()
				gameboard = ""
		elif "GAME TERMINATED" in gameboard:
			exit()
		if not turn_gotten.is_set():
			gameboard = receive(sock_a)
			# logging.debug(f"Gameboard: {gameboard}")
			clear()
			print(gameboard)
		time.sleep(1)
	else:
		print(gameboard)
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
def make_movement(sock_a):
	global turn_gotten, gameboard, counter
	while not gameover.is_set():
		logging.debug(f"Waiting for turn")
		turn_gotten.wait()
		logging.debug("Your question. Don't forget the question marker '?': ")
		# message = input()
		# if "?" not in message:
		# 	print(f"{bcolors.WARNING}You forgot the question marker! xD Write again please: {bcolors.ENDC}")
		# 	continue
		# create recognizer and mic instances
		recognizer = sr.Recognizer()
		microphone = sr.Microphone()
		for j in range(PROMPT_LIMIT):
			print(f"Ask your question: ")
			question = recognize_speech_from_mic(recognizer, microphone)
			if question["transcription"]:
				break
			if not question["success"]:
				break
			print(f"{bcolors.WARNING}I didn't catch that. What did you say?{bcolors.ENDC}")
		# if there was an error, stop the game
		if question["error"]:
			print(f"{bcolors.FAIL}ERROR: {question['error']}{bcolors.ENDC}")
			continue
		print(f"You said: {question['transcription']}")
		confirmation = input("Press ENTER if it is correct and type no if not: ")
		if confirmation.lower() == "no":
			continue
		question["transcription"] += "?"
		sock_a.sendall(str.encode(question['transcription']))
		turn_gotten.clear()
		counter += 1
		gameboard = ""
		time.sleep(1)
	else:
		print(gameboard)
if __name__ == '__main__':
	# if len(sys.argv) >= 3:
	# 	HOST = sys.argv[1]
	# 	PORT = sys.argv[2]
	# 	if int(PORT) < 1023:
	# 		print("[E] Port must be reather than 2024")
	# 		exit()
	# else:
	# 	print("[E] Program usage: python client-minesweeper.py [HOST] [PORT]")
	# 	exit()
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		first_message = ""
		s.connect((HOST, int(PORT)))
		clear()
		logging.debug("I'm tired braahh!")
		data = s.recv(buffer_size)
		sdata = data.decode("utf-8")
		if "Hi! You are player 1" in sdata:
			logging.debug(sdata)
			first_message = f"I'm first player"
		else:
			logging.debug(sdata)
			first_message = f"I'm a player"
		s.sendall(str.encode(first_message))
		data = s.recv(buffer_size)
		sdata = data.decode('utf-8')
		logging.debug(sdata)
		p = threading.Thread(
			name="Printer",
			target=printer,
			args=(s,)
		)
		p.start()
		m = threading.Thread(
			name="Input",
			target=make_movement,
			args=(s,)
		)
		m.start()
		m.join()
		p.join()
