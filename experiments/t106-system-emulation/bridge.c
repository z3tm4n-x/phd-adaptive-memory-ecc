/* Test-only transport of actual ELF MMIO to actual RTL. No rule on host. */
#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static FILE *stream;
const char *system_folder(void) { return getenv("T106_RUN"); }
static void connect_once(void) {
    if(stream) return;
    const char *name=getenv("T106_SOCKET");
    if(!name || strlen(name)>=sizeof(((struct sockaddr_un *)0)->sun_path)) abort();
    int fd=socket(AF_UNIX,SOCK_STREAM,0);
    struct sockaddr_un a={.sun_family=AF_UNIX};strcpy(a.sun_path,name);
    if(fd<0 || connect(fd,(struct sockaddr *)&a,sizeof(a))) {perror("T106 connect");abort();}
    stream=fdopen(fd,"r+");if(!stream) abort();
    setvbuf(stream,0,_IONBF,0);
}
void system_next(int *op,int *addr,int *value,int *delay) {
    connect_once();unsigned o,a,v,d;
    if(fscanf(stream,"%u %x %x %u",&o,&a,&v,&d)!=4) abort();
    *op=o;*addr=a;*value=v;*delay=d;
}
void system_reply(int response,int value,int tick) {
    if(fprintf(stream,"%u %08x %u\n",response,(unsigned)value,(unsigned)tick)<0) abort();
}
