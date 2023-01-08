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
	DIR *dp;
	struct dirent *ep;     
	short int i = 0, file_buffer_after = 0, file_buffer_before = 0;
	system("clear");
	while(1){
		printf("[I] Checking directory... %2d\n", i);
		printf("[I] There are: %d files\n", file_buffer_after = list_direcory());
		if(file_buffer_before == file_buffer_after)
			printf("[I] Not changed! :)\n");
		else{
			printf("[I] Changed! :)\n");
			file_buffer_before = file_buffer_after;
		}
		sleep(1);
		system("clear");
		i++;
	}
}
int list_direcory(){
	DIR *dp; // For directory
	struct dirent *ep; // Structure for listing directory
	struct stat buffer; // Buffer for file information
	int status, fildes; // File descriptor for file information
	int s = 0; // File counter
	dp = opendir ("./"); // Opening diretory
	if (dp != NULL){
		printf("\tFile name\tLast modified\n");
		while ((ep = readdir (dp)) != NULL){
			fildes = open(ep->d_name, O_RDWR); // Get file descriptor
			status = fstat(fildes, &buffer); // Get file information
			if(strcmp(ep->d_name, "..") && strcmp(ep->d_name, "."))
				printf("\t%s \t %s", ep->d_name, ctime(&buffer.st_mtime));
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
