from os import system, name
import threading
import logging
import socket

HOST = "192.168.0.13"
PORT = 8080
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
	connection_to = (HOST, PORT)
	with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
		message = "Hello UDP Server"
		bytesToSend = str.encode(message)
		s.sendto(bytesToSend, connection_to)
		message_received = s.recvfrom(bufferSize)
		logging.debug(f"Message from Server {message_received[0]}")