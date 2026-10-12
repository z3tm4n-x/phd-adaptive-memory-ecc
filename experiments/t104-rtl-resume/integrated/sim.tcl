set here [file dirname [file normalize [info script]]]
set out [file normalize [lindex $argv 0]]
set phase [lindex $argv 1]
set stress [lindex $argv 2]
file mkdir $out
create_project integrated_sim $out -part xc7z020clg484-1
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
foreach f {async_queue.sv slow_queue.sv} {add_files [file join $here ../split $f]}
foreach f {e_backend_registered.sv handshake_channel.sv} {add_files [file join $here ../registered $f]}
foreach f {event_fifo.sv segmented_counter.sv slow_rule.sv candidate_link.sv frame_engine.sv executor.sv} {
    set source [file join $here $f]
    if {$argc>3 && [file exists [file join [lindex $argv 3] $f]]} {set source [file join [lindex $argv 3] $f]}
    add_files $source
}
add_files -fileset sim_1 [file join $here tb_integrated.sv]
set_property top tb_integrated [get_filesets sim_1]
set_property generic [list PHASE=$phase STRESS=$stress] [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property xsim.simulate.log_all_signals false [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
close_sim
exit
