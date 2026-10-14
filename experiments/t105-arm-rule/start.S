.syntax unified
.file "start.S"
.arm
.section .text.start,"ax"
.global _start
_start:
    cpsid if
    ldr sp, =_stack_top
    ldr r0, =_bss_start
    ldr r1, =_bss_end
    mov r2, #0
1:  cmp r0, r1
    strlo r2, [r0], #4
    blo 1b
    bl main
2:  b 2b
.section .note.GNU-stack,"",%progbits
