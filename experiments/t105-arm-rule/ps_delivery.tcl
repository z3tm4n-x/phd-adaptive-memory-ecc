# Concrete PS7 GP0 -> standard SmartConnect -> AXI-Lite mailbox, all PL at50.
# No DDR or external memory is needed for the chosen OCM placement contract.
# This script is sourced by full_top.tcl inside a fresh project.
create_bd_design ps_delivery
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7]
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 {1} \
 CONFIG.PCW_USE_S_AXI_GP0 {0} CONFIG.PCW_UIPARAM_DDR_ENABLE {0} \
 CONFIG.PCW_CRYSTAL_PERIPHERAL_FREQMHZ {33.333333} \
 CONFIG.PCW_APU_PERIPHERAL_FREQMHZ {600}] $ps
set sc [create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 axi_path]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1} CONFIG.NUM_CLKS {1}] $sc
set ck [create_bd_port -dir I -type clk -freq_hz 50000000 aclk50]
set rn [create_bd_port -dir I -type rst aresetn]
set_property CONFIG.POLARITY ACTIVE_LOW $rn
set_property CONFIG.ASSOCIATED_RESET aresetn $ck
set bus [create_bd_intf_port -mode Master -vlnv xilinx.com:interface:aximm_rtl:1.0 M_AXI]
set_property -dict [list CONFIG.PROTOCOL AXI4LITE CONFIG.ADDR_WIDTH 32 \
 CONFIG.DATA_WIDTH 32 CONFIG.FREQ_HZ 50000000 CONFIG.HAS_BURST 0 \
 CONFIG.NUM_READ_OUTSTANDING 1 CONFIG.NUM_WRITE_OUTSTANDING 1] $bus
set_property CONFIG.ASSOCIATED_BUSIF M_AXI $ck
connect_bd_net $ck [get_bd_pins ps7/M_AXI_GP0_ACLK] [get_bd_pins axi_path/aclk]
connect_bd_net $rn [get_bd_pins axi_path/aresetn]
connect_bd_intf_net [get_bd_intf_pins ps7/M_AXI_GP0] [get_bd_intf_pins axi_path/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_path/M00_AXI] $bus
make_bd_intf_pins_external [get_bd_intf_pins ps7/FIXED_IO]
set_property name FIXED_IO [get_bd_intf_ports FIXED_IO_0]
assign_bd_address -offset 0x40000000 -range 4K [get_bd_addr_segs M_AXI/Reg]
validate_bd_design
save_bd_design
set bd [get_files ps_delivery.bd]
set_property synth_checkpoint_mode None $bd
generate_target all $bd
make_wrapper -files $bd -top
add_files [file join [get_property DIRECTORY [current_project]] t105_full.gen sources_1 bd ps_delivery hdl ps_delivery_wrapper.v]
update_compile_order -fileset sources_1
set fp [open ps7-address-and-clocks.txt w]
puts $fp "Tool: [version -short]; PS7 nominal clocks, not CPU WCET"
foreach p [lsort [list_property $ps]] {
 if {[regexp {^CONFIG.PCW_.*(APU|CPU|CRYSTAL|PLL|M_AXI_GP0|DDR).*} $p]} {
  puts $fp "$p = [get_property $p $ps]"
 }
}
foreach a [get_bd_addr_segs ps7/Data/*] {puts $fp "SEGMENT $a [get_property OFFSET $a] [get_property RANGE $a]"}
close $fp
