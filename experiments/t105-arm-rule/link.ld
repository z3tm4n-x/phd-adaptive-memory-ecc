ENTRY(_start)
MEMORY { OCM (rwx) : ORIGIN = 0xfffc0000, LENGTH = 256K }
SECTIONS {
  .text : { *(.text.start) *(.text*) *(.rodata*) } >OCM
  .data : { *(.data*) } >OCM
  .bss (NOLOAD) : { . = ALIGN(8); _bss_start = .; *(.bss*) *(COMMON) . = ALIGN(8); _bss_end = .; } >OCM
  _stack_top = ORIGIN(OCM) + LENGTH(OCM) - 4096;
  ASSERT(_bss_end + 8192 < _stack_top, "OCM stack collision")
  /DISCARD/ : { *(.comment) *(.ARM.exidx*) *(.ARM.extab*) }
}
