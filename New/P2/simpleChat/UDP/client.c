#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <pthread.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define PORT  			5000
#define BUFFER_SIZE 	100
#define EVER			1
#define IP_ADDRESS "127.0.0.1"
// #define IP_ADDRESS "192.168.100.10"

struct settings {
   struct sockaddr_in server_address;
   int socket_file_descriptor;
   int server_struct_length;
};

void *message_printer(void *arguments);

int main(int argc, char **argv){
	int sockfd;
	pthread_t tid;
	struct sockaddr_in server_address;
	char message[BUFFER_SIZE];
	int server_struct_length = sizeof(server_address);
	struct settings *args;
	memset(message, '\0', sizeof(message));
	memset (&server_address, 0, sizeof (server_address));
	args = malloc(sizeof(struct settings));
	if( inet_pton(AF_INET, IP_ADDRESS, &server_address.sin_addr) <= 0 ){
		perror("[E] Error to bind direction");
		exit(1);
	}
	printf("[I] Creating socket....\n");
	if( (sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0 ){
		perror("[E] Error to create socket");
		exit(1);
	}
	server_address.sin_family = AF_INET;
	server_address.sin_port = htons(PORT);
	server_address.sin_addr.s_addr = inet_addr("127.0.0.1");
	printf ("[I] Connecting ...\n");
	(*args).server_address = server_address;
	(*args).socket_file_descriptor = sockfd;
	(*args).server_struct_length = server_struct_length;
	pthread_create( &tid, NULL, message_printer, (void *)args );
	for(;EVER;){
		printf ("=> You: ");
		fgets(message, BUFFER_SIZE, stdin);
		if(sendto(sockfd, message, strlen(message), 0,(struct sockaddr*)&server_address, server_struct_length) < 0){
			perror("[E] Error to send the message to server");
			exit(1);
		}
		printf ("[I] Message sent successfully!\n");
		if(!strcmp(message, "exit\n"))
			break;
	}
	printf ("[I] Closing connection... \n");
	close(sockfd);
	pthread_join( tid, NULL);
	return 0;
}
void *message_printer(void *arguments){
	struct settings *args = (struct settings*)arguments;
	char message[BUFFER_SIZE];
	int sockfd = args->socket_file_descriptor;
	int server_struct_length = args->server_struct_length;
	for(;EVER;){
		if(recvfrom(sockfd, message, sizeof(message), 0,(struct sockaddr*)&args->server_address, &server_struct_length) < 0){
			perror("Error while receiving server's message\n");
			exit(0);
		}
		printf("=> Server's response: %s\n", message);
		memset(message, 0, sizeof(message));
	}
}