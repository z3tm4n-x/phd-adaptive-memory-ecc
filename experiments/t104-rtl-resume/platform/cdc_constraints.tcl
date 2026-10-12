# Applied to a synthesized, hierarchy-preserved executor. Each selector fails
# closed when empty. These are conditional settling bounds, not MTBF evidence.
proc required_cells {pattern} {
    set cells [get_cells -hierarchical -regexp $pattern]
    if {[llength $cells] == 0} {error "CDC selector empty: $pattern"}
    puts "T104_CDC_CELLS $pattern [llength $cells]"
    return $cells
}
proc data_pins {cells} {
    return [get_pins -of_objects $cells -filter {REF_PIN_NAME == D}]
}
# Single-bit handshake/fault synchronizers: only D of the first FF is excepted.
# The remaining two stages retain ordinary setup/hold constraints.
set first [required_cells {.*(request_sync|consume_sync|response_sync|credit_sync|fault_cpu|fault_x)_reg\[0\]$}]
set_false_path -to [data_pins $first]

# Gray bus: transition separation is one memory tick (4 ns). Registration at
# its source is checked separately; skew < tick is not a cure for binary glitches.
set gray [required_cells {.*gt1_reg\[[0-9]+\]$}]
set gray_source [required_cells {.*published_gray_reg\[[0-9]+\]$}]
set_max_delay 4.000 -datapath_only -from $gray_source -to [data_pins $gray]
set_bus_skew 2.000 -from $gray_source -to [data_pins $gray]

# Bundled request: third sync stage exposes VALID; capture is the following
# receiver edge, >= 3 receiver periods after launch. 8 ns leaves >=4 ns at
# the minimum 12 ns separation. This applies to DATA and derived enable cones.
set request [required_cells {.*request_hold_reg\[[0-9]+\]$}]
set_max_delay 8.000 -datapath_only -from $request -to [all_registers -clock mem_clk -data_pins]

# Reply payload is held from memory release until consumption crosses back.
# It is delivered to a virtual source endpoint, not registered by this top.
# Earliest indication is >=2 source periods (16 ns minimum); 4 ns settling.
set reply [required_cells {.*response_hold_reg\[[0-9]+\]$}]
set_max_delay 4.000 -datapath_only -from $reply -to [get_ports {app_reply_payload[*] cmd_reply_payload[*]}]
# -datapath_only disables ordinary hold on ONLY these named CDC data paths;
# the handshake stability/retirement contract supplies the hold requirement.
