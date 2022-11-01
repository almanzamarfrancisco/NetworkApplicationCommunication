# User choose the number or threads that 
# the program will generate and its factorial number to calculate
import threading
import logging
import time
import sys

def factorial(n):
	if n > 1:
		return n*factorial(n-1)
	else:
		return n
def threadFunction(num):
	time.sleep(num*0.1)
	logging.debug(f"{factorial(num)}")

if __name__ == '__main__':
	if len(sys.argv) >= 2:
		threads_number = int(sys.argv[1])
	else:
		print("[E] Program usage: python E1.py [NUMBER OF THREADS] [args...]")
		exit()
	logging.basicConfig(level=logging.DEBUG,format='(%(threadName)-10s) %(message)s',)
	# logging.debug(f"Threads number: {threads_number}")
	thread_list = []
	for n in range(threads_number):
		number = int(sys.argv[n+2])
		thread_list.append(threading.Thread(name=f"Thread {n}", target=threadFunction, args=(number,)))
	for n in range(threads_number):
		thread_list[n].start()