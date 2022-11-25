#include <stdio.h>      /* for printf() and fprintf() */
#include <sys/socket.h> /* for socket() and bind() */
#include <arpa/inet.h>  /* for sockaddr_in */
#include <stdlib.h>     /* for atoi() and exit() */
#include <string.h>     /* for memset() */
#include <unistd.h>     /* for close() */

#define PORT            5000
#define BUFFER_SIZE     100
#define EVER            1
#define IP_ADDRESS "127.0.0.1"

void DieWithError(char *errorMessage);  /* External error handling function */

int main(int argc, char *argv[]){
	int sock;                         /* Socket */
	struct sockaddr_in broadcastAddr; /* Broadcast address */
	char *broadcastIP;                /* IP broadcast address */
	unsigned short broadcastPort;     /* Server port */
	char *sendString;                 /* String to broadcast */
	int broadcastPermission;          /* Socket opt to set permission to broadcast */
	unsigned int sendStringLen;       /* Length of string to broadcast */
	/* Create socket for sending/receiving datagrams */
	if ((sock = socket(PF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0)
		DieWithError("socket() failed");
	/* Set socket to allow broadcast */
	broadcastPermission = 1;
	if (setsockopt(sock, SOL_SOCKET, SO_BROADCAST, (void *) &broadcastPermission, 
		sizeof(broadcastPermission)) < 0)
		DieWithError("setsockopt() failed");
	/* Construct local address structure */
	memset(&broadcastAddr, 0, sizeof(broadcastAddr));   /* Zero out structure */
	broadcastAddr.sin_family = AF_INET;                 /* Internet address family */
	broadcastAddr.sin_addr.s_addr = inet_addr(IP_ADDRESS);/* Broadcast IP address */
	broadcastAddr.sin_port = htons(PORT);         /* Broadcast port */
	sendStringLen = strlen("Hi! I'm the server");  /* Find length of sendString */
	for (;EVER;){ /* Run forever */
		 /* Broadcast sendString in datagram to clients every 3 seconds*/
	if (sendto(sock, sendString, sendStringLen, 0, (struct sockaddr *) 
		&broadcastAddr, sizeof(broadcastAddr)) != sendStringLen)
		DieWithError("sendto() sent a different number of bytes than expected");
		sleep(1);   /* Avoids flooding the network */
}
	/* NOT REACHED */
}
void DieWithError(char *errorMessage){
	perror(errorMessage);
	exit(0);
}