#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <arpa/inet.h>

#define PORT            5000
#define QUEUE_SIZE      5
#define BUFFER_SIZE     100
#define EVER            1
#define IP_ADDRESS "127.0.0.1"

void *client_attender(void *arg);

struct settings {
   struct sockaddr_in client_address;
   int socket_file_descriptor;
   int client_struct_length;
   int local_client_id;
};

int main(int argc, char **argv){
	int *hilo, nhs[QUEUE_SIZE],nh=0, sockfd;
	pthread_t tids[QUEUE_SIZE];

	struct sockaddr_in server_address, client_address;
	struct settings *args, args_array[QUEUE_SIZE];
	int client_struct_length = sizeof(client_address);
	char message[BUFFER_SIZE];
	memset (&server_address, 0, sizeof (server_address));
	memset (&client_address, 0, sizeof (client_address)); 
	memset(message, '\0', sizeof(message));
	args = malloc(sizeof(struct settings));
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
	for(;EVER;){
		printf("[I] Listening for incoming messages...\n\n");
		if (recvfrom(sockfd, message, BUFFER_SIZE, 0,(struct sockaddr*)&client_address, &client_struct_length) < 0){
			perror("[E] Error to receive");
			exit(0);
		}
		printf("[I] Received message from IP: %s and port: %i\n", inet_ntoa(client_address.sin_addr), ntohs(client_address.sin_port));
		printf("=> Message from client: %s\n", message);
		if (sendto(sockfd, "Hello stranger! :)", 18, 0,(struct sockaddr*)&client_address, client_struct_length) < 0){
			perror("Can't send");
			exit(0);
		}
		(*args).client_address = client_address;
		(*args).socket_file_descriptor = sockfd;
		(*args).client_struct_length = client_struct_length;
		(*args).local_client_id = nh;
		args_array[nh] = *args;
		pthread_create(&tids[nh], NULL, client_attender, (void *)args);
		printf("==> 2nd Verification: %s and port: %i, nh: %d\n", inet_ntoa((args_array[nh]).client_address.sin_addr), ntohs((args_array[nh]).client_address.sin_port), (args_array[nh]).local_client_id);
		nh++;
	}
	for (nh = 0; nh < QUEUE_SIZE; nh++){
		pthread_join( tids[nh], (void **)&hilo );
		printf("Client %d has finished!\n", *hilo);
	}
	printf("[I] Server has finished! :) \n");
	close (sockfd);
	return 0;
}
void *client_attender(void *arguments){
	struct settings *args = (struct settings*)arguments;
	int sockfd = args->socket_file_descriptor;
	int client_struct_length = args->client_struct_length;
	char message[BUFFER_SIZE];
	memset(message, '\0', sizeof(message));
	for(;EVER;){
		// printf ("=> You: ");
		// fgets(message, BUFFER_SIZE, stdin);
		// if (sendto(sockfd, message, strlen(message), 0,(struct sockaddr*)&args->client_address, client_struct_length) < 0){
		// 	perror("Can't send");
		// 	exit(0);
		// }
		// if(!strcmp(message, "exit\n"))
		// 	break;
		printf("==> Verification: %s and port: %i, nh: %d\n", inet_ntoa(args->client_address.sin_addr), ntohs(args->client_address.sin_port), args->local_client_id);
		if (recvfrom(sockfd, message, BUFFER_SIZE, 0,(struct sockaddr*)&args->client_address, &client_struct_length) < 0){
			perror("[E] Error to receive");
			exit(0);
		}
		printf("=> Message from client from IP %s and port: %i\n: %s\n",inet_ntoa(args->client_address.sin_addr), ntohs(args->client_address.sin_port), message);
		if(!strcmp(message, "exit\n"))
			break;
		memset(message, 0, sizeof(message));
	}
}