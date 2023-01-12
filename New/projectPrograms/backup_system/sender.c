#include <stdio.h>      /* for printf() and fprintf() */
#include <stdlib.h>     /* for atoi() and exit() */
#include <string.h>     /* for memset() */
#include <unistd.h>     /* for close() */
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <time.h>
#include <dirent.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>

#define _XOPEN_SOURCE 700
#define PORT            5000
#define QUEUE           5
#define BUFFER_SIZE     100
#define EVER            1
#define SIZE 1024
#define CLIENT_IPKALI "192.168.1.20"
#define CLIENT_IPONE "192.168.3.20"

int list_directory();
void * client_attender(void *arg);
void send_file(char *filename, FILE *fp, int sockfd);
void *listen_directory();
pthread_mutex_t lock;
int flag;
char *filename;

int main(int argc, char *argv[]){
	pthread_t tid[3];
	int sockfd, client_sockfd, thread_counter=0, flag=0;
	struct sockaddr_in server_address;
	memset (&server_address, 0, sizeof (server_address));
	filename = (char*)malloc(sizeof(char)*50);
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
	if (pthread_mutex_init(&lock, NULL) != 0) {
		perror("\n[E] Mutex init has failed\n");
		exit(1);
	}
	pthread_create( &tid[0], NULL, listen_directory, NULL );
	thread_counter++;
	for(;EVER;){
		printf ("Waiting connections ...\n");
		if( (client_sockfd = accept(sockfd, NULL, NULL)) < 0 ){
			perror("[E] Error to accept a client");
			exit(1);
		}
		if(thread_counter<=3){
			pthread_create( &tid[thread_counter], NULL, client_attender, (void *)&client_sockfd );
			thread_counter++;
		}
		else
			break;
	}
	printf ("====> Everybody is here...\n");
	for(int j=0;j<3;j++){
		pthread_join( tid[j], NULL );
	}
	pthread_mutex_destroy(&lock);
	printf("[I] Server has finished! :) \n");
	close (sockfd);
}
int list_direcory(char **lmfn){
	DIR *dp; // For directory
	struct dirent *ep; // Structure for listing directory
	struct stat buffer; // Buffer for file information
	int status, fildes; // File descriptor for file information
	int s = 0; // File counter
	time_t latest = 0;
	char *latest_name = (char*)malloc(sizeof(char)*20);
	dp = opendir ("./"); // Opening diretory
	if (dp != NULL){
		printf("\tFile name\tLast modified\n");
		while ((ep = readdir (dp)) != NULL){
			fildes = open(ep->d_name, O_RDWR); // Get file descriptor
			status = fstat(fildes, &buffer); // Get file information
			if(strcmp(ep->d_name, "..") && strcmp(ep->d_name, ".")){ // skip directories '.' and '..'
				printf("\t%s\t%s\n", ep->d_name, ctime(&buffer.st_mtime));
				if(buffer.st_mtime > latest){
					latest = buffer.st_mtime;
					strcpy(latest_name, ep->d_name);
				}
				s++;
			}
		}
		*lmfn = latest_name;
		printf("The lastes modified file is: %s \n", *lmfn);
		(void) closedir (dp);
		return s;
	}
	else{
		perror ("Couldn't open the directory");
		return -1;
	}
}
void *listen_directory(void *arg){
	DIR *dp;
	struct dirent *ep; 
	register int k=0;    
	short int i = 0, file_buffer_after = 0, file_buffer_before = 0;
	char *last_modified_file_name = (char*)malloc(sizeof(char)*20);
	// system("clear");
	for(;EVER;){
		// pthread_mutex_unlock(&lock);
		printf("[I] Checking directory... %2d\n", i);
		file_buffer_after = list_direcory(&last_modified_file_name);
		if(i==0)
			file_buffer_after = file_buffer_before;
		printf("[I] There are: %d files\n", file_buffer_after);
		if(file_buffer_before != file_buffer_after && i>file_buffer_after){
			printf("[I] Directory Changed! :)\n");
			file_buffer_before = file_buffer_after;
			strcpy(filename, last_modified_file_name);
			flag = 1;
		}
		else{
			printf("[I] Not changed! :)\n");
			flag = 0;
		}
		printf("\t[I] Last modified name: %s\n", last_modified_file_name);
		while(k--);
		// sleep(1);
		// pthread_mutex_lock(&lock);
		// system("clear");
		i++;
	}
	return last_modified_file_name;
}
void *client_attender(void *arg){
	FILE *fp;
	register int n=0;
	struct sockaddr_in addr;
	socklen_t addr_size = sizeof(struct sockaddr_in);
	char message[BUFFER_SIZE], clientip[20];
	int client_sockfd = *(int *)arg, k=0;
	getpeername(client_sockfd, (struct sockaddr *)&addr, &addr_size);
	struct sockaddr_in *s = (struct sockaddr_in *) &addr;
	inet_ntop(AF_INET, &s->sin_addr, clientip, sizeof clientip);
	printf("[I] A client has connected \n");
	if(read(client_sockfd, message, BUFFER_SIZE) < 0){
		perror ("[E] Error to receive data from client");
		exit(EXIT_FAILURE);
	}
	printf ("-> Client message: %s \n", message);
	for(;EVER;){
		printf ("-> Unlocking mutex:\n");
		pthread_mutex_unlock(&lock);
		if(flag){
			printf("=>> sendMessage('%s', %d)\n", clientip, ntohs(addr.sin_port));
			// strcat(filename, "././");
			printf("-> Getting file: %s... \n", filename);
			fp = fopen(filename, "r");
			if (fp == NULL) {
				perror("[E] Error in reading file");
				exit(1);
			}
			printf("[I] Sending file %s to client...\n", filename);
			send_file(filename, fp, client_sockfd);
			// sleep(1);
			while(n--);
		}
		printf("-> counter k: %d\n",k);
		k++;
		// sleep(1);
		while(n--);
		pthread_mutex_lock(&lock);
	}
	puts("[I] Closing client connection ...");
	close (client_sockfd);
}
void send_file(char* filename, FILE *fp, int sockfd){
	int n;
	struct stat st;
	char data[SIZE] = {0};
	printf("===========>>>>>>Send file funcion: %s\n", filename);
	stat(filename, &st);
	size_t size = st.st_size;
	printf("File size: ******** %zu Bytes\n", size);
	while(fgets(data, SIZE, fp) != NULL) {
		if (send(sockfd, data, sizeof(data), 0) == -1) {
			perror("[E] Error in sending file");
			exit(1);
		}
	}
	bzero(data, SIZE);
	printf("===========>>>>>>File sent: %s\n", filename);
	strcpy(data, "!END!");
	if (send(sockfd, data, sizeof(data), 0) == -1) {
		perror("[E] Error in sending messages");
		exit(1);
	}
	printf("===========>>>>>>Sent message: END\n");
}