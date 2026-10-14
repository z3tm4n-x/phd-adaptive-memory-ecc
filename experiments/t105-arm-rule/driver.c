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
        /* The immutable collector bank already proves these identities:
         * base_G = previous bank's end_G; start never changes after start;
         * reserved = 0; count = end_G - base_G (overflow sets fault).
         * Reconstruct only those identities; do NOT move policy to PL.
         * The full sequence is still read and validated, including first
         * startup. No assumption that an old bank is the requested bank. */
        for(uint32_t i=0;i<2;i++) d->input.words[i]=m[64+i];
        for(uint32_t i=4;i<8;i++) d->input.words[i]=m[64+i];
        d->input.batch.base_generation=d->rule.rule.generation;
        if(d->rule.sequence==0) {
            d->input.words[8]=m[72];d->input.words[9]=m[73];
        } else d->input.batch.start_tick=d->rule.start_tick;
        d->input.batch.err_count=m[85];d->input.batch.flags=m[86];
        d->input.batch.reserved=0;
        if(d->input.batch.end_generation<d->input.batch.base_generation ||
           d->input.batch.end_generation-d->input.batch.base_generation>UINT32_MAX)
            return fail(d,m,6);
        d->input.batch.event_count=(uint32_t)(d->input.batch.end_generation-d->input.batch.base_generation);
        for(uint32_t i=10;i<18;i++) d->input.words[i]=d->input.batch.err_count?m[64+i]:0;
        for(uint32_t i=18;i<20;i++) d->input.words[i]=(d->input.batch.flags&B_RECOVERY)?m[64+i]:0;
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
        /* RTL clears snapshot only after the sequence/G/CRC-checked
         * decision was accepted. Status is NOT a fast-domain ACK.
         * There is one owner, no runtime reset, and no other clear path.
         * Start the next snapshot now, without a redundant ACK read or
         * second status read in phase 0. Faults still stop before CLAIM. */
        m[1]=1;barrier();d->phase=1;return 1;
    default:return fail(d,m,5);
    }
}
