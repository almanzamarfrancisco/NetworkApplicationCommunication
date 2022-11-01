#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>

#define PORT            5000
#define QUEUE           5
#define BUFFER_SIZE     100
#define EVER            1


int main(int argc, char **argv)
{
    // pid_t pid;
    int sockfd, client_sockfd;
    struct sockaddr_in server_address;
    char message[BUFFER_SIZE];
    memset (&server_address, 0, sizeof (server_address));   //se limpia la estructura con ceros
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
        // pid = fork();
        // if( !pid ){
            printf("A client has connected \n");
            if( read (client_sockfd, message, BUFFER_SIZE) < 0 ){
                perror ("[E] Error to receive data from client");
                exit(EXIT_FAILURE);
            }
            printf ("Client message: \n %s \n", message);
            puts("Sending a message to client ...");
            if( write (client_sockfd, "Welcome stranger!", 17) < 0 ){
                perror("");
                exit(EXIT_FAILURE);
            }
            close (client_sockfd);
            exit(0);
        // }
    }
    printf("Server has finished! :) \n");
    close (sockfd);

    return 0;
}

