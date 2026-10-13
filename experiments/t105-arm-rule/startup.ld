ENTRY(t105_boot)
MEMORY { BOOT (rwx) : ORIGIN = 0xfffe0000, LENGTH = 8K }
SECTIONS {
 .text : { *(.boot) *(.text*) *(.rodata*) } >BOOT
 .data : { *(.data*) } >BOOT
 .bss (NOLOAD) : { *(.bss*) *(COMMON) } >BOOT
 ASSERT(SIZEOF(.data) == 0 && SIZEOF(.bss) == 0, "startup must not need C initialization")
 /DISCARD/ : { *(.comment) *(.ARM.exidx*) *(.ARM.extab*) }
}
