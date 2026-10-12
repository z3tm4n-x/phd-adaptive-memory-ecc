# Internal component timing only. Virtual I/O is not SRAM/FMC pad timing.
if {$argc!=2} {error "part output-directory required"}
set part [lindex $argv 0]
if {$part ni {xc7z020clg484-1 xc7z020clg484-2}} {error "part not declared"}
set out [file normalize [lindex $argv 1]]
if {[file exists $out]} {error "output already exists"}
set here [file dirname [file normalize [info script]]]
file mkdir $out
cd $out
set_param general.maxThreads 4
create_project -in_memory -part $part
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
foreach file {async_queue.sv slow_queue.sv handshake_channel.sv predecision_guard.sv operation_lane.sv clock_250_50.sv clocked_lane.sv} {
    read_verilog -sv [file join $here $file]
}
read_verilog -sv [file join $here ../rtl/e_backend.sv]
read_xdc [file join $here component_input.xdc]
synth_design -top clocked_lane -part $part -mode out_of_context -flatten_hierarchy none
# Actual common MMCM: no disconnected generated clock at a second input port.
set fast_clock [get_clocks -of_objects [get_pins clocks/fast/O]]
set slow_clock [get_clocks -of_objects [get_pins clocks/slow/O]]
if {[llength $fast_clock]!=1 || [llength $slow_clock]!=1} {error "missing generated clocks"}
set_clock_uncertainty -setup 0.5 [get_clocks *]
set_clock_uncertainty -hold 0.1 [get_clocks *]
set slow_inputs [get_ports {startup_rst_slow soft_loss_slow request_valid request_data[*] response_ready}]
set slow_outputs [get_ports {request_ready response_valid response_data[*] queues_ready_slow}]
set fast_inputs [get_ports {mmcm_startup_reset startup_rst_fast dq_in[*] err_in}]
set fast_outputs [get_ports {locked word_out[*] ce oe we drive alias_high byte_enable[*] dq_out[*] protocol_fault}]
foreach direction {input output} {
    foreach domain {fast slow} {
        set ports [set ${domain}_${direction}s]
        set_${direction}_delay -clock [set ${domain}_clock] -max 0.5 $ports
        set_${direction}_delay -clock [set ${domain}_clock] -min 0.1 $ports
    }
}
config_timing_corners -corner Slow -delay_type min_max
config_timing_corners -corner Fast -delay_type min_max
write_xdc before_route.xdc
set channel [open before_route.xdc r]
set constraints [read $channel]
close $channel
if {[regexp {set_max_delay[^\n]*(1000\.000|3003\.000)} $constraints]} {
    error "XPM used fallback periods: source clock must be loaded before scoped IP constraints"
}
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file timing.rpt
report_timing -from [all_registers -clock $fast_clock] -to [all_registers -clock $fast_clock] -delay_type max -max_paths 10 -file fast_setup.rpt
report_timing -from [all_registers -clock $fast_clock] -to [all_registers -clock $fast_clock] -delay_type min -max_paths 10 -file fast_hold.rpt
report_clocks -file clocks.rpt
report_utilization -file utilization.rpt
report_utilization -hierarchical -file hierarchy.rpt
report_cdc -details -file cdc.rpt
report_exceptions -file exceptions.rpt
report_exceptions -ignored -file ignored.rpt
report_clock_interaction -file interactions.rpt
check_timing -verbose -file check_timing.rpt
report_route_status -file route.rpt
write_checkpoint routed.dcp
write_xdc effective.xdc
puts "SPLIT_COMPONENT_ROUTE_COMPLETE $part"
exit
