# Reproducible full-width, full-top OOC implementation. No automatic PASS.
# vivado -mode batch -source implement.tcl -tclargs PART EMPTY_OUTPUT_DIR
if {$argc != 2} {error "Required: PART and new output directory"}
set part [lindex $argv 0]
if {$part ni {xc7z020clg484-1 xc7z020clg484-2}} {error "Unregistered platform"}
set out [file normalize [lindex $argv 1]]
if {[file exists $out]} {error "Refusing to overwrite $out"}
file mkdir $out
set here [file dirname [file normalize [info script]]]
cd $out
set_param general.maxThreads 4
create_project -in_memory -part $part
foreach module {e_backend absolute_calendar permission_gate service_config rpc_cdc app_frontend command_receiver executor_core executor} {
    read_verilog -sv [file join $here .. rtl $module.sv]
}
read_xdc [file join $here ooc.xdc]
synth_design -top executor -part $part -mode out_of_context -flatten_hierarchy none
source [file join $here virtual_io.tcl]
source [file join $here cdc_constraints.tcl]
config_timing_corners -corner Slow -delay_type min_max
config_timing_corners -corner Fast -delay_type min_max
# This command configures POWER estimation; it does not set STA PVT corners.
set_operating_conditions -grade commercial -process maximum -junction_temp 85
report_operating_conditions -all -file power_operating_conditions.rpt
report_property [current_design] -file design_properties.rpt
report_utilization -hierarchical -file synthesized_utilization.rpt
check_timing -verbose -file synthesized_check_timing.rpt
write_checkpoint synthesized.dcp
opt_design
place_design
phys_opt_design
route_design
check_timing -verbose -file check_timing.rpt
report_clocks -file clocks.rpt
report_property [get_clocks mem_clk] -file memory_clock_properties.rpt
report_clock_interaction -file clock_interaction.rpt
report_cdc -details -file cdc.rpt
report_exceptions -file exceptions.rpt
report_exceptions -ignored -file exceptions_ignored.rpt
report_bus_skew -file bus_skew.rpt
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -max_paths 3 -file timing.rpt
report_timing -delay_type min_max -path_type full_clock_expanded -input_pins -max_paths 20 -nworst 1 -file longest_paths.rpt
report_timing -from [get_clocks mem_clk] -to [get_clocks mem_clk] -max_paths 10 -path_type full_clock_expanded -file memory_paths.rpt
report_utilization -hierarchical -file utilization.rpt
report_utilization -file resources.rpt
report_drc -file drc.rpt
report_route_status -file route_status.rpt
write_checkpoint routed.dcp
write_xdc effective.xdc
puts "T104_IMPLEMENTATION_COMPLETED $part $out"
exit
