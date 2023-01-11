all: receiver sender
clientmake: sender.c
	gcc -std=c99 -o sender sender.c
receivermake: receiver.c
	gcc -std=c99 -o receiver receiver.c
clean: 
	rm -rf sender receiver