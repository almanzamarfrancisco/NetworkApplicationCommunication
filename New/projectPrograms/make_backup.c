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
#define USER "kali"
#define SERVER "192.168.1.20"
#define FILE_DESTINATION "/home/kali/Desktop/backup"

int list_direcory(char **);

int main(int argc, char *argv[]){
	DIR *dp;
	struct dirent *ep;     
	short int i = 0, file_buffer_after = 0, file_buffer_before = 0;
	char *last_modified_file_name = (char*)malloc(sizeof(char)*20);
	char *ssh_command = (char*)malloc(sizeof(char)*100);
	system("clear");
	while(1){
		printf("[I] Checking directory... %2d\n", i);
		file_buffer_after = list_direcory(&last_modified_file_name);
		printf("[I] There are: %d files\n", file_buffer_after);
		if(file_buffer_before == file_buffer_after)
			printf("[I] Not changed! :)\n");
		else{
			printf("[I] Changed! :)\n");
			file_buffer_before = file_buffer_after;
			sprintf(ssh_command, "scp %s %s@%s:%s", last_modified_file_name, USER, SERVER, FILE_DESTINATION);
			puts(ssh_command);
			if(system(ssh_command) < 0){
				perror("ssh_command failure to execute");
				exit(EXIT_FAILURE);
			}
			if(i>4)
				exit(1);
		}
		printf("Last modified name: %s\n", last_modified_file_name);
		sleep(1);
		system("clear");
		i++;
	}
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
