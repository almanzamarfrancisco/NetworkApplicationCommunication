#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define PORT  			5000
#define BUFFER_SIZE 	100
#define EVER			1
#define DIR_IP "127.0.0.1"
// #define DIR_IP "192.168.100.10"

int main(int argc, char **argv){
	int sockfd;
	struct sockaddr_in server_address;
	char message[BUFFER_SIZE];
	memset (&server_address, 0, sizeof (server_address));
	server_address.sin_family = AF_INET;
	server_address.sin_port = htons(PORT );
	if( inet_pton(AF_INET, DIR_IP, &server_address.sin_addr) <= 0 ){
		perror("[E] Error to bind direction");
		exit(1);
	}
	printf("[I] Creating socket....\n");
	if( (sockfd = socket (AF_INET, SOCK_STREAM, 0)) < 0 ){
		perror("[E] Error to create socket");
		exit(1);
	}
	printf ("[I] Connecting ...\n");
	if( connect(sockfd, (struct sockaddr *)&server_address, sizeof(server_address) ) < 0) 
	{
		perror ("[E] Error to connect");
		exit(1);
	}
	printf ("Sending a message ...\n");
	if( write(sockfd, "I'm the client :)", 15) < 0 ){
		perror("[E] Error to send the message to server");
		exit(1);
	}
	for(;EVER;){
		printf ("[I] Waiting for reply ...\n");
		if (read (sockfd, message, 100) < 0){	
			perror ("[E] Error to receive data from client");
			exit(1);
		}
		printf ("-> Server message: %s\n", message);
		if(!strcmp(message, "exit\n"))
			break;
		memset(message, 0, sizeof(message));
		printf ("=> You: ");
		fgets(message, BUFFER_SIZE, stdin);
		if( write(sockfd, message, strlen(message)) < 0 ){
			perror("[E] Error to send the message to server");
			exit(1);
		}
	}
	printf ("Closing connection... \n");
	close(sockfd);
	return 0;
}
	
