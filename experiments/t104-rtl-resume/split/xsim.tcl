# Reuse installed vendor IP; do not copy it into the research repository.
set here [file dirname [file normalize [info script]]]
set phase [lindex $argv 0]
set out [file normalize [lindex $argv 1]]
set stress [lindex $argv 2]
file mkdir $out
create_project split_sim $out -part xc7z020clg484-1
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
add_files [list [file join $here async_queue.sv] [file join $here slow_queue.sv] \
    [file join $here handshake_channel.sv] [file join $here operation_lane.sv] \
    [file join $here predecision_guard.sv] [file join $here ../rtl/e_backend.sv]]
add_files -fileset sim_1 [file join $here tb_lane.sv]
set_property top tb_lane [get_filesets sim_1]
set_property generic [list PHASE=$phase STRESS=$stress] [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property xsim.simulate.log_all_signals false [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
close_sim
exit
