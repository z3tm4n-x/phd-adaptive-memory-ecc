# Sourced as Tcl, NOT parsed as XDC (XDC rejects foreach).
# Classify each bit; do not accidentally clock the X interface with CPU clock.
foreach port [get_ports *] {
    set name [get_property NAME $port]
    if {$name in {mem_clk cpu_clk x_clk command_clk}} {continue}
    set domain mem_clk
    if {[string match cmd_* $name]} {set domain command_clk}
    if {[regexp {^(app_[a-z_]+)\[([0-9]+)\]$} $name -> bus bit]} {
        set width [dict get {app_valid 1 app_kind 2 app_word 19 app_data 32 app_mask 4 app_id 64 app_ready 1 app_reply_valid 1 app_reply_payload 97 app_reply_ready 1} $bus]
        set domain [expr {$bit < $width ? "cpu_clk" : "x_clk"}]
    }
    if {[get_property DIRECTION $port] eq "IN"} {
        set_input_delay -clock [get_clocks $domain] -max 0.500 $port
        set_input_delay -clock [get_clocks $domain] -min 0.100 $port
    } else {
        set_output_delay -clock [get_clocks $domain] -max 0.500 $port
        set_output_delay -clock [get_clocks $domain] -min 0.100 $port
    }
}
