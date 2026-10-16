set here [file dirname [file normalize [info script]]]
set out [file normalize [lindex $argv 0]]
create_project time_format [file join $out time_project] -part xc7z020clg484-1 -force
add_files -fileset sim_1 [file join $here tb_time_format.sv]
set_property top tb_time_format [get_filesets sim_1]
set_property xsim.simulate.runtime all [get_filesets sim_1]
set_property xsim.simulate.log_all_signals false [get_filesets sim_1]
launch_simulation -simset sim_1 -mode behavioral
close_sim
exit
