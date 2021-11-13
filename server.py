#!/usr/bin/env python3

import sys
import socket
import selectors
import types
import logging
import time

logging.basicConfig(level=logging.DEBUG,format='(%(threadName)-10s) %(message)s',)
sel = selectors.DefaultSelector()

HOST = "192.168.1.125"
PORT = 8080

def accept(sock_a, mask):
	sock_conn, addr = sock_a.accept()  # Should be ready
	logging.debug(f'aceptado {sock_conn}, de {addr}')
	sock_conn.setblocking(False)
	time.sleep(3)
	sel.register(sock_conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)
	#sel.register(sock_conn,selectors.EVENT_WRITE, read_write)

def read_write(sock_c, mask):
	if mask & selectors.EVENT_READ:
		data = sock_c.recv(1024)  # Should be ready
		if data:
			logging.debug(f'recibido{repr(data)} a {sock_c}')
			logging.debug(f'respondiendo {repr(data)}, a {sock_c}')
			# sock_c.sendall(str.encode("Alllllvvvvvvvv"))  # Hope it won't block
		else:
			logging.debug('cerrando {sock_c}')
			sel.unregister(sock_c)
			sock_c.close()
	if mask & selectors.EVENT_WRITE:
		logging.debug ("enviando datos")
		sock_c.sendall(str.encode("SELECTOR EVENT_WRITE"))  # Hope it won't block
		logging.debug("Selector EVENT_WRITE")
		time.sleep(3)

if __name__ == '__main__':
	with socket.socket() as sock_accept:
		sock_accept.bind((HOST, PORT))
		sock_accept.listen(100)
		sock_accept.setblocking(False)
		sel.register(sock_accept, selectors.EVENT_READ, accept)
		while True:
			logging.debug("Esperando evento...")
			events = sel.select()
			# logging.debug(events)
			for key, mask in events:
				callback = key.data
				callback(key.fileobj, mask)
