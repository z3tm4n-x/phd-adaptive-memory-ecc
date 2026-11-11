# Out-of-context synthesis of the reduced, clocked native controller.
set here [file dirname [file normalize [info script]]]
if {$argc!=1 || [lindex $argv 0] ni {0 1}} {error "select CHECK_LOCAL=0 or 1"}
create_project -in_memory -part xc7z020clg484-1
read_verilog -sv [file join $here native8.sv]
synth_design -top native8 -part xc7z020clg484-1 -mode out_of_context -generic CHECK_LOCAL=[lindex $argv 0]
create_clock -period 10 [get_ports clk]
report_utilization -file native8_utilization.rpt
report_timing_summary -file native8_timing.rpt
puts "NATIVE8_PART [get_property PART [current_design]]"
puts "NATIVE8_VIVADO [version -short]"
puts "NATIVE8_FF [llength [get_cells -hier -filter {REF_NAME =~ FD*}]]"
puts "NATIVE8_LUT [llength [get_cells -hier -filter {REF_NAME =~ LUT*}]]"
puts "NATIVE8_CARRY [llength [get_cells -hier -filter {REF_NAME == CARRY4}]]"
puts "NATIVE8_DATA_SETUP_SLACK [get_property SLACK [get_timing_paths -from [all_registers] -to [all_registers] -max_paths 1]]"
