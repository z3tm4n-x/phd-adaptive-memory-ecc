# A separate all-register scope: doesn't suppress/report-away virtual IO failures.
if {$argc!=1} {error "routed directory required"}
set out [file normalize [lindex $argv 0]]
cd $out
open_checkpoint routed.dcp
set regs [all_registers]
report_timing -from $regs -to $regs -delay_type max -max_paths 10 -file all_internal_setup.rpt
report_timing -from $regs -to $regs -delay_type min -max_paths 10 -file all_internal_hold.rpt
set f [open internal_slack.txt w]
foreach kind {max min} {
    set path [get_timing_paths -from $regs -to $regs -delay_type $kind -max_paths 1]
    if {[llength $path]!=1} {error "missing internal path"}
    puts $f "$kind [get_property SLACK $path]"
}
close $f
exit
