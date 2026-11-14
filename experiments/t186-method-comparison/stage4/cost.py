"""Full attributed cost vector. Time/energy per action remain parameters."""
from fractions import Fraction as F

def ledger(r,spec):
    a=r['algorithm'];H=r['horizon_ns'];app=r['application']
    actions=dict(common_cut=a['nominal_cut_services'],common_packet_ready=a['nominal_ready_services'],
                 source_capture=a['source_records'],record_process=a['source_records']-a['pending_records']-a['dropped_records'],
                 decision_update=a['logical_updates'],precomputed_expiry=a['precomputed_expiry_evaluations'],
                 forecast_extra=a['full_hourly_forecasts'],application_request=app['transport_request_records'],
                 application_reply=app['transport_completed_reply_records'],
                 source_state_check_extra=a['source_state_checks'],prefix_check_extra=a['prefix_checks'],
                 loss_transition_extra=a['loss_state_checks'])
    Hs=F(H,10**9);X=F(209)+F(H,10000)
    standalone={k:str(F(H,v)) if v else None for k,v in actions.items()}
    nominal_patent_max=(60*10**9)//4+1 if spec['family']=='patent' else None
    return dict(memory_bus=r['bus'],memory_bus_fraction_exact=r['mean_bus_fraction_exact'],
                action_counts=actions,action_rates_per_s_exact={k:str(F(v,1)/Hs) for k,v in actions.items()},
                time_ns_per_action={k:None for k in actions},energy_J_per_action={k:None for k in actions},
                attributed_CPU_fraction_formula='sum(N_i*c_i_ns)/T_ns; separate from SRAM; per-action scopes must not overlap',
                attributed_CPU_fraction=None,energy_J=None,
                conditional_one_core_individual_caps_ns=standalone,
                cap_scope='necessary one-term ceilings only if all attributed work completes inside T; tails/other actions reduce available budget',
                packet_record_bytes=32,source_record_bytes=32*a['source_records'],
                processed_record_bytes=32*actions['record_process'],common_header_bytes_per_cut=None,
                buffer_reserved_bytes=a['transport_reserved_bytes'],buffer_peak_live_payload_bytes=32*a['peak_transport_records'],
                loss_state_reserved_bytes=a['loss_state_reserved_bytes'],
                loss_state_scope='64-byte packed control allocation beyond transport: two G64 watermarks, before-edge health/watermark/counter snapshot, health/UNKNOWN flags; audit traces/counters are separate simulation output',
                loss_work_scope='new extra action coefficients exclude base capture/record/decision work; all processing and storage must fit the existing 3900ns/X contract',
                policy_state=dict(peak_timestamp_records=a['peak_policy_timestamp_records'],
                                  nominal_dense_patent_window_records_upper=nominal_patent_max,
                                  nominal_timestamp_payload_bytes_upper=8*nominal_patent_max if nominal_patent_max else None,
                                  scope='timestamp queue beyond transport; nominal source4ns bound, metadata/clock margins extra; forecast cache is simulation-only',
                                  actual_controller_state_bytes=None),
                pending=dict(application=app['pending'],records=a['pending_records'],inflight=a['pending_inflight'],captured=a['pending_captured']),
                protected_SRAM_extra=dict(numerical_extra_ns=0,
                    assumption='packet/policy state lives outside the compared SRAM; no added protected-SRAM transactions in this conditional executor',
                    physical_placement_verified=False,physical_extra_ns_per_action=None,
                    total_existing_X_upper_ns=str(X),mean_ns_per_cut_if_all_X=str(X/a['nominal_cut_services']) if a['nominal_cut_services'] else None,
                    condition='all additional work, jointly with existing X, must obey 209ns + 1e-4*interval_ns for every interval; a total average alone is insufficient'),
                fault_price_scope='history counters here; full expected/global-bad/false/outage/recovery terms are retained in bounds.json, not zeroed by an empty trace')
