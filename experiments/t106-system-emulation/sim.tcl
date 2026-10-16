set here [file dirname [file normalize [info script]]]
set old [file normalize [file join $here ../t104-rtl-resume]]
set arm [file normalize [file join $here ../t105-arm-rule]]
set out [file normalize [lindex $argv 0]]
create_project system_sim [file join $out project] -part xc7z020clg484-1
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
foreach f {async_queue.sv slow_queue.sv} {add_files [file join $old split $f]}
add_files [file join $old registered handshake_channel.sv]
add_files [file join $old integrated event_fifo.sv]
foreach f {segmented_counter.sv frame_engine.sv e_backend_registered.sv} {add_files [file join $old physical $f]}
foreach f {history_batch.sv rule_mailbox.sv interval_guard.sv interval_link.sv arm_executor.sv} {add_files [file join $arm $f]}
add_files -fileset sim_1 [file join $here tb_system.sv]
set_property top tb_system [get_filesets sim_1]
set_property -dict [list xsim.elaborate.xelab.more_options "-sv_lib bridge -sv_root $out"] [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property xsim.simulate.log_all_signals false [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
close_sim
exit
