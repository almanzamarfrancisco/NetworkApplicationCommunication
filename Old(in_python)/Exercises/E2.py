# Same as one but numbers of threads have to log sorted by id
import threading
import logging
import time
import sys
import math

def factorial(id, arg):
	logging.debug(f"Factorial result: {math.factorial(arg)}")

if __name__ == '__main__':
	args = []
	if len(sys.argv) >= 2:
		threads_number = int(sys.argv[1])
	else:
		print("[E] Program usage: python E1.py [NUMBER OF THREADS]")
		exit()
	logging.basicConfig(level=logging.DEBUG,format='(%(threadName)-10s) %(message)s',)
	# logging.debug(f"Threads number: {threads_number}")
	for n in range(threads_number):
		# logging.debug(f"{n}")
		number_string = input(f"Set {n} thread arg: ")
		args.append(int(number_string))
	for n in range(threads_number):
		t = threading.Thread(name=f"Threads {n}", target=factorial, args=(n,args[n],))
		t.start()