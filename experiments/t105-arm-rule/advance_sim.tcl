set here [file dirname [file normalize [info script]]]
set old [file normalize [file join $here ../t104-rtl-resume]]
set out [file normalize [lindex $argv 0]]
create_project advance_sim $out -part xc7z020clg484-1
set_property XPM_LIBRARIES {XPM_CDC} [current_project]
add_files [file join $old registered handshake_channel.sv]
add_files [file join $old physical frame_engine.sv]
foreach f {interval_guard.sv interval_link.sv} {add_files [file join $here $f]}
add_files -fileset sim_1 [file join $here tb_advance.sv]
set_property top tb_advance [get_filesets sim_1]
set_property generic [list PHASE=[lindex $argv 1]] [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property xsim.simulate.log_all_signals false [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
close_sim
exit
