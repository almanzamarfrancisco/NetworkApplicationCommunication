#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <sys/stat.h>

#define PORT            5000
#define QUEUE           5
#define BUFFER_SIZE     100
#define EVER            1
#define SIZE 1024

void * client_attender(void *arg);
void send_file(FILE *fp, int sockfd);
int main(int argc, char **argv){
	// int *hilo, nhs[NUM_HILOS];
	// pthread_t tids[NUM_HILOS];
	int *hilo, nh;
	pthread_t tid;
	int sockfd, client_sockfd;
	struct sockaddr_in server_address;
	memset (&server_address, 0, sizeof (server_address));
	server_address.sin_family       = AF_INET;
	server_address.sin_port         = htons(PORT);
	server_address.sin_addr.s_addr  = INADDR_ANY;
	printf("[I] Creating socket ....\n");
	if( (sockfd = socket (AF_INET, SOCK_STREAM, 0)) < 0 ){
		perror("[E] Error to create socket");
		exit(1);
	}
	printf("Configuring socket ...\n");
	if( bind(sockfd, (struct sockaddr *) &server_address, sizeof(server_address)) < 0 ){
		perror ("[E] Error to configure socket");
		exit(1);
	}
	printf ("[E] Establishing QUEUE...\n");
	if( listen(sockfd, QUEUE) < 0 ){
		perror("[E] Error to establish queue");
		exit(1);
	}
	for(;EVER;){
		printf ("Waiting connections ...\n");
		if( (client_sockfd = accept(sockfd, NULL, NULL)) < 0 ){
			perror("[E] Error to accept a client");
			exit(1);
		}
		pthread_create( &tid, NULL, client_attender, (void *)&client_sockfd );
	}
	pthread_join( tid, (void **)&hilo );
	printf("[I] Server has finished! :) \n");
	close (sockfd);
	
	return 0;
}

void *client_attender(void *arg){
	char message[BUFFER_SIZE];
	int client_sockfd = *(int *)arg;
	char *filename = "test.txt";
	FILE *fp;
	printf("[I] A client has connected \n");
	if(read(client_sockfd, message, BUFFER_SIZE) < 0){
		perror ("[E] Error to receive data from client");
		exit(EXIT_FAILURE);
	}
	printf ("-> Client message: %s \n", message);
	puts("[I] Sending a message to client ...");
	if( write (client_sockfd, "Welcome stranger!", 17) < 0 ){
		perror("[E] Error to send menssage to client");
		exit(EXIT_FAILURE);
	}
	memset(message, 0, sizeof(message));
	printf("=>>>>>>>Client said it want the file!\n");
	fp = fopen(filename, "r");
	if (fp == NULL) {
		perror("[E] Error in reading file.");
		exit(1);
	}
	send_file(fp, client_sockfd);
	puts("[I] Closing client connection ...");
	close (client_sockfd);
}
void send_file(FILE *fp, int sockfd){
	int n;
	char data[SIZE] = {0};
	struct stat st;
	stat("test.txt", &st);
	size_t size = st.st_size;
	printf("Size: %zu", size);
	while(fgets(data, SIZE, fp) != NULL) {
		if (send(sockfd, data, sizeof(data), 0) == -1) {
			perror("[E] Error in sending file.");
			exit(1);
		}
		bzero(data, SIZE);
	}
}