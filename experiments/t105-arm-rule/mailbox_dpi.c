/* Native C for Vivado/XPM functional composition; never a CPU timing model. */
#include "batch.h"
static t105_batch_state state;
int calculate_batch(const uint32_t *input,uint32_t *output) {
    t105_batch b; t105_decision d;
    unsigned char *p=(unsigned char *)&b;
    for(unsigned i=0;i<24;i++) for(unsigned j=0;j<4;j++) p[4*i+j]=input[i]>>(8*j);
    if(!state.sequence) t105_batch_init(&state);
    if(!t105_batch_apply(&state,&b) || !t105_decide(&state,&d)) return 0;
    p=(unsigned char *)&d;
    for(unsigned i=0;i<8;i++) {
        uint32_t word=0;for(unsigned j=0;j<4;j++) word|=(uint32_t)p[4*i+j]<<(8*j);
        output[i]=word;
    }
    return 1;
}
