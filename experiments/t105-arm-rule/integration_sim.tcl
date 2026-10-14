set here [file dirname [file normalize [info script]]]
set old [file normalize [file join $here ../t104-rtl-resume]]
set out [file normalize [lindex $argv 0]]
set dpi [file normalize [lindex $argv 3]]
create_project arm_sim $out -part xc7z020clg484-1
set_property XPM_LIBRARIES {XPM_CDC XPM_FIFO XPM_MEMORY} [current_project]
foreach f {async_queue.sv slow_queue.sv} {add_files [file join $old split $f]}
add_files [file join $old registered handshake_channel.sv]
add_files [file join $old integrated event_fifo.sv]
foreach f {segmented_counter.sv frame_engine.sv e_backend_registered.sv} {add_files [file join $old physical $f]}
foreach f {history_batch.sv rule_mailbox.sv interval_guard.sv interval_link.sv arm_executor.sv} {add_files [file join $here $f]}
add_files -fileset sim_1 [file join $here tb_arm.sv]
set_property top tb_arm [get_filesets sim_1]
set generics [list PHASE=[lindex $argv 1] STRESS=[lindex $argv 2]]
if {[llength $argv]>4} {lappend generics CYCLES=[lindex $argv 4]}
set_property generic $generics [get_filesets sim_1]
set_property -dict [list xsim.elaborate.xelab.more_options "-sv_lib dpi -sv_root $dpi"] [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property xsim.simulate.log_all_signals false [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
close_sim
exit
