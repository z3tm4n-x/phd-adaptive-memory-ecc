/* Functional native-C/RTL bridge. NOT an ARM timing or PS7 model. */
#include <vpi_user.h>
#include "batch.h"
static t105_batch_state state;
static PLI_INT32 calculate(PLI_BYTE8 *unused) {
    (void)unused;
    vpiHandle call=vpi_handle(vpiSysTfCall,0);
    vpiHandle args=vpi_iterate(vpiArgument,call);
    vpiHandle input=vpi_scan(args), output=vpi_scan(args);
    s_vpi_value v={.format=vpiVectorVal};
    t105_batch b; t105_decision d;
    unsigned char *p=(unsigned char *)&b;
    vpi_get_value(input,&v);
    for(unsigned i=0;i<24;i++) {
        if(v.value.vector[i].bval) {vpi_printf("UNKNOWN_HISTORY\n");vpi_control(vpiFinish,1);return 0;}
        for(unsigned j=0;j<4;j++) p[4*i+j]=(unsigned)v.value.vector[i].aval>>(8*j);
    }
    if(!state.sequence) t105_batch_init(&state);
    if(!t105_batch_apply(&state,&b) || !t105_decide(&state,&d)) {
        vpi_printf("C_REJECTED_HISTORY\n");vpi_control(vpiFinish,1);return 0;
    }
    s_vpi_vecval words[8];p=(unsigned char *)&d;
    for(unsigned i=0;i<8;i++) {
        unsigned word=0;for(unsigned j=0;j<4;j++) word|=(unsigned)p[4*i+j]<<(8*j);
        words[i].aval=word;words[i].bval=0;
    }
    v.value.vector=words;vpi_put_value(output,&v,0,vpiNoDelay);return 0;
}
static void register_bridge(void) {
    s_vpi_systf_data data={.type=vpiSysTask,.tfname="$t105_decide_batch",.calltf=calculate};
    vpi_register_systf(&data);
}
void (*vlog_startup_routines[])(void)={register_bridge,0};
