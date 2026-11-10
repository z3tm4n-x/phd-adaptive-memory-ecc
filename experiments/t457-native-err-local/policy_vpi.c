/* Bridge only. frozen_rule.h is built from the checked-in public #448 model.
 * No generator, old external decoder or old bus tariff is linked. */
#include <vpi_user.h>
#include <assert.h>
#include <stdint.h>
#include <limits.h>
#include "frozen_rule.h"

static uint64_t get(vpiHandle a) {
    s_vpi_value v = {.format=vpiVectorVal};
    vpi_get_value(a,&v);
    assert(v.value.vector[0].bval==0);
    uint64_t lo=(uint32_t)v.value.vector[0].aval;
    if(vpi_get(vpiSize,a)<=32) return lo;
    assert(!v.value.vector[1].bval);
    return lo | ((uint64_t)(uint32_t)v.value.vector[1].aval<<32);
}
static void put(vpiHandle a,uint64_t n){
    s_vpi_vecval bits[2]={{(PLI_INT32)n,0},{(PLI_INT32)(n>>32),0}};
    s_vpi_value v={.format=vpiVectorVal}; v.value.vector=bits;
    vpi_put_value(a,&v,0,vpiNoDelay);
}
static PLI_INT32 policy(PLI_BYTE8 *unused){
    (void)unused;
    vpiHandle it=vpi_iterate(vpiArgument,vpi_handle(vpiSysTfCall,NULL));
    vpiHandle a[8];
    for(int i=0;i<8;i++){a[i]=vpi_scan(it);assert(a[i]);}
    assert(!vpi_scan(it));
    Port p={.L=(Tick)get(a[0])};
    Rule rule={CELL_LADDER,256,1680,"native457"};
    Tick round=(Tick)get(a[1]), change;
    State s={.step=(int)get(a[4]),.last_bad=(Tick)get(a[5])};
    int step=choose(&p,&rule,&s,round,get(a[2])?0:-1,(int)get(a[3]),&change);
    put(a[6],step);put(a[7],s.last_bad);
    return 0;
}
static void setup(void){
    s_vpi_systf_data f={.type=vpiSysTask,.tfname="$native_choose",.calltf=policy};
    vpi_register_systf(&f);
}
void (*vlog_startup_routines[])(void)={setup,0};
