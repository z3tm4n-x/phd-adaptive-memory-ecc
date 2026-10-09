# Local synchronous cutpoint characterization, NOT a board timing result.
if {$argc!=2} {error "part output-directory required"}
set part [lindex $argv 0]
if {$part ni {xc7z020clg484-1 xc7z020clg484-2}} {error "undeclared part"}
set here [file dirname [file normalize [info script]]]
set out [file normalize [lindex $argv 1]]
if {[file exists $out]} {error "output already exists"}
file mkdir $out
cd $out
set_param general.maxThreads 4
create_project -in_memory -part $part
read_verilog -sv [file join $here e_backend_registered.sv]
synth_design -top e_backend_registered -part $part -mode out_of_context
create_clock -name fast -period 4 [get_ports clk]
set_input_jitter [get_clocks fast] .05
set_clock_uncertainty -setup .5 [get_clocks fast]
set_clock_uncertainty -hold .1 [get_clocks fast]
set inputs [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_input_delay -clock fast -max .5 $inputs
set_input_delay -clock fast -min .1 $inputs
set_output_delay -clock fast -max .5 [all_outputs]
set_output_delay -clock fast -min .1 [all_outputs]
config_timing_corners -corner Slow -delay_type min_max
config_timing_corners -corner Fast -delay_type min_max
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file timing.rpt
report_timing -from [all_registers] -to [all_registers] -delay_type max -max_paths 10 -file internal_setup.rpt
report_timing -from [all_registers] -to [all_registers] -delay_type min -max_paths 10 -file internal_hold.rpt
report_utilization -file utilization.rpt
check_timing -verbose -file check_timing.rpt
report_exceptions -ignored -file ignored.rpt
report_route_status -file route.rpt
write_checkpoint routed.dcp
write_xdc effective.xdc
puts "REGISTERED_BACKEND_ROUTE_COMPLETE $part"
exit
