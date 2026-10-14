/* Test-only transport of actual ELF MMIO to actual RTL. No rule on host. */
#include <sys/socket.h>
#include <sys/un.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static int stream=-1;
const char *system_folder(void) { return getenv("T106_RUN"); }
static void connect_once(void) {
    if(stream>=0) return;
    const char *name=getenv("T106_SOCKET");
    if(!name || strlen(name)>=sizeof(((struct sockaddr_un *)0)->sun_path)) abort();
    int fd=socket(AF_UNIX,SOCK_STREAM,0);
    struct sockaddr_un a={.sun_family=AF_UNIX};strcpy(a.sun_path,name);
    if(fd<0 || connect(fd,(struct sockaddr *)&a,sizeof(a))) {perror("T106 connect");abort();}
    stream=fd;
}
void system_next(int *op,int *addr,int *value,int *delay) {
    connect_once();unsigned o,a,v,d;
    char line[128];unsigned n=0;
    do {
        if(n+1>=sizeof(line) || recv(stream,line+n,1,0)!=1) abort();
    } while(line[n++]!='\n');
    line[n]=0;
    if(sscanf(line,"%u %x %x %u",&o,&a,&v,&d)!=4) abort();
    *op=o;*addr=a;*value=v;*delay=d;
}
void system_reply(int response,int value,int tick) {
    char line[128];int length=snprintf(line,sizeof(line),"%u %08x %u\n",response,(unsigned)value,(unsigned)tick);
    for(int n=0;n<length;) {
        int wrote=send(stream,line+n,length-n,MSG_NOSIGNAL);
        if(wrote<=0) {perror("T106 reply");abort();}
        n+=wrote;
    }
}
