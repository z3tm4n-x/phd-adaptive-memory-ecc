# Read-only diagnosis of a routed checkpoint; no timing exceptions are added.
open_checkpoint [lindex $argv 0]
set out [lindex $argv 1]
set sources [get_pins -hier -filter {NAME =~ *history* && REF_PIN_NAME == C}]
set targets [get_pins -hier -filter {NAME =~ *history* && REF_PIN_NAME == D}]
report_timing -from $sources -to $targets -delay_type min -max_paths 20 -file ${out}-history-min.rpt
report_design_analysis -congestion -file ${out}-congestion.rpt
report_high_fanout_nets -timing -max_nets 30 -file ${out}-fanout.rpt
report_timing -from [get_ports err_in] -to [get_pins controller/backend/err_due_reg/D] -delay_type min -file ${out}-err-input-hold.rpt
report_timing -from [get_ports err_in] -to [get_pins controller/backend/err_due_reg/D] -delay_type max -file ${out}-err-input-setup.rpt
report_timing -from [get_pins -hier -filter {NAME =~ controller/backend/step_reg* && REF_PIN_NAME == C}] -to [get_pins controller/backend/err_due_reg/D] -delay_type min -file ${out}-err-internal-hold.rpt
exit
