/* Bridge only. frozen_rule.h is built from the checked-in public #448 model.
 * No generator, old external decoder or old bus tariff is linked. */
#include <vpi_user.h>
#include <assert.h>
#include <stdint.h>
#include <limits.h>
#include <stdlib.h>
#include "frozen_rule.h"

static uint64_t get(vpiHandle a) {
    int width=vpi_get(vpiSize,a);
    assert(width>=1 && width<=64);
    s_vpi_value v = {.format=vpiVectorVal};
    vpi_get_value(a,&v);
    uint64_t result=0;
    for(int offset=0;offset<width;offset+=32){
        int n=width-offset;
        uint32_t mask=n>=32?UINT32_MAX:((UINT32_C(1)<<n)-1);
        s_vpi_vecval word=v.value.vector[offset/32];
        assert(!((uint32_t)word.bval&mask));
        result|=(uint64_t)((uint32_t)word.aval&mask)<<offset;
    }
    return result;
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
    Tick det=get(a[2])?0:-1;
    int invalid=(int)get(a[3]);
    if(getenv("T457_VPI_DEBUG") && (round==1280 || round==1282))
        vpi_printf("PROBE r=%lld old=%d bad_cell=%lld det=%lld invalid=%d nbits=%d\n",
                   (long long)round,s.step,(long long)s.last_bad,(long long)det,invalid,vpi_get(vpiSize,a[3]));
    int step=choose(&p,&rule,&s,round,det,invalid,&change);
    put(a[6],step);put(a[7],s.last_bad);
    return 0;
}
static void setup(void){
    s_vpi_systf_data f={.type=vpiSysTask,.tfname="$native_choose",.calltf=policy};
    vpi_register_systf(&f);
}
void (*vlog_startup_routines[])(void)={setup,0};
