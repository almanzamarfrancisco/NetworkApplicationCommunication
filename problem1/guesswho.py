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

bufferSize = 1024
PROMPT_LIMIT = 5

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
	GRAY = '\u001b[38;5;240m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

logging.basicConfig(level=logging.DEBUG,format=f'{bcolors.OKCYAN}(%(threadName)-10s){bcolors.ENDC} %(message)s',)

def show_game_board(rest):
	with open("characters.json") as f:
		characters = json.load(f)
	for i, c in enumerate(characters):
		if not i%8:
			print()
		if c in rest:
			print(f"{bcolors.OKCYAN}{bcolors.BOLD}{c['name'] : <10}{bcolors.ENDC}", end="")
		else:
			print(f"{bcolors.GRAY}{c['name'] : <10}{bcolors.ENDC}", end="")
	print()

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

if __name__ == '__main__':
	characters = []
	character_choosed = {}
	key_words = []
	end_game = False
	attempts = 3
	# There are 2 types of features yes/no feature and specific feature
	feature = ""
	has_feature = False # This variable says if the choosed_character has the yes/no feature
	specific_feature = False # This variable says if a specific feature is asked
	has_specific_feature = False # This variable says if a specific feature is asked
	with open("characters.json") as f:
		characters = json.load(f)
	# n = random.randint(0,len(characters))
	n = 14
	for i, c in enumerate(characters):
		if i == n:
			character_choosed = c.copy()
			logging.debug(f"Choosed character: {bcolors.OKGREEN}{c['name']}{bcolors.ENDC}")
		ql = c.copy()
		ql.pop("name")
		for v in ql.values():
			if v not in key_words and "yes" not in v and "no" not in v:
				key_words.append(v)
	character_keys = list(character_choosed.keys())
	character_names = [(c['name']) for c in characters]
	key_words += character_keys
	logging.debug(f"Physical Characteristics you can ask for: {character_keys}")
	logging.debug(f"Key words: {key_words}")
	show_game_board(characters)
	# create recognizer and mic instances
	recognizer = sr.Recognizer()
	microphone = sr.Microphone()
	while not end_game:
		# question = input("Ask your question: ")
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
			break
		print(f"You said: {question['transcription']}")
		confirmation = input("Press ENTER if it is correct and type no if not: ")
		if confirmation.lower() == "no":
			continue
		key_words_asked = []
		for k in key_words:
			match = re.search(f" {k}", question["transcription"]) # There are cases that keywords are in Character names
			if bool(match) and k not in key_words_asked:
					key_words_asked.append(k)
		# Exception in male and female
		if "female" in key_words_asked and "male" in key_words_asked:
			key_words_asked.remove("male")
		if len(key_words_asked) == 0:
			name_found = False
			for cn in character_names:
				if cn in question["transcription"]:
					name_found = True
					if cn == character_choosed["name"]:
						print(f"{bcolors.OKGREEN}Yeah! You win!! :D{bcolors.ENDC}")
						end_game = True
					else:
						attempts -= 1
						if attempts <= 0:
							print(f"{bcolors.FAIL}You lose!! xD{bcolors.ENDC}")
							end_game = True
						else:
							print(f"{bcolors.WARNING}Nope! you have {attempts} attemps:| {bcolors.ENDC}")
			if not name_found:
				print(f"{bcolors.WARNING}I didn't catch that, try asking with the keywords suggested :){bcolors.ENDC}")
			continue
		if len(key_words_asked) > 2:
			print(f"{bcolors.WARNING}I didn't catch that, try asking one feature at time :){bcolors.ENDC}")
			continue
		logging.debug(f"key_words_asked: {key_words_asked}")
		# Discard characters
		for c_feature in character_choosed.keys():
			for k in key_words_asked:
				if c_feature == k:
					logging.debug(f"{bcolors.WARNING}key_word: {k} and feature: {c_feature}{bcolors.ENDC}")
					feature = c_feature
					# Yes/no features
					if character_choosed[c_feature] == "yes":
						logging.debug(f"{bcolors.OKGREEN}YES{bcolors.ENDC}")
						has_feature = True
					elif character_choosed[c_feature] == "no":
						logging.debug(f"{bcolors.OKGREEN}NO{bcolors.ENDC}")
						has_feature = False
					# Specific feature
					else:
						specific_feature = True
						feature = key_words_asked[1]
						if character_choosed[feature] == key_words_asked[0]:
							logging.debug(f"{bcolors.OKGREEN}YES{bcolors.ENDC}")
							has_specific_feature = True
						else:
							logging.debug(f"{bcolors.OKGREEN}NO{bcolors.ENDC}")
							has_specific_feature = False
		# logging.debug(f"My character feature: {feature}::{character_choosed[feature]}")
		for c in characters.copy():
			# logging.debug(f"{c['name']}: c[{feature}] {c[feature]}, {has_feature and c[feature] == 'no'}")
			if has_feature and c[feature] == "no":
				# logging.debug(f"Discarting: {c['name']}")
				characters.remove(c)
			elif not has_feature and c[feature] == "yes":
				# logging.debug(f"Discarting: {c['name']}")
				characters.remove(c)
			elif specific_feature and has_specific_feature and c[feature] != key_words_asked[0]:
				# logging.debug(f"Discarting: {c['name']}")
				characters.remove(c)
			elif specific_feature and not has_specific_feature and c[feature] == key_words_asked[0]:
				# logging.debug(f"Discarting: {c['name']}")
				characters.remove(c)
		# if specific_feature:
		# 	logging.debug(f"==> {feature} is {character_choosed[feature]}")
		# else:
		# 	logging.debug(f"==> Has {feature}")
		show_game_board(characters)
		has_feature = False # Reinit
		specific_feature = False # Reinit
		has_specific_feature = False # Reinit