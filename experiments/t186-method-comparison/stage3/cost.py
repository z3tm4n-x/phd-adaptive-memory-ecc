"""Full cost basis, with unknown device costs kept as parameters."""
from fractions import Fraction as F


def ledger(result,method):
    H=result['horizon_ns'];a=result['algorithm'];app=result['application']
    adaptive=method['family']!='constant'
    cpu={'driver_base_cut':a['nominal_cut_services'],
         'consume_ERR_record':a['delivered_ERR'] if adaptive else 0,
         'decision_update':a['logical_updates'],
         'forecast_extra':a['full_hourly_forecasts'],
         'application_request':app['transport_request_records'],
         'application_completed_reply':app['transport_completed_reply_records']}
    # c_cut covers fixed driver/handshake work, c_ERR variable decoding,
    # c_decision the rule update; c_forecast its additional arithmetic.
    rates={k:str(F(v*10**9,H)) for k,v in cpu.items()}
    standalone={k:str(F(H,v)) if v else None for k,v in cpu.items()}
    return dict(
        memory_bus=result['bus'],
        memory_bus_fraction=str(F(result['bus']['total_ns'],H)),
        cpu_action_counts=cpu,cpu_action_rate_per_s_exact=rates,
        cpu_cost_ns_per_action={k:None for k in cpu},
        cpu_busy_fraction_formula='sum(N_i * c_i_ns) / horizon_ns',
        cpu_busy_fraction=None,
        standalone_necessary_c_i_ns_for_one_core=standalone,
        standalone_cap_scope='necessary one-term ceiling; other nonnegative costs make the jointly sufficient cap smaller',
        observation=dict(source_ERR=a['source_ERR'],delivered_ERR=a['delivered_ERR'],pending_ERR=a['pending_ERR'],
                         control_ERR=a['control_ERR'],observed_write_ERR=a['observed_write_ERR'],
                         collector_energy_per_record_J=None,transport_bits_per_record=None,
                         observed_write_preobservation_included_in_write32_bus=True),
        application_transport=dict(requests=app['transport_request_records'],completed_replies=app['transport_completed_reply_records'],
                                   pending=app['pending'],bits_per_request=None,bits_per_reply=None,
                                   energy_per_request_J=None,energy_per_reply_J=None),
        full_subsystem_energy_J=None,
        omitted_history_quota_scope='diagnostic histories have no injected false/loss/outage; full-contract expectation/upper quota terms await T196, not assumed zero outside these histories')


def resource_bounds(app,H):
    frames=-(-1000000//1568)+2
    E=F('148.501480');read=F('185.001840');write=F('217.002160')
    ac=app.interval_count_upper(1000000)
    peak=frames*8*E+ac*write
    response=320+1568+write+320+80
    counts=app.summary(H)['counts']
    means={kind:str(F(x['arrived']*10**9,H)) for kind,x in counts.items()}
    return dict(scope='conditional r4 service upper for declared application spacing; endpoint-excess recorded separately',
                peak_any_1ms_percent=float(peak/10000),peak_any_1ms_fraction_exact=str(peak/1000000),
                response_with_10_percent_ns=str(response*F(11,10)),
                control_with_10_percent_ns=str(E*F(11,10)),write_with_10_percent_ns=str(write*F(11,10)),
                peak_below_80_percent=peak<=800000,response_below_3us_with_reserve=response*F(11,10)<=3000,
                write_fits_240ns_with_reserve=write*F(11,10)<=240,
                joint_min_spacing_ge_100us=app.min_spacing is None or app.min_spacing>=100000,
                exact_arrival_mean_per_s=means,
                finite_interval_quiet_excess='possible at boundaries; at most per-residue endpoint counts, not waived',
                full_r4_certificate=False)
