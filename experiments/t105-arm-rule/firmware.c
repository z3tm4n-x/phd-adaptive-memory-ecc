#include "driver.h"
/* Linkable OCM image, NOT a qualified BSP or a measured execution.
 * Enter after PS clocks/OCM and the PL startup contract are established.
 * One owning core; Device/non-cacheable MMIO; no runtime restart.
 * The second core, DMA and interrupts are outside this timing candidate. */
static t105_driver controller;
int main(void) {
    volatile uint32_t *m=(volatile uint32_t *)0x40000000u;
    t105_driver_init(&controller);
    for(;;) {
        int status=t105_driver_step(&controller,m);
        if(status<0) {
            /* Fault is retained and published by the driver/peripheral.
             * No fallback that pretends the program serviced its deadline. */
            for(;;) __asm__ volatile("wfi" ::: "memory");
        }
    }
}
