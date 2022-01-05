from os import system, name
import threading
import selectors
import logging
import socket
import random
import json
import time

bufferSize = 1024

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

if __name__ == '__main__':
	characters = []
	character_choosed = {}
	key_words = []
	end_game = False
	a = False
	with open("characters.json") as f:
		characters = json.load(f)
	n = random.randint(0,len(characters))
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
	key_words += character_keys
	logging.debug(f"Physical Characteristics you can ask for: {character_keys}")
	logging.debug(f"Key words: {key_words}")
	while not end_game:
		question = input(f"Ask your question: ")
		key_words_asked = []
		for i, k in enumerate(key_words):
			if k in question:
				# logging.debug(f"You ask for: {k}")
				if k not in key_words_asked:
					key_words_asked.append(k)
		if "female" in key_words_asked:
			key_words_asked.remove('male')
		logging.debug(f"key_words_asked: {key_words_asked}")
		# Discard characters
		aa = ""
		for ck in character_choosed.keys():
			for k in key_words_asked:
				if ck == k:
					logging.debug(f"{bcolors.WARNING}key_word: {k} and dic key: {ck}{bcolors.ENDC}")
					aa = ck
					if character_choosed[ck] == "yes":
						logging.debug(f"Yes")
						a = True
					else:
						logging.debug(f"No")
						a = False
		# for v in character_choosed.values():
		# 	for k in key_words_asked:
		# 		if v == k:
		# 			logging.debug(f"{bcolors.WARNING}key_word: {k} and value: {v}{bcolors.ENDC}")
		for i, c in enumerate(characters):
			if a and c[aa] == "no":
				logging.debug(f"Discarting: {c['name']}")
				del characters[i]
			elif not a and c[aa] == "yes":
				logging.debug(f"Discarting: {c['name']}")
				del characters[i]
		for c in characters:
			logging.debug(c)