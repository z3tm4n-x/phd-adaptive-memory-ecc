# Read-only interrogation of an existing routed checkpoint; NO new constraints.
# vivado -mode batch -source sta_detail.tcl -tclargs ROUTED_DCP NEW_OUTPUT_DIR
if {$argc != 2} {error "Required: routed checkpoint and new output directory"}
set checkpoint [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
if {![file isfile $checkpoint]} {error "Missing routed checkpoint"}
if {[file exists $out]} {error "Refusing to overwrite $out"}
file mkdir $out
cd $out
set_param general.maxThreads 4
open_checkpoint $checkpoint
proc path_row {handle path} {
    set row {}
    foreach property {STARTPOINT_PIN ENDPOINT_PIN GROUP REQUIREMENT SLACK DATAPATH_DELAY LOGIC_LEVELS EXCEPTION} {
        lappend row [get_property $property $path]
    }
    lappend row [get_property CLASS [get_property STARTPOINT_PIN $path]]
    puts $handle [join $row "\t"]
}
set header "start\tend\tgroup\trequirement_ns\tslack_ns\tdata_delay_ns\tlogic_levels\texception\tstart_class"
set hold [get_timing_paths -delay_type min -max_paths 20000 -nworst 1 -slack_lesser_than 0]
if {[llength $hold] >= 20000} {error "Hold extraction truncated"}
if {[llength $hold]} {report_property [lindex $hold 0] -file path_properties.rpt}
set h [open hold.tsv w]; puts $h $header
foreach path $hold {path_row $h $path}
close $h
set gray_sources [get_cells -hierarchical -regexp {.*published_gray_reg\[[0-9]+\]$}]
set gray_cells [get_cells -hierarchical -regexp {.*gt1_reg\[[0-9]+\]$}]
set gray_pins [get_pins -of_objects $gray_cells -filter {REF_PIN_NAME == D}]
set h [open gray.tsv w]; puts $h $header
set missing {}
foreach pin $gray_pins {
    set paths [get_timing_paths -quiet -delay_type max -from $gray_sources -to $pin -max_paths 1]
    if {[llength $paths] != 1} {lappend missing $pin; continue}
    path_row $h [lindex $paths 0]
}
close $h
set h [open selection.txt w]
puts $h "hold_paths [llength $hold]"
puts $h "gray_source_cells [llength $gray_sources]"
puts $h "gray_destination_cells [llength $gray_cells]"
puts $h "gray_destination_pins [llength $gray_pins]"
puts $h "gray_missing_paths [llength $missing] $missing"
foreach pin $missing {
    puts $h "MISSING $pin"
    puts $h "NET [get_nets -of_objects $pin]"
    set drivers [get_pins -of_objects [get_nets -of_objects $pin] -filter {DIRECTION == OUT}]
    puts $h "DRIVERS $drivers"
    puts $h "DRIVER_TYPES [get_property REF_NAME [get_cells -of_objects $drivers]]"
}
close $h
report_timing -delay_type max -from $gray_sources -to $gray_pins -max_paths 4 -file gray_worst.rpt
report_exceptions -coverage -file exceptions_coverage.rpt
report_exceptions -ignored -file exceptions_ignored.rpt
puts "T104_DETAIL_COMPLETED $out"
exit
