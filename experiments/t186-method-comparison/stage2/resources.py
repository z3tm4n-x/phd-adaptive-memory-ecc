"""All-history service upper bounds for this episode application envelope."""
from fractions import Fraction as F


def calculate(cfg):
    # A 1 ms window meets no more than ceil(1e6/1568)+2 frames.
    frames=-(-1000000//1568)+2
    E,R,read=F('148.501480'),F('92.500920'),F('185.001840')
    response=320+1568+read+320+80
    spacing=cfg['application']['period_s']*10**9
    assert spacing>1000000+response
    # Fixed sparse arrivals: no more than one overlapping application read.
    peak=frames*8*E+read
    flags=dict(peak_below_80_percent=peak<=800000,control_with_10_percent_fits=E*F(11,10)<=164,
               read_with_10_percent_fits=read*F(11,10)<=240,response_with_10_percent_below_3us=response*F(11,10)<=3000)
    assert all(flags.values())
    return dict(scope='conditional r4 scalar service upper, all methods, all histories of registered sparse read-only load; not measured WCET/STA',
                peak_any_1ms_bus_percent_exact=str(peak/10000),peak_any_1ms_bus_percent=float(peak/10000),
                control_with_10_percent_ns=str(E*F(11,10)),read_with_10_percent_ns=str(read*F(11,10)),
                response_with_10_percent_ns=str(response*F(11,10)),flags=flags,
                algorithm_CPU_time_and_energy=None,full_application_write_load='not implemented in stage2',
                nominal_delivery_cut_ns=188160,full_r4_ERR_rule_budget_ns=10000,
                nominal_cut_transfer_to_full_r4='not established; immediate local veto preserved, cut exceeds r4 budget')
