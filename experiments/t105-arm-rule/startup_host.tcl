# Cold POR/JTAG preparation only. Sourcing defines procedures; does NOT connect,
# reset, program, load, run, or qualify a real target. No hardware test assigned.
# Caller must supply read32/write32 procedures with completed ordered transfers.
# Run on DAP while both CPUs are halted after POR, PL loaded through JTAG, and
# qualified_switch is LOW. Never call on a running mission or OS handoff.
proc t105_cold_prepare {read32 write32} {
    # Check cold disabled L2 and chosen silicon before altering any registers.
    if {([{*}$read32 0xf8f02100] & 1) != 0} {error "cold L2 disabled required"}
    if {([{*}$read32 0xf8007080] >> 28) != 2} {error "PS silicon v3.0 required"}
    {*}$write32 0xf8000008 0xdf0d
    foreach {a mask value} {
        0xf8000244 0x133 0x22
        0xf800020c 0x1 0x1
        0xf8000210 0x3 0x3
        0xf8000214 0xf3 0xf3
        0xf8000218 0x33 0x33
        0xf800012c 0x01ffcccd 0
        0xf8000100 0x18 0x10
        0xf8000100 0x3 0x1
        0xf8000100 0x7f000 0x24000
        0xf8000110 0x3ffff0 0x113220
        0xf8000100 0x1 0
    } {t105_mask_check $read32 $write32 $a $mask $value}
    set locked 0
    for {set i 0} {$i < 100000} {incr i} {
        if {([{*}$read32 0xf800010c] & 1) != 0} {set locked 1;break}
    }
    if {!$locked} {error "ARM PLL did not lock: no image launch"}
    foreach {a mask value} {
        0xf8000120 0x1f003f30 0x1f000200
        0xf8000100 0x18 0
        0xf80001c4 1 1
        0xf8000910 0xf 0xf
        0xf8f00040 0xfff00000 0
        0xf8f00044 0xfff00000 0xffe00000
        0xf8f00000 3 3
        0xf8000900 0xf 0xf
        0xf8000240 0xffffffff 0
    } {t105_mask_check $read32 $write32 $a $mask $value}
    {*}$write32 0xf8000004 0x767b
    # All remapping / CLK_621 changes completed while CPU0 was halted.
    # Load pinned firmware.elf, startup.elf, set PC=t105_boot, resume CPU0
    # in the chosen launch environment. No mission start is generated here.
    return "C0_HOST_PREPARED_NOT_STARTED"
}
proc t105_mask_check {read32 write32 a mask value} {
    set old [{*}$read32 $a]
    {*}$write32 $a [expr {(($old & ~$mask) | $value) & 0xffffffff}]
    if {([{*}$read32 $a] & $mask) != $value} {error "register mismatch $a"}
}
