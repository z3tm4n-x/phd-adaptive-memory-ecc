# Conditional virtual-interface experiment, NOT a ZedBoard pin/board constraint.
# Same constraints for -1 and -2. Source clocks are independently phased.
create_clock -name mem_clk -period 4.000 [get_ports mem_clk]
create_clock -name cpu_clk -period 10.000 [get_ports cpu_clk]
create_clock -name x_clk -period 8.000 [get_ports x_clk]
create_clock -name command_clk -period 10.000 [get_ports command_clk]
# Engineering allowances, not measured board oscillator/MMCM specifications.
set_input_jitter [get_clocks mem_clk] 0.050
set_input_jitter [get_clocks cpu_clk] 0.050
set_input_jitter [get_clocks x_clk] 0.050
set_input_jitter [get_clocks command_clk] 0.050
set_property HD.CLK_SRC BUFGCTRL_X0Y0 [get_ports mem_clk]
set_property HD.CLK_SRC BUFGCTRL_X0Y1 [get_ports cpu_clk]
set_property HD.CLK_SRC BUFGCTRL_X0Y2 [get_ports x_clk]
set_property HD.CLK_SRC BUFGCTRL_X0Y3 [get_ports command_clk]
set_clock_uncertainty -setup 0.500 [get_clocks *]
set_clock_uncertainty -hold 0.100 [get_clocks *]

# Per-bit IO constraints are in virtual_io.tcl, sourced after synthesis.
# There are no clock groups or blanket interclock false paths here.
