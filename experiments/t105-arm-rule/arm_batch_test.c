#include "batch.h"
typedef struct {
    t105_batch input;
    t105_state expected;
    t105_decision decision;
    uint32_t reset;
} vector;
#include "batch_vectors.h"
static int semi(uint32_t op,const void *arg) {
    register uint32_t r0 __asm__("r0")=op;
    register const void *r1 __asm__("r1")=arg;
    __asm__ volatile("svc 0x123456" : "+r"(r0) : "r"(r1) : "memory","cc");
    return (int)r0;
}
static int equal(const void *p,const void *q,uint32_t n) {
    const unsigned char *a=p,*b=q;
    while(n--) if(*a++!=*b++) return 0;
    return 1;
}
int main(void) {
    t105_batch_state s; t105_decision d; uint32_t failure=0;
    t105_batch_init(&s);
    for(uint32_t i=0;i<sizeof(vectors)/sizeof(vectors[0]);i++) {
        if(vectors[i].reset) t105_batch_init(&s);
        if(!t105_batch_apply(&s,&vectors[i].input) ||
           !equal(&s.rule,&vectors[i].expected,sizeof(s.rule)) ||
           !t105_decide(&s,&d) || !equal(&d,&vectors[i].decision,sizeof(d))) {
            failure=i+1; break;
        }
    }
    semi(4,failure?"ARM_BATCH_FAILED\n":"ARM_BATCH_OK\n");
    uint32_t result[2]={0x20026,failure};semi(0x20,result);return (int)failure;
}
