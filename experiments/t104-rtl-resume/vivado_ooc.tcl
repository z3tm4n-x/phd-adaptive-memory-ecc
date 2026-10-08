# Optional, UNEXECUTED with Vivado in this delivery. No default device/XDC.
# This only prepares an out-of-context implementation, not a board/pin WCET
# or automatic timing PASS. Inspect reports, exceptions, CDC and XDC coverage.
# Usage: vivado -mode batch -source vivado_ooc.tcl -tclargs PART TIMING.xdc
# Command reference: https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands
if {$argc != 2} {
    error "Required: exact FPGA PART (including package/speed grade) and XDC; no defaults."
}
set part [lindex $argv 0]
set xdc [file normalize [lindex $argv 1]]
if {$part eq "" || ![file isfile $xdc] || [file size $xdc] == 0} {
    error "Missing explicit part or nonempty XDC. No platform result produced."
}
if {[llength [info commands synth_design]] == 0} {
    error "Run this script with Vivado, not a generic Tcl interpreter."
}
set matches [get_parts -quiet $part]
if {[llength $matches] != 1 || [get_property NAME $matches] ne $part} {
    error "PART must exactly name one device supported by this installation."
}
set here [file dirname [file normalize [info script]]]
set run_dir [file join $here .build "vivado-[clock microseconds]-[pid]"]
if {[file exists $run_dir]} {error "Refusing to overwrite existing run directory."}
file mkdir $run_dir
file copy $xdc [file join $run_dir supplied.xdc]
set original_dir [pwd]
cd $run_dir
set metadata [open run.txt w]
puts $metadata "scope: OOC; no automatic board, pin-WCET or physical-E qualification"
puts $metadata "Vivado: [version -short]"
puts $metadata "part: $part"
puts $metadata "XDC original: $xdc"
puts $metadata "UTC: [clock format [clock seconds] -gmt 1 -format {%Y-%m-%dT%H:%M:%SZ}]"
if {![catch {exec git -C $here rev-parse HEAD} revision]} {
    puts $metadata "source HEAD: $revision"
}
if {![catch {exec git -C $here status --porcelain -- .} dirty]} {
    puts $metadata "source task status (empty means tracked/untracked clean): $dirty"
}
close $metadata
set_param general.maxThreads 4
foreach module {e_backend absolute_calendar permission_gate service_config rpc_cdc
                app_frontend command_receiver executor_core executor} {
    read_verilog -sv [file join $here rtl "$module.sv"]
}
# The user-supplied XDC must establish all clocks/IO contracts and justified
# CDC constraints. Never blanket false-path the stable payload or Gray bus.
read_xdc [file join $run_dir supplied.xdc]
synth_design -top executor -part $part -mode out_of_context
foreach port {mem_clk cpu_clk x_clk command_clk} {
    if {[llength [get_clocks -quiet -of_objects [get_ports $port]]] == 0} {
        error "XDC left $port without a clock. No timing conclusion is possible."
    }
}
opt_design
place_design
phys_opt_design
route_design
check_timing -verbose -file check_timing.rpt
report_clocks -file clocks.rpt
report_cdc -details -file cdc.rpt
report_exceptions -file exceptions.rpt
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose -max_paths 20 -file timing.rpt
report_utilization -hierarchical -file utilization.rpt
report_drc -file drc.rpt
report_route_status -file route_status.rpt
write_checkpoint routed.dcp
cd $original_dir
puts "Reports: $run_dir"
puts "No automatic PASS: review constraints, unconstrained paths, setup/hold, CDC and physical IO."
