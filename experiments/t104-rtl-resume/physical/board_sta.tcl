# Full SRAM pad boundary; CPU/X is a separately specified50-MHz fabric port.
if {$argc!=1} {error "new output directory required"}
set here [file dirname [file normalize [info script]]]
set out [file normalize [lindex $argv 0]]
if {[file exists $out]} {error "output already exists"}
file mkdir $out
cd $out
set_param general.maxThreads 4
create_project -in_memory -part xc7z020clg484-1
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
foreach f {async_queue.sv slow_queue.sv clock_250_50.sv} {read_verilog -sv [file join $here ../split $f]}
foreach f {e_backend_registered.sv handshake_channel.sv} {
 set path [file join $here $f]
 if {![file exists $path]} {set path [file join $here ../registered $f]}
 read_verilog -sv $path
}
foreach f {event_fifo.sv segmented_counter.sv slow_rule.sv candidate_link.sv frame_engine.sv executor.sv} {
 set path [file join $here $f]
 if {![file exists $path]} {set path [file join $here ../integrated $f]}
 read_verilog -sv $path
}
read_verilog -sv [file join $here address_map.sv]
read_verilog -sv [file join $here top.sv]
read_verilog -sv [file join $here board_top.sv]
read_xdc [file join $here ../split/component_input.xdc]
read_xdc [file join $here board_pins.xdc]
synth_design -top board_top -part xc7z020clg484-1 -flatten_hierarchy rebuilt
set fast [get_clocks -of_objects [get_pins core/clocks/fast/O]]
set slow [get_clocks -of_objects [get_pins core/clocks/slow/O]]
set_clock_uncertainty -setup 0.5 [get_clocks *]
set_clock_uncertainty -hold 0.1 [get_clocks *]
# Switch inputs are asynchronous and only enter standard XPM synchronizers.
# Only vendor XPM exceptions are allowed; LEDs have real routed endpoints.
set_output_delay -clock $slow -max 5 [get_ports {fault_led locked_led}]
set_output_delay -clock $slow -min 0 [get_ports {fault_led locked_led}]
set_load 5 [get_ports {fault_led locked_led}]
set_input_delay -clock $slow -max 0 [get_ports {qualified_switch loss_switch}]
set_input_delay -clock $slow -min 0 [get_ports {qualified_switch loss_switch}]

# No invented periodic capture window for the asynchronous SRAM. These are
# explicit pad propagation budgets, composed with the proved phase waveform
# and datasheet bounds by the independent I/O checker. Both min and max
# reports are retained. Analog pad loading is15pF, adapter flight≤.5ns.
set sram_in [get_ports {sram_err sram_dq[*]}]
set sram_out [get_ports {sram_a[*] sram_dq[*] sram_ce_n sram_oe_n sram_we_n sram_lb_n sram_ub_n}]
set_max_delay -datapath_only 2.5 -from $sram_in -to [all_registers]
set_min_delay 0 -from $sram_in -to [all_registers]
set_max_delay -datapath_only 5.0 -from [all_registers] -to $sram_out
set_min_delay 0 -from [all_registers] -to $sram_out
config_timing_corners -corner Slow -delay_type min_max
config_timing_corners -corner Fast -delay_type min_max
write_checkpoint synthesized.dcp
set pin_regs [get_cells -hier -regexp {.*backend/pad_(ce|oe|we|be)_n_reg.*}]
if {[llength $pin_regs]!=5} {error "expected five output control registers"}
# The synthesis hints alone did not prevent later control-set extraction.
# UG912 remaps the actual primitive controls; clocks/uncertainty are unchanged.
set_property CONTROL_SET_REMAP ALL $pin_regs
set_property CONTROL_SET_REMAP ENABLE [get_cells -hier -regexp {.*calendar/word_due_reg.*}]
opt_design -directive ExploreWithRemap
place_design -directive ExtraTimingOpt
phys_opt_design -directive AggressiveExplore
route_design -directive AggressiveExplore
phys_opt_design -directive AggressiveExplore
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file timing.rpt
report_timing -from [all_registers] -to [all_registers] -delay_type max -max_paths 40 -file internal_setup.rpt
report_timing -from [all_registers] -to [all_registers] -delay_type min -max_paths 40 -file internal_hold.rpt
report_timing -from $sram_in -to [all_registers] -delay_type max -max_paths 40 -file input_max.rpt
report_timing -from $sram_in -to [all_registers] -delay_type min -max_paths 40 -file input_min.rpt
report_timing -from [all_registers] -to $sram_out -delay_type max -max_paths 80 -file output_max.rpt
report_timing -from [all_registers] -to $sram_out -delay_type min -max_paths 80 -file output_min.rpt
report_utilization -file utilization.rpt
report_utilization -hierarchical -file hierarchy.rpt
report_io -file io.rpt
report_cdc -details -file cdc.rpt
report_bus_skew -file bus_skew.rpt
report_exceptions -file exceptions.rpt
report_exceptions -ignored -file ignored.rpt
report_clocks -file clocks.rpt
check_timing -verbose -file check_timing.rpt
report_route_status -file route.rpt
report_drc -file drc.rpt
write_checkpoint routed.dcp
write_xdc effective.xdc
puts "PHYSICAL_ROUTE_COMPLETE"
exit
