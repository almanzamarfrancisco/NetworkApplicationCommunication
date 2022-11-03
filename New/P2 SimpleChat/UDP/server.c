#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <arpa/inet.h>

#define PORT            5000
#define QUEUE           5
#define BUFFER_SIZE     100
#define EVER            1
#define IP_ADDRESS "127.0.0.1"

void * client_attender(void *arg);

int main(int argc, char **argv){
	// int *hilo, nhs[NUM_HILOS];
	// pthread_t tids[NUM_HILOS];
	// int *hilo, nh;
	// pthread_t tid;
	register int i = 0;
	int sockfd, client_sockfd;
	struct sockaddr_in server_address, client_address;
	char client_message[BUFFER_SIZE], server_message[BUFFER_SIZE];
	int client_struct_length = sizeof(client_address);
	memset (&server_address, 0, sizeof (server_address));   //se limpia la estructura con ceros
	memset (&server_address, 0, sizeof (client_address));   //se limpia la estructura con ceros
	server_address.sin_family = AF_INET;
    server_address.sin_port = htons(PORT);
    server_address.sin_addr.s_addr = inet_addr(IP_ADDRESS);
	printf("[I] Creating socket ....\n");
	if((sockfd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0 ){
		perror("[E] Error to create socket");
		exit(1);
	}
	printf("[I] Configuring socket ...\n");
	if(bind(sockfd, (struct sockaddr *) &server_address, sizeof(server_address)) < 0 ){
		perror ("[E] Error to configure socket");
		exit(1);
	}
	printf("[I] Listening for incoming messages...\n\n");
	if (recvfrom(sockfd, client_message, BUFFER_SIZE, 0,(struct sockaddr*)&client_address, &client_struct_length) < 0){
		perror("[E] Error to receive");
		exit(0);
	}
	printf("[I] Received message from IP: %s and port: %i\n", inet_ntoa(client_address.sin_addr), ntohs(client_address.sin_port));
	printf("=> Message from client: %s\n", client_message);
	if (sendto(sockfd, "Hello stranger! :)", 18, 0,(struct sockaddr*)&client_address, client_struct_length) < 0){
        perror("Can't send");
        exit(0);
    }
	// pthread_join( tid, (void **)&hilo );
	printf("[I] Server has finished! :) \n");
	close (sockfd);
	return 0;
}