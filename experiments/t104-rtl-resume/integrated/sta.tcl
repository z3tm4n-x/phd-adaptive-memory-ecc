# Unchanged uncertainty and virtual boundary first: reveal full-logic critical
# paths, without hiding I/O failures or pretending this is the physical top.
if {$argc<2 || $argc>3} {error "part output-directory ?fast-floorplan? required"}
set part [lindex $argv 0]
set out [file normalize [lindex $argv 1]]
if {[file exists $out]} {error "output already exists"}
set here [file dirname [file normalize [info script]]]
file mkdir $out
cd $out
set_param general.maxThreads 4
create_project -in_memory -part $part
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
foreach f {async_queue.sv slow_queue.sv clock_250_50.sv} {read_verilog -sv [file join $here ../split $f]}
foreach f {e_backend_registered.sv handshake_channel.sv} {read_verilog -sv [file join $here ../registered $f]}
foreach f {event_fifo.sv segmented_counter.sv slow_rule.sv candidate_link.sv frame_engine.sv executor.sv clocked_top.sv} {read_verilog -sv [file join $here $f]}
read_xdc [file join $here ../split/component_input.xdc]
synth_design -top clocked_integrated -part $part -mode out_of_context -flatten_hierarchy rebuilt -fanout_limit 16
set fast_clock [get_clocks -of_objects [get_pins clocks/fast/O]]
set slow_clock [get_clocks -of_objects [get_pins clocks/slow/O]]
set_clock_uncertainty -setup 0.5 [get_clocks *]
set_clock_uncertainty -hold 0.1 [get_clocks *]
set slow_inputs [get_ports {startup_rst_slow qualified_start loss_slow request_valid[*] request_data[*] response_ready[*]}]
set slow_outputs [get_ports {request_ready[*] response_valid[*] response_data[*]}]
set fast_inputs [get_ports {mmcm_startup_reset startup_rst_fast dq_in[*] err_in}]
set fast_outputs [get_ports {locked word_out[*] ce oe we drive alias_high byte_enable[*] dq_out[*] fault}]
foreach direction {input output} {
    foreach domain {fast slow} {
        set_${direction}_delay -clock [set ${domain}_clock] -max 0.5 [set ${domain}_${direction}s]
        set_${direction}_delay -clock [set ${domain}_clock] -min 0.1 [set ${domain}_${direction}s]
    }
}
config_timing_corners -corner Slow -delay_type min_max
config_timing_corners -corner Fast -delay_type min_max
opt_design -directive ExploreWithRemap
if {$argc==3 && [lindex $argv 2]=="fast-floorplan"} {
    # Architectural placement experiment: keep the fast sequential island
    # and its RAM in one bounded region. No timing exceptions/clock changes.
    create_pblock fast_island
    set_property IS_SOFT false [get_pblocks fast_island]
    resize_pblock [get_pblocks fast_island] -add {SLICE_X36Y0:SLICE_X75Y49 RAMB36_X1Y0:RAMB36_X2Y9 RAMB18_X1Y0:RAMB18_X2Y19}
    add_cells_to_pblock [get_pblocks fast_island] [all_registers -clock $fast_clock]
    # Keep the independently closed atomic engine's logic as one island,
    # not only its registers with LUTs scattered through other fast logic.
    create_pblock e_island
    set_property IS_SOFT false [get_pblocks e_island]
    resize_pblock [get_pblocks e_island] -add {SLICE_X60Y25:SLICE_X75Y49}
    add_cells_to_pblock [get_pblocks e_island] [get_cells -hier -filter {NAME =~ controller/backend/*}]
}
place_design -directive ExtraTimingOpt
phys_opt_design -directive AggressiveExplore
route_design -directive AggressiveExplore
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file timing.rpt
report_timing -from [all_registers] -to [all_registers] -delay_type max -max_paths 20 -file internal_setup.rpt
report_timing -from [all_registers] -to [all_registers] -delay_type min -max_paths 20 -file internal_hold.rpt
report_utilization -file utilization.rpt
report_utilization -hierarchical -file hierarchy.rpt
report_cdc -details -file cdc.rpt
report_exceptions -file exceptions.rpt
report_exceptions -ignored -file ignored.rpt
report_clocks -file clocks.rpt
check_timing -verbose -file check_timing.rpt
report_route_status -file route.rpt
write_checkpoint routed.dcp
write_xdc effective.xdc
puts "INTEGRATED_ROUTE_COMPLETE $part"
exit
