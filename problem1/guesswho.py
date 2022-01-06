from os import system, name
import threading
import selectors
import logging
import socket
import random
import json
import time
import re

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
	attempts = 3
	# There are 2 types of features yes/no feature and specific feature
	feature = ""
	has_feature = False # This variable says if the choosed_character has the yes/no feature
	specific_feature = False # This variable says if a specific feature is asked
	has_specific_feature = False # This variable says if a specific feature is asked
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
	character_names = [(c['name']) for c in characters]
	key_words += character_keys
	logging.debug(f"Physical Characteristics you can ask for: {character_keys}")
	logging.debug(f"Key words: {key_words}")
	while not end_game:
		question = input(f"Ask your question: ")
		key_words_asked = []
		for k in key_words:
			match = re.search(f" {k}", question) # There are cases that keywords are in Character names
			if bool(match) and k not in key_words_asked:
					key_words_asked.append(k)
		# Exception in male and female
		if "female" in key_words_asked and "male" in key_words_asked:
			key_words_asked.remove("male")
		if len(key_words_asked) == 0:
			name_found = False
			for cn in character_names:
				if cn in question:
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
		for c in characters:
			logging.debug(f"{c['name']}: {c[feature]}")
	has_feature = False # Reinit
	specific_feature = False # Reinit
	has_specific_feature = False # Reinit