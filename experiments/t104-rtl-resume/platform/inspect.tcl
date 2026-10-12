puts "T104_VERSION_BEGIN"
puts [version]
puts "T104_VERSION_END"
set installed [get_parts -quiet]
puts "T104_INSTALLED_PART_COUNT [llength $installed]"
puts "T104_INSTALLED_SAMPLE [lrange $installed 0 15]"
puts "T104_ZYNQ_MATCHES [get_parts -quiet *7z*]"
if {[llength $installed]} {report_property [lindex $installed 0]}
set missing {}
foreach part {xc7z020clg484-1 xc7z020clg484-2} {
    set found [get_parts -quiet $part]
    if {[llength $found] != 1} {
        lappend missing $part
        puts "T104_PART_UNAVAILABLE $part"
    } else {
        puts "T104_PART_AVAILABLE $part"
        report_property $found
    }
}
if {[llength $missing]} {
    puts "T104_PLATFORM_STATUS BLOCKED_DEVICE_SUPPORT"
    exit 2
}
puts "T104_PLATFORM_STATUS DEVICE_SUPPORT_AVAILABLE_NOT_STA"
exit 0
