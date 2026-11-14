if {$argc!=3} {error "route.tcl output_directory adaptive(0/1) protected(0/1)"}
set here [file dirname [file normalize [info script]]]
lassign $argv dir adaptive protected
set out [file normalize $dir]
if {[file exists $out]} {error "fresh output required: $out"}
file mkdir $out
cd $out
set_param general.maxThreads 4
create_project -force route $out/project -part xc7z020clg484-1
foreach file {rule scan_engine controller config_repair board} {read_verilog -sv $here/rtl/$file.sv}
if {$protected} {
    create_ip -name sem -vendor xilinx.com -library ip -version 4.1 -module_name sem_core
    set ip [get_ips sem_core]
    set_property -dict [list CONFIG.ENABLE_INJECTION false CONFIG.INJECTION_SHIM none CONFIG.ENABLE_CORRECTION true CONFIG.CORRECTION_METHOD repair CONFIG.ENABLE_CLASSIFICATION false CONFIG.CLOCK_FREQ 50] $ip
    generate_target all $ip
    synth_ip $ip
    report_property $ip -file sem_properties.rpt
}
read_xdc $here/board.xdc
synth_design -top bank_board -part xc7z020clg484-1 -flatten_hierarchy none -generic ADAPTIVE=$adaptive -generic PROTECTED=$protected
set_clock_uncertainty -setup 0.5 [get_clocks *]
set_clock_uncertainty -hold 0.1 [get_clocks *]
set ins [get_ports {sram_err sram_dq[*]}]
set outs [get_ports {sram_a[*] sram_dq[*] sram_ce_n sram_oe_n sram_we_n sram_lb_n sram_ub_n}]
# Path budgets for asynchronous SRAM. External retention, setup and turnaround
# are composed from min/max data/clock arcs after routing. No multicycle waiver.
set_max_delay -datapath_only 2.5 -from $ins -to [all_registers]
set_min_delay 0 -from $ins -to [all_registers]
set_max_delay -datapath_only 5 -from [all_registers] -to $outs
set_min_delay 0 -from [all_registers] -to $outs
config_timing_corners -corner Slow -delay_type min_max
config_timing_corners -corner Fast -delay_type min_max
set pad_registers [get_cells -hier -regexp {.*core/(pad_addr|cs|oe|we)_reg.*}]
if {[llength $pad_registers]<20} {error "missing physical address/control FFs: $pad_registers"}
set_property CONTROL_SET_REMAP ALL $pad_registers
if {$protected} {
    set engines [get_cells -hier -filter {ORIG_REF_NAME == scan_engine || REF_NAME =~ scan_engine*}]
    if {[llength $engines]!=3} {error "expected three service replicas: $engines"}
    set_property DONT_TOUCH true $engines
    # Place one of three capture registers per external input in its ILOGIC.
    # The other two captures still sample that pad independently in the fabric.
    set captures [get_cells -hier -regexp {core/lane\[0\]\.u/(repair_image_reg\[[0-9]+\]|sampled_err_reg)}]
    if {[llength $captures]!=17} {error "missing primary capture registers: $captures"}
    set_property IOB TRUE $captures
    # Board-specific DQ0 input has the tightest routes. Retain distinct
    # capture slices next to its pad in both protected modes.
    foreach {lane loc} {1 SLICE_X112Y123 2 SLICE_X112Y122} {
        set cap [get_cells -hier -regexp [format {core/lane\[%d\]\.u/repair_image_reg\[0\]} $lane]]
        if {[llength $cap]!=1} {error "missing DQ0 capture for replica $lane"}
        set_property LOC $loc $cap
    }
}
opt_design
place_design -directive ExtraTimingOpt
phys_opt_design -directive AggressiveExplore
route_design -directive AggressiveExplore
phys_opt_design -directive AggressiveExplore
report_route_status -file route.rpt
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file timing.rpt
report_utilization -file utilization.rpt
report_io -file pins.rpt
report_drc -file drc.rpt
check_timing -verbose -file check.rpt
report_timing -max_paths 8 -delay_type max -file worst_setup.rpt
report_timing -max_paths 8 -delay_type min -file worst_hold.rpt
report_utilization -hierarchical -file hierarchy.rpt
report_power -file power.rpt
set fp [open cells.tsv w]
puts $fp "cell\tprimitive\tsite\tbel"
foreach c [lsort [get_cells -hier -filter {REF_NAME =~ FD* || REF_NAME =~ RAMB* || REF_NAME =~ ICAP* || REF_NAME =~ FRAME_ECC*}]] {
    puts $fp "$c\t[get_property REF_NAME $c]\t[get_property LOC $c]\t[get_property BEL $c]"
}
close $fp
set_property BITSTREAM.SEU.ESSENTIALBITS YES [current_design]
write_checkpoint routed.dcp
write_bitstream -force bank.bit
write_xdc effective.xdc
# Diagnostic I/O reports only. The acceptance constraints above are saved in DCP.
reset_timing
create_clock -name ref100 -period 10 [get_ports ref100]
set fclk [get_clocks -of_objects [get_pins clock_buffer/O]]
set_clock_uncertainty -setup 0.5 [get_clocks *]
set_clock_uncertainty -hold 0.1 [get_clocks *]
set_load 15 $outs
set_input_delay -clock $fclk -max 0 $ins
set_input_delay -clock $fclk -min 0 $ins
set_output_delay -clock $fclk -max 0 $outs
set_output_delay -clock $fclk -min 0 $outs
foreach corner {Slow Fast} {
    foreach kind {min max} {
        report_timing -from $ins -to [all_registers] -corner $corner -delay_type $kind -max_paths 150 -nworst 4 -file clocked_input_${corner}_${kind}.rpt
        report_timing -from [all_registers] -to $outs -corner $corner -delay_type $kind -max_paths 150 -nworst 4 -file clocked_output_${corner}_${kind}.rpt
        # The four worst paths to a bidirectional pad can all be T arcs.
        # Explicitly request data AND output-enable launches on each bit.
        foreach {signal group} {data data t_n direction} {
            set launch [get_cells -hier -regexp [format {.*core/%s_reg\[[0-9]+\]} $signal]]
            if {[llength $launch]!=16} {error "missing $signal pad FFs"}
            report_timing -from $launch -to [get_ports {sram_dq[*]}] -corner $corner -delay_type $kind -max_paths 64 -nworst 4 -file clocked_${group}_${corner}_${kind}.rpt
        }
    }
}
puts "T534_ROUTED_AND_BITSTREAM"
exit
