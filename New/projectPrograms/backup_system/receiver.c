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
#define SIZE 1024

int main(int argc, char **argv){
	int sockfd, i=0, n=0, counter=0;

	FILE *fp;
	char *filename = (char*)malloc(sizeof(char)*50);
	char buffer[SIZE];

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
	if( connect(sockfd, (struct sockaddr *)&server_address, sizeof(server_address) ) < 0){
		perror ("[E] Error to connect");
		exit(1);
	}
	printf ("Sending a message ...\n");
	if( write(sockfd, "I'm the client :)", 15) < 0 ){
		perror("[E] Error to send the message to server");
		exit(1);
	}
	printf ("[I] Waiting for reply ...\n");
	for(;EVER;){
		printf("=> Counter: %d\n", counter);
		// write_file(i, sockfd);
		printf("Writing file baby... \n");
		sprintf(filename, "./received/%drecv%d.txt", ntohs(server_address.sin_port), counter);
		fp = fopen(filename, "w");
		while (1) {
			n = recv(sockfd, buffer, SIZE, 0);
			if (n <= 0){
				break;
				// return;
			}
			printf(".");
			fprintf(fp, "%s", buffer);
			bzero(buffer, SIZE);
		}
		puts("File gotten! :)");
		counter++;
	}
	printf ("Closing connection... \n");
	close(sockfd);
	return 0;
}
