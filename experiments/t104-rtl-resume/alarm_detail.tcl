# Extend the historical read-only extraction, retaining its exact semantics.
set t104_detail_script [file join [file dirname [file normalize [info script]]] sta_detail.tcl]
rename exit t104_real_exit
proc exit {} {}
source $t104_detail_script
rename exit {}
rename t104_real_exit exit
set setup [get_timing_paths -delay_type max -max_paths 20000 -nworst 1 -slack_lesser_than 0]
if {[llength $setup] >= 20000} {error "Setup extraction truncated"}
set h [open setup.tsv w]; puts $h $header
foreach path $setup {path_row $h $path}
close $h
set gate_cells [get_cells -hier -regexp {core/gate/.*_reg.*}]
set gate_pins [get_pins -of_objects $gate_cells -filter {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
if {![llength $gate_pins]} {error "No adjacent gate endpoints"}
report_timing -delay_type max -to $gate_pins -max_paths 12 -nworst 1 -file adjacent_gate.rpt
set h [open fanout.tsv w]
puts $h "net\tsink_pins\tdrivers"
foreach net [get_nets -hier -filter {NAME =~ *gate* || NAME =~ *new_queue_loss* || NAME =~ *alarm* || NAME =~ *permit*}] {
    set sinks [get_pins -quiet -of_objects $net -filter {DIRECTION == IN}]
    if {[llength $sinks]>=32} {
        puts $h "$net\t[llength $sinks]\t[get_pins -quiet -of_objects $net -filter {DIRECTION == OUT}]"
    }
}
close $h
puts "T104_ALARM_DETAIL_COMPLETE $out"
exit
