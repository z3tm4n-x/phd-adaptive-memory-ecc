/* C0-OCM cold profile. No vendor BSP defaults, no runtime reset/recovery.
 * Hardware is NOT accessed by the reproduction: see startup_check.py.
 * Register provenance and pre-start/JTAG isolation are in STARTUP.md. */
#include <stdint.h>
#define R(a) (*(volatile uint32_t *)(a))
#define MRC(name, spec) static uint32_t name(void) {uint32_t v; __asm__ volatile("mrc " spec : "=r"(v)); return v;}
#define MCR(name, spec) static void name(uint32_t v) {__asm__ volatile("mcr " spec :: "r"(v) : "memory");}
MRC(sctlr,"p15, 0, %0, c1, c0, 0")
MRC(actlr,"p15, 0, %0, c1, c0, 1")
MRC(midr,"p15, 0, %0, c0, c0, 0")
MRC(mpidr,"p15, 0, %0, c0, c0, 5")
MRC(scr,"p15, 0, %0, c1, c1, 0")
MRC(ttbr,"p15, 0, %0, c2, c0, 0")
MRC(ttbcr,"p15, 0, %0, c2, c0, 2")
MRC(dacr,"p15, 0, %0, c3, c0, 0")
MCR(wsctlr,"p15, 0, %0, c1, c0, 0")
MCR(wactlr,"p15, 0, %0, c1, c0, 1")
MCR(wttbr,"p15, 0, %0, c2, c0, 0")
MCR(wttbr1,"p15, 0, %0, c2, c0, 1")
MCR(wttbcr,"p15, 0, %0, c2, c0, 2")
MCR(wdacr,"p15, 0, %0, c3, c0, 0")
MCR(tlbi,"p15, 0, %0, c8, c7, 0")
MCR(ici,"p15, 0, %0, c7, c5, 0")
MCR(bpi,"p15, 0, %0, c7, c5, 6")
static void sync(void) {__asm__ volatile("dsb sy\nisb sy" ::: "memory");}
static const uint32_t expectations[][3] = {
 {0xf8000100,0x0007f01f,0x00024000}, /* FDIV36, reset/power/bypass/strap off */
 {0xf800010c,1,1},                   /* ARM PLL lock */
 {0xf8000120,0x1f003f30,0x1f000200}, /* ARM PLL /2, active clocks */
 {0xf80001c4,1,1},                   /* 6:2:1; never change while fetching OCM */
 {0xf8000244,0x133,0x22},            /* CPU1 reset+clockstop, CPU0/peri running */
 {0xf800020c,1,1},                   /* PL330 reset */
 {0xf8000210,3,3},                   /* USB resets */
 {0xf8000214,0xf3,0xf3},             /* GEM resets */
 {0xf8000218,0x33,0x33},             /* SDIO resets */
 {0xf800012c,0x01ffcccd,0},          /* no peripheral AMBA clocks */
 {0xf8000910,0xf,0xf},              /* all OCM high before loading either ELF */
 {0xf8f00000,3,3},                  /* SCU + address filtering enabled */
 {0xf8f00040,0xfff00000,0},
 {0xf8f00044,0xfff00000,0xffe00000},
 {0xf8f02100,1,0},                  /* L2 already disabled after cold POR */
 {0xf8007014,0xc0000000,0x40000000}, /* DevC STATUS: DMA queue empty, not full */
 {0xf8007080,0xf0000000,0x20000000}  /* chosen PS silicon v3.0 */
};
int startup_main(void) {
 volatile uint32_t *report=(volatile uint32_t *)0xfffed000;
 report[0]=0; report[1]=midr(); report[2]=sctlr(); report[3]=actlr();
 if(midr()!=0x413fc090 || (mpidr()&0xfff) || (scr()&1)) return report[0]=1;
 for(unsigned i=0;i<sizeof(expectations)/sizeof(expectations[0]);i++)
  if((R(expectations[i][0])&expectations[i][1])!=expectations[i][2]) return report[0]=0x100+i;
 /* qualified_start must be held externally low, not asserted by a CPU write. */
 if(R(0x40000000)!=0) return report[0]=2;
 /* Cortex-A9 GICv1, Secure access: ICDDCR[1:0], ICCICR[4:0].
  * Higher bits are reserved, NOT the GICv2 bypass-disable controls.
  * Both interfaces disabled leaves legacy IRQ/FIQ pass-through enabled.
  * IRQ is masked by CPSR.I; NMFI=1 means CPSR.F is NOT our FIQ guarantee.
  * External FIQ must remain inactive from cold entry through the mission.
  * This is a platform precondition, not established by these readbacks. */
 R(0xf8f01000)=0; R(0xf8f00100)=0; sync();
 if((R(0xf8f01000)&3) || (R(0xf8f00100)&0x1f)) return report[0]=3;
 /* No L2 prefetch and no L2 use. Reject dirty/warm starts, do not flush them. */
 R(0xf8f02f60) &= ~0x30000000u;
 if(R(0xf8f02f60)&0x30000000u) return report[0]=5;
 wactlr((actlr()&~6u)|0x40u);
 volatile uint32_t *l1=(volatile uint32_t *)0xfffd0000;
 volatile uint32_t *ocm=(volatile uint32_t *)0xfffd4000;
 volatile uint32_t *dev=(volatile uint32_t *)0xfffd4400;
 for(unsigned i=0;i<4096;i++) l1[i]=0;
 for(unsigned i=0;i<256;i++) {ocm[i]=0;dev[i]=0;}
 l1[0xfff]=0xfffd4001; l1[0x400]=0xfffd4401; /* coarse, domain0 */
 /* Independent decoder in checker does not reuse these encodings. */
 for(unsigned i=0xc0;i<0xc2;i++) ocm[i]=(0xfff00000u+(i<<12))|0x452;
 for(unsigned i=0xd0;i<0xd5;i++) ocm[i]=(0xfff00000u+(i<<12))|0x453;
 for(unsigned i=0xe0;i<0xe2;i++) ocm[i]=(0xfff00000u+(i<<12))|0x652;
 for(unsigned i=0xed;i<0xf0;i++) ocm[i]=(0xfff00000u+(i<<12))|0x453;
 for(unsigned i=0xfd;i<0xff;i++) ocm[i]=(0xfff00000u+(i<<12))|0x453;
 dev[0]=0x40000417; /* Device/shareable, privileged RW, XN */
 sync(); tlbi(0); ici(0); bpi(0); sync();
 wttbcr(0); wttbr1(0); wttbr(0xfffd0002); wdacr(1); sync();
 if(ttbr()!=0xfffd0002 || ttbcr()!=0 || dacr()!=1) return report[0]=4;
 uint32_t control=sctlr();
 /* Short descriptors, explicit TEX/C/B, client domain, low VBAR, ARM LE. */
 control &= ~((1u<<30)|(1u<<29)|(1u<<28)|(1u<<25)|(1u<<19)|0x3804u);
 control |= 3; /* MMU and alignment enabled; I/C/Z remain clear */
 wsctlr(control); sync();
 if(sctlr()!=control || ttbr()!=0xfffd0002 || ttbcr()!=0 || dacr()!=1 ||
    (actlr()&0x46)!=0x40) return report[0]=4;
 report[4]=sctlr();report[5]=actlr();report[6]=ttbr();report[7]=dacr();
 report[0]=0x43305244; /* C0RD: startup done, NOT timing qualified or mission started */
 sync();return 0;
}
