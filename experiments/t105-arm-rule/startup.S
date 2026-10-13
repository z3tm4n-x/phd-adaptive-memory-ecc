.syntax unified
.file "startup.S"
.arm
.section .boot,"ax"
.global t105_boot
t105_boot:
    b cold_entry
    b startup_trap
    b startup_trap
    b startup_trap
    b startup_trap
    b startup_trap
    b startup_trap
    b startup_trap
cold_entry:
    cpsid aif
    mrs r0, cpsr
    and r0, r0, #0x1f
    cmp r0, #0x13
    bne startup_trap
    mrc p15, 0, r0, c1, c0, 0
    ldr r1, =0x1005 /* no MMU or enabled L1 at entry: no dirty warm handoff */
    tst r0, r1
    bne startup_trap
    ldr sp, =0xffff0000
    ldr r0, =t105_boot
    mcr p15, 0, r0, c12, c0, 0
    bl startup_main
    cmp r0, #0
    bne startup_trap
    /* MMU is identity-mapped; this is the unmodified, pinned policy ELF. */
    ldr r0, =0xfffc0000
    bx r0
.global startup_trap
startup_trap:
    cpsid aif
    b startup_trap
.section .note.GNU-stack,"",%progbits
