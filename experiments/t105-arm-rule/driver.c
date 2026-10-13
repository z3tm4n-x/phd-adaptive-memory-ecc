#include "driver.h"
static void barrier(void) {
#ifdef __arm__
    __asm__ volatile("dmb sy" ::: "memory");
#else
    __asm__ volatile("" ::: "memory");
#endif
}
static int fail(t105_driver *d,volatile uint32_t *m,uint32_t reason) {
    d->failure=reason; m[3]=1;barrier();return -1;
}
void t105_driver_init(t105_driver *d) {
    t105_batch_init(&d->rule);d->phase=0;d->failure=0;
}
int t105_driver_step(t105_driver *d, volatile uint32_t *m) {
    if(d->failure) return -1;
    uint32_t status=m[0];barrier();
    if(status&16u) {d->failure=1;return -1;}
    switch(d->phase) {
    case 0:
        if(!(status&8u)) return 0;
        /* An unexpected retained bank means this is not qualified startup;
         * never discard/reinitialize already acknowledged history. */
        if(status&7u) return fail(d,m,2);
        m[1]=1;barrier();d->phase=1;return 0;
    case 1:
        if(!(status&1u)) return 0;
        for(uint32_t i=0;i<24;i++) d->input.words[i]=m[64+i];
        barrier();
        if(!t105_batch_apply(&d->rule,&d->input.batch) ||
           !t105_decide(&d->rule,&d->output.decision)) {
            /* Numerical/protocol failure is explicit; do not silently
             * substitute a healthy result or clear the retained bank. */
            return fail(d,m,3);
        }
        for(uint32_t i=0;i<8;i++) m[128+i]=d->output.words[i];
        barrier();m[2]=1;barrier();d->phase=2;return 0;
    case 2:
        if(status&7u) return 0;
        /* Only read ACK after snapshot/validation/output are all clear.
         * ACK means accepted by slow interval delivery, NOT fast applied. */
        {uint32_t lo=m[4],hi=m[5];barrier();
         if((((uint64_t)hi<<32)|lo)!=d->rule.sequence) {
             return fail(d,m,4);
         }}
        d->phase=0;return 1;
    default:return fail(d,m,5);
    }
}
