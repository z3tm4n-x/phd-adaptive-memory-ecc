# Read-only analysis of the existing routed checkpoint; no placement changes.
if {$argc!=2} {error "checkpoint and new output directory required"}
set checkpoint [file normalize [lindex $argv 0]]
set out [file normalize [lindex $argv 1]]
if {[file exists $out]} {error "output already exists"}
file mkdir $out
open_checkpoint $checkpoint
set ins [get_ports {sram_err sram_dq[*]}]
set outs [get_ports {sram_a[*] sram_dq[*] sram_ce_n sram_oe_n sram_we_n sram_lb_n sram_ub_n}]
foreach corner {Slow Fast} {
 foreach kind {min max} {
  report_timing -from $ins -to [all_registers] -corner $corner -delay_type $kind -max_paths 400 -nworst 4 -file $out/input_${corner}_${kind}.rpt
  report_timing -from [all_registers] -to $outs -corner $corner -delay_type $kind -max_paths 400 -nworst 4 -file $out/output_${corner}_${kind}.rpt
 }
}
set p [lindex [get_timing_paths -from [get_ports sram_err] -max_paths 1] 0]
report_property $p -file $out/path_properties.rpt
report_datasheet -file $out/datasheet.rpt
# Diagnostic clocked I/O reports expose clock insertion and actual input
# hold/setup arcs. They are NOT acceptance constraints and are never saved
# back into the implemented DCP. The external phase checker replaces this
# fictitious every-edge stimulus by the actual SRAM windows.
reset_timing
create_clock -name ref100 -period 10 [get_ports ref100]
set_clock_uncertainty -setup 0.5 [get_clocks *]
set_clock_uncertainty -hold 0.1 [get_clocks *]
set_load 15 $outs
set fclk [get_clocks fast_raw]
set_input_delay -clock $fclk -max 0 $ins
set_input_delay -clock $fclk -min 0 $ins
set_output_delay -clock $fclk -max 0 $outs
set_output_delay -clock $fclk -min 0 $outs
foreach corner {Slow Fast} {
 foreach kind {min max} {
  report_timing -from $ins -to [all_registers] -corner $corner -delay_type $kind -max_paths 400 -nworst 4 -file $out/clocked_input_${corner}_${kind}.rpt
  report_timing -from [all_registers] -to $outs -corner $corner -delay_type $kind -max_paths 400 -nworst 4 -file $out/clocked_output_${corner}_${kind}.rpt
 }
}
puts "PHYSICAL_IO_INSPECTION_COMPLETE"
exit
