# Configuration availability only. No bitstream, board access or STA claim.
set out [file normalize [lindex $argv 0]]
file mkdir $out
create_project t105_ps_probe $out/project -part xc7z020clg484-1 -force
create_bd_design ps_probe
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7]
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 {1} \
 CONFIG.PCW_CRYSTAL_PERIPHERAL_FREQMHZ {33.333333} \
 CONFIG.PCW_APU_PERIPHERAL_FREQMHZ {600}] $ps
set aclk [create_bd_port -dir I -type clk -freq_hz 50000000 aclk50]
connect_bd_net $aclk [get_bd_pins $ps/M_AXI_GP0_ACLK]
set validation_code [catch {validate_bd_design} validation_text]
set fp [open $out/configuration.txt w]
puts $fp "TYPE: Vivado PS7 configuration probe, not measured clocks/WCET"
puts $fp "TOOL: [version -short]"
puts $fp "PART: [get_property PART [current_project]]"
puts $fp "PROBE_BD_VALIDATION_CODE: $validation_code"
puts $fp "PROBE_BD_VALIDATION_TEXT: $validation_text"
puts $fp "ACLK50_PORT_HZ: [get_property CONFIG.FREQ_HZ $aclk]"
foreach p [lsort [list_property $ps]] {
 if {[regexp {^CONFIG.PCW_.*(APU|CPU|CRYSTAL|PLL|M_AXI_GP0).*} $p]} {
  puts $fp "$p = [get_property $p $ps]"
 }
}
close $fp
save_bd_design
exit
