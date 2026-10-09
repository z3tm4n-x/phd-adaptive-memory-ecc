# Read BEFORE synthesis so scoped XPM constraints see the actual periods.
set_property PACKAGE_PIN Y9 [get_ports ref100]
create_clock -name ref100 -period 10 [get_ports ref100]
set_input_jitter [get_clocks ref100] 0.05
