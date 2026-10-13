#include "rule.h"
typedef struct { t105_input input; t105_state expected; uint32_t low,reset; } vector;
#include "vectors.h"
static int semi(uint32_t op, const void *arg) {
    register uint32_t r0 __asm__("r0")=op;
    register const void *r1 __asm__("r1")=arg;
    __asm__ volatile("svc 0x123456" : "+r"(r0) : "r"(r1) : "memory", "cc");
    return (int)r0;
}
int main(void) {
    t105_state s;
    t105_init(&s);
    uint32_t failure=0;
    for (uint32_t i=0;i<sizeof(vectors)/sizeof(vectors[0]);i++) {
        if(vectors[i].reset) t105_init(&s);
        t105_apply(&s,&vectors[i].input);
        const unsigned char *a=(const unsigned char *)&s;
        const unsigned char *b=(const unsigned char *)&vectors[i].expected;
        for(uint32_t j=0;j<sizeof(s);j++) if(a[j]!=b[j]) failure=i+1;
        if(t105_low(&s)!=vectors[i].low) failure=i+1;
        if(failure) break;
    }
    semi(4,failure ? "ARM_RULE_FAILED\n" : "ARM_RULE_OK\n");
    uint32_t exit_args[2]={0x20026,failure};
    semi(0x20,exit_args);
    return (int)failure;
}
