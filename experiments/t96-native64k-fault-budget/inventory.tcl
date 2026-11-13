# Read the existing routed design. No implementation or configuration writes.
if {$argc != 2} {error "inventory.tcl routed.dcp output.tsv"}
open_checkpoint [lindex $argv 0]
if {[get_property PART [current_design]] ne "xc7z020clg484-1"} {error "wrong routed part"}
set f [open [lindex $argv 1] w]
puts $f "cell\tprimitive\tsite\tbel"
foreach c [lsort [get_cells -hier -filter {REF_NAME =~ FD*}]] {
    set site [get_property LOC $c]
    set bel [get_property BEL $c]
    if {$site eq "" || $bel eq ""} {error "unplaced FF $c"}
    puts $f "$c\t[get_property REF_NAME $c]\t$site\t$bel"
}
close $f
close_design
