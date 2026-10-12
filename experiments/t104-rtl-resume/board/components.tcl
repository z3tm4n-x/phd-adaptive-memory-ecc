# Separate component elaboration; NOT timing closure of executor or pads.
set here [file dirname [file normalize [info script]]]
set out [file normalize [lindex $argv 0]]
file mkdir $out
set_param general.maxThreads 4
read_verilog -sv $here/clock_tree.sv
synth_design -top clock_tree -part xc7z020clg484-1 -mode out_of_context
set_property PACKAGE_PIN Y9 [get_ports board_100mhz]
set_property IOSTANDARD LVCMOS33 [get_ports board_100mhz]
create_clock -name board_100 -period 10 [get_ports board_100mhz]
set_input_jitter [get_clocks board_100] 0.05
report_clocks -file $out/clocks.rpt
report_utilization -file $out/clock_utilization.rpt
set f [open $out/clock_properties.rpt w]
foreach c [get_clocks] {puts $f "CLOCK $c [get_property PERIOD $c] [get_property IS_GENERATED $c]"}
foreach c [get_cells -hier -filter {REF_NAME =~ MMCME2*}] {puts $f [report_property -return_string $c]}
close $f
write_checkpoint -force $out/clock_synth.dcp
close_design
read_verilog -sv $here/sram_pads.sv
synth_design -top sram_pads -part xc7z020clg484-1 -mode out_of_context
source $out/fmc_pins.xdc
report_utilization -file $out/pad_utilization.rpt
report_io -file $out/pad_io.rpt
set f [open $out/pad_properties.rpt w]
puts $f "IOBUF_COUNT [llength [get_cells -hier -filter {REF_NAME == IOBUF}]]"
foreach p [concat [get_ports sram_a*] [get_ports sram_dq*] [get_ports sram_*_n] [get_ports sram_err]] {
    puts $f "PAD $p [get_property PACKAGE_PIN $p] [get_property IOSTANDARD $p]"
}
close $f
write_checkpoint -force $out/pad_synth.dcp
puts "T104_BOARD_COMPONENTS_COMPLETE"
