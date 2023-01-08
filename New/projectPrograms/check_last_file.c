#include <stdio.h>      /* for printf() and fprintf() */
#include <stdlib.h>     /* for atoi() and exit() */
#include <string.h>     /* for memset() */
#include <unistd.h>     /* for close() */
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <time.h>
#include <dirent.h>

#define _XOPEN_SOURCE 700

int list_direcory();

int main(int argc, char *argv[]){
	// struct stat buffer;
	// int status, fildes;
	// fildes = open("./Notes.txt", O_RDWR);
	// status = fstat(fildes, &buffer);
	// puts("**Printigin in a file**");
	// printf("Access time  = %s\n", ctime(&buffer.st_mtime));
	DIR *dp;
	struct dirent *ep;     
	short int i = 0;
	system("clear");
	while(1){
		printf("[I] Checking directory... %2d\n", i);
		printf("[I] There are: %d files\n", list_direcory());
		sleep(1);
		system("clear");
		i++;
	}
}
int list_direcory(){
	DIR *dp;
	struct dirent *ep; 
	int s = 0;
	dp = opendir ("./");
	if (dp != NULL){
		while ((ep = readdir (dp)) != NULL){
			printf("File: %s\n", ep->d_name);
			s++;
		}
		(void) closedir (dp);
		return s;
	}
	else{
		perror ("Couldn't open the directory");
		return -1;
	}
}
