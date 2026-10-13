# Pure register model for the ACTUAL host procedure; never binds XSCT/JTAG.
source [file join [file dirname [info script]] startup_host.tcl]
set saved_trace {}
proc read32 {a} {
    global regs
    set a [expr {$a}]
    if {[info exists regs($a)]} {return $regs($a)}
    return 0
}
proc write32 {a v} {
    global regs trace mutation
    set a [expr {$a}]
    if {$mutation eq "ignore-ocm" && $a==0xf8000910} {return}
    lappend trace [list $a $v]
    set regs($a) $v
}
set passed {}
foreach mutation {none l2-on no-pll-lock ignore-ocm wrong-silicon} {
    array unset regs
    set trace {}
    set regs([expr {0xf800010c}]) [expr {$mutation ne "no-pll-lock"}]
    set regs([expr {0xf8007080}]) [expr {$mutation eq "wrong-silicon" ? 0x10000000 : 0x20000000}]
    set regs([expr {0xf8f02100}]) [expr {$mutation eq "l2-on"}]
    set regs([expr {0xf8007014}]) 0x40000000
    set result [catch {t105_cold_prepare read32 write32} message]
    if {$result != ($mutation ne "none")} {error "wrong result $mutation $message"}
    if {$mutation eq "none"} {set good [array get regs];set saved_trace $trace}
    lappend passed $mutation
}
if {$argc != 1} {error "JSON output required"}
set f [open [lindex $argv 0] w]
puts $f "\{\"kind\":\"Tcl register model, not a hardware launch\",\"tcl\":\"[info patchlevel]\","
puts $f "\"cases\":\[\"[join $passed {","}]\"\],\"registers\":\{"
set pairs {}
foreach {a v} $good {lappend pairs [format {"0x%08x":"0x%08x"} $a $v]}
puts $f [join [lsort $pairs] ,]
puts $f "\},\"writes\":\["
set pairs {}
foreach pair $saved_trace {lappend pairs [format {[%u,%u]} {*}$pair]}
puts $f [join $pairs ,]
puts $f "\]\}"
close $f
puts "C0_HOST_MODEL_PASS [llength $passed]"
