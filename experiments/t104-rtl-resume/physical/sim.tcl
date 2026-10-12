set here [file dirname [file normalize [info script]]]
set out [file normalize [lindex $argv 0]]
file mkdir $out
create_project physical_sim $out -part xc7z020clg484-1
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
foreach f {async_queue.sv slow_queue.sv} {add_files [file join $here ../split $f]}
foreach f {e_backend_registered.sv handshake_channel.sv} {
 set p [file join $here $f]
 if {![file exists $p]} {set p [file join $here ../registered $f]}
 add_files $p
}
foreach f {event_fifo.sv segmented_counter.sv slow_rule.sv candidate_link.sv frame_engine.sv executor.sv} {
 set p [file join $here $f]
 if {![file exists $p]} {set p [file join $here ../integrated $f]}
 add_files $p
}
add_files -fileset sim_1 [file join $here ../integrated tb_integrated.sv]
set_property top tb_integrated [get_filesets sim_1]
set_property generic [list PHASE=[lindex $argv 1] STRESS=[lindex $argv 2]] [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property xsim.simulate.log_all_signals false [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
close_sim
exit

