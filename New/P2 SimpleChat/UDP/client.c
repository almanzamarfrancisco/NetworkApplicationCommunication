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
#define IP_ADDRESS "127.0.0.1"
// #define IP_ADDRESS "192.168.100.10"

int main(int argc, char **argv){
	int sockfd;
	register int i = 0;
	struct sockaddr_in server_address;
	char client_message[BUFFER_SIZE], server_message[BUFFER_SIZE];
	int server_struct_length = sizeof(server_address);
	memset(server_message, '\0', sizeof(server_message));
    memset(client_message, '\0', sizeof(client_message));
	memset (&server_address, 0, sizeof (server_address));
	
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
	if(sendto(sockfd, "I'm the client :)", 15, 0,(struct sockaddr*)&server_address, server_struct_length) < 0){
		perror("[E] Error to send the message to server");
		exit(1);
	}
	printf ("[I] Message sent successfully!\n");
	if(recvfrom(sockfd, server_message, sizeof(server_message), 0,(struct sockaddr*)&server_address, &server_struct_length) < 0){
        perror("Error while receiving server's message\n");
        exit(0);
    }
	printf("=> Server's response: %s\n", server_message);
	printf ("[I] Closing connection... \n");
	close(sockfd);
	return 0;
}
	
