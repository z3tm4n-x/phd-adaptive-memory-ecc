#include "driver.h"
#include <assert.h>
#include <string.h>
int main(void) {
    t105_driver d;uint32_t m[160]={0};t105_driver_init(&d);
    assert(t105_driver_step(&d,m)==0 && d.phase==0);
    m[0]=8;assert(t105_driver_step(&d,m)==0 && m[1]==1 && d.phase==1);
    t105_batch b={.sequence=1,.end_tick=100,.start_tick=1,.flags=3};
    memcpy(m+64,&b,sizeof(b));m[0]=9;
    assert(t105_driver_step(&d,m)==0 && d.phase==2 && m[2]==1);
    assert(d.output.decision.generation==0 && d.output.decision.flags==1);
    assert(d.output.decision.not_before==1+T105_NR);
    assert(memcmp(m+128,&d.output.decision,32)==0);
    assert(t105_driver_step(&d,m)==0); /* bank retained, no early ACK */
    m[0]=8;m[4]=1;assert(t105_driver_step(&d,m)==1 && d.phase==1 && m[1]==1);
    b.sequence=2;b.end_tick=101;memcpy(m+64,&b,sizeof(b));m[0]=9;
    assert(t105_driver_step(&d,m)==0);
    /* Hardware release, not the retained diagnostic ACK register, is the
     * completion evidence in the optimized protocol. */
    m[0]=8;assert(t105_driver_step(&d,m)==1 && d.phase==1);
    b.sequence=2;b.end_tick=102;memcpy(m+64,&b,sizeof(b));m[0]=9;
    assert(t105_driver_step(&d,m)==-1 && d.failure==3); /* replay */
    t105_driver_init(&d);m[0]=9;
    assert(t105_driver_step(&d,m)==-1 && d.failure==2);
    t105_driver_init(&d);m[0]=24;
    assert(t105_driver_step(&d,m)==-1 && d.failure==1);
    return 0;
}
