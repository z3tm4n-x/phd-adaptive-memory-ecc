set here [file dirname [file normalize [info script]]]
set phase [lindex $argv 0]
set out [file normalize [lindex $argv 1]]
set stress [lindex $argv 2]
set bench [file normalize [lindex $argv 3]]
file mkdir $out
create_project registered_sim $out -part xc7z020clg484-1
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
foreach file {async_queue.sv slow_queue.sv} {
    add_files [file join $here ../split $file]
}
foreach file {operation_lane.sv generation_guard.sv e_backend_registered.sv handshake_channel.sv} {
    add_files [file join $here $file]
}
add_files -fileset sim_1 $bench
set_property top tb_lane [get_filesets sim_1]
set_property generic [list PHASE=$phase STRESS=$stress] [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property xsim.simulate.log_all_signals false [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
close_sim
exit
