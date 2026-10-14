/* Test-only blocking bridge. It transfers actual ARM MMIO to RTL, not C rule results. */
#include <vpi_user.h>
#include <stdio.h>
#include <stdlib.h>
static PLI_INT32 next(PLI_BYTE8 *unused) {
    (void)unused; unsigned op,addr,data,delay;
    if(scanf("%u %x %x %u",&op,&addr,&data,&delay)!=4) {
        vpi_printf("BRIDGE_EOF\n");vpi_control(vpiFinish,1);return 0;
    }
    unsigned values[4]={op,addr,data,delay};
    vpiHandle args=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));
    for(unsigned i=0;i<4;i++) {
        s_vpi_value v={.format=vpiIntVal};v.value.integer=(int)values[i];
        vpi_put_value(vpi_scan(args),&v,0,vpiNoDelay);
    }
    return 0;
}
static PLI_INT32 reply(PLI_BYTE8 *unused) {
    (void)unused;unsigned values[3];
    vpiHandle args=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,0));
    for(unsigned i=0;i<3;i++) {
        s_vpi_value v={.format=vpiIntVal};vpi_get_value(vpi_scan(args),&v);
        values[i]=(unsigned)v.value.integer;
    }
    printf("ISA_REPLY %u %08x %u\n",values[0],values[1],values[2]);fflush(stdout);
    return 0;
}
static void register_bridge(void) {
    s_vpi_systf_data a={.type=vpiSysTask,.tfname="$isa_next",.calltf=next};vpi_register_systf(&a);
    s_vpi_systf_data b={.type=vpiSysTask,.tfname="$isa_reply",.calltf=reply};vpi_register_systf(&b);
}
void (*vlog_startup_routines[])(void)={register_bridge,0};
