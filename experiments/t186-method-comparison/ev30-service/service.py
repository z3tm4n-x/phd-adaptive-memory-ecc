"""Exact engineering bounds for one EV30/OFF service. No probability solver."""
from copy import deepcopy
from fractions import Fraction as F

NS = 10**9


def span(p, nominal, upper=True):
    return F(nominal)*F(p['clock_upper' if upper else 'clock_lower']) + (
        F(p['endpoint_span_ns']) if upper else -F(p['endpoint_span_ns']))


def count_before(horizon, first, step):
    """Integer physical-time offers in [0,horizon); no float or time stepping."""
    if min(horizon, first) < 0 or step <= 0:
        raise ValueError('invalid physical-time calendar')
    return max(0, (horizon-1-first)//step+1)


def workload(common):
    a = common['application']; h = a['epoch_ns']
    H = F(common['mission_s'])*NS
    if H.denominator != 1:
        raise ValueError('horizon must be integer SI ns')
    first = {k: a['first_ns']+a[k+'_offset_ns'] for k in ('read', 'write')}
    if not 0 <= a['read_offset_ns'] < a['write_offset_ns'] < h:
        raise ValueError('ordered strict-uniform streams required')
    counts = {k: count_before(int(H), first[k], h) for k in first}
    return dict(horizon_ns=int(H), first_ns=first, counts=counts,
                step_ns=h, spacing_ns=min(a['write_offset_ns']-a['read_offset_ns'],
                h-a['write_offset_ns']+a['read_offset_ns']),
                period_per_word_ns=common['words']*h,
                deadline_ns=common['constraints']['application_deadline_ns'])


def ac_limits(p):
    """Maximum adverse board/IO skew for each inequality, not actual delays.

    Intervals start at controller edges. Each row covers the aggregate relevant
    path(s), not a separate allowance for every component of that path.
    The same board implementation must satisfy all rows simultaneously.
    """
    ac=p['AC']; lo=lambda t:span(p,t,False)
    cyc=p['cycle_ns']; cap=p['read_capture_ns']
    setup=p['write_setup_ns']; pulse=p['write_pulse_ns']; hold=p['write_hold_ns']
    if setup+pulse+hold != cyc or not 0 < cap < cyc:
        raise ValueError('write partition/read capture does not fit cycle')
    limits={
        'read_cycle_shrink_ns':lo(cyc)-ac['tRC_min'],
        'write_cycle_shrink_ns':lo(cyc)-ac['tWC_min'],
        'read_address_CE_BE_board_capture_ns':lo(cap)-max(ac['tAA_max'],ac['tACE_max'],ac['tDBE_max']),
        'read_OE_board_capture_ns':lo(cap)-ac['tDOE_max'],
        # Do not spend SRAM tOHA as FPGA hold credit; next change could be OE.
        'read_capture_hold_and_skew_ns':lo(cyc-cap),
        'SRAM_release_extra_ns':lo(p['read_release_ns'])-ac['tHZOE_max'],
        'FPGA_disable_and_bus_settle_ns':lo(p['write_release_ns']),
        'WE_pulse_shrink_ns':lo(pulse)-ac['tPWE_min'],
        'address_CE_BE_to_write_end_skew_ns':lo(setup+pulse)-max(ac['tAW_min'],ac['tSCE_min'],ac['tBW_min']),
        'data_to_write_end_skew_ns':lo(setup+pulse)-ac['tSD_min'],
        'address_to_write_start_skew_ns':lo(setup)-ac['tSA_min'],
        'write_address_data_hold_skew_ns':lo(hold)-max(ac['tHA_min'],ac['tHD_min']),
        'supply_stable_wait_slack_ns':lo(p['post_supply_stable_wait_ns'])-ac['supply_stable_wait_min_ns'],
    }
    return dict(maximum_admissible_ns=limits,positive_margins=all(v>0 for v in limits.values()),
                actual_board_parameters=None,OE_during_write='HIGH',
                simultaneous_constraints=True,read_first_address_precedes_CE_BE_required=True,
                old_revision_exceptions_resolved_by_source_owner_only=True)


def transaction(p):
    b=p['cycle_ns'];d=p['decode_ns'];e=p['encode_ns']
    r=p['read_release_ns'];w=p['write_release_ns'];c=p['controller_budget_ns']
    if min(b,d,e,r,w,c)<0:
        raise ValueError('negative service budget')
    core={'read':3*b+d+r,'write':6*b+r+d+e+w,'initial':3*b+e+w}
    hi={k:span(p,v+c) for k,v in core.items()}
    core_hi={k:span(p,v) for k,v in core.items()}
    aperture=span(p,p['transaction_aperture_ns'],False)
    target=F(p['local_busy_target_fraction'])*aperture
    # Joint budget: the write constrains d+e+c. Margins are not independent.
    fixed=6*b+r+w
    sum_limit=(target-F(p['endpoint_span_ns']))/F(p['clock_upper'])-fixed
    c_limit=sum_limit-d-e
    hard_c=(aperture-F(p['endpoint_span_ns']))/F(p['clock_upper'])-core['write']
    return dict(core_nominal_ns=core,core_upper_ns=core_hi,
                full_upper_ns=hi,controller_allocation_nominal_ns=c,
                aperture_lower_ns=aperture,local_target_ns=target,
                busy_slack_ns=aperture-max(hi.values()),
                local_target_slack_ns=target-max(hi.values()),
                joint_decode_encode_controller_limit_ns=sum_limit,
                total_controller_limit_at_fixed_codec_ns=c_limit,
                additional_controller_to_target_ns=c_limit-c,
                total_controller_limit_hard_aperture_ns=hard_c,
                fits_aperture=max(hi.values())<=aperture,
                fits_local_target=max(hi.values())<=target,
                padding_reserved=False)


def peak_bound(w, durations, L):
    """Charge full work for every transaction intersecting any [u,u+L].

    Such offers lie within [u-D,u+L]. Both stream-specific spacing and merged
    minimum spacing apply. The maximization below only relaxes feasible counts.
    """
    length=L+w['deadline_ns']
    each=length//w['step_ns']+1
    total=min(2*each,length//w['spacing_ns']+1)
    candidates=[]
    for nr in range(each+1):
        for nw in range(each+1):
            if nr+nw<=total:
                candidates.append((nr*durations['read']+nw*durations['write'],nr,nw))
    amount,nr,nw=max(candidates)
    return dict(window_ns=L,expanded_offer_window_ns=length,
                each_stream_count_upper=each,merged_count_upper=total,
                maximizing_relaxed_counts={'read':nr,'write':nw},
                occupied_ns_upper=amount,fraction_upper=amount/F(L),
                excludes_pre_mission_initialization=True)


def evaluate(p, common):
    w=workload(common);tr=transaction(p);ac=ac_limits(p)
    a=common['application'];cc=common['constraints'];D=w['deadline_ns']
    inbound=a['inbound_ns']+a['ready_ns'];outbound=a['outbound_ns']+a['backpressure_ns']
    response={k:F(inbound+outbound)+tr['full_upper_ns'][k] for k in ('read','write')}
    maximum=max(response.values());spacing=w['spacing_ns']
    # Induction from the empty initial server: even the response to request i
    # ends before the next offer. No steady-state/average queue assumption.
    isolated=maximum<spacing
    peak=peak_bound(w,tr['full_upper_ns'],cc['peak_window_ns'])
    nr,nw=w['counts']['read'],w['counts']['write'];W=common['words'];T=F(common['mission_s'])
    init_bus=W*tr['full_upper_ns']['initial']
    core_sum=nr*tr['core_upper_ns']['read']+nw*tr['core_upper_ns']['write']+W*tr['core_upper_ns']['initial']
    full_sum=nr*tr['full_upper_ns']['read']+nw*tr['full_upper_ns']['write']+init_bus
    rates={'app_read':F(nr)/T,'app_write':F(nw)/T,'initialize_word':F(W)/T,
           'decode':F(nr+nw)/T,'encode':F(nw+W)/T,
           'read_x16':F(3*(nr+nw))/T,'write_x16':F(3*(nw+W))/T,
           'SRAM_release':F(nr+nw)/T,'FPGA_release':F(nw+W)/T,
           'app_dispatch':F(nr+nw)/T,'scrub':F(0),'adaptive_records':F(0)}
    ccoef={k:F(count)*F(p['clock_upper'])/(T*NS)
           for k,count in [('read_controller_ns',nr),('write_controller_ns',nw),('init_controller_ns',W)]}
    target_response=cc['map_targets']['response_ns']
    last={k:w['first_ns'][k]+(w['counts'][k]-1)*w['step_ns'] if w['counts'][k] else None for k in ('read','write')}
    result=dict(status='CONDITIONAL_ENGINEERING_RESULT_PENDING_REVIEW',
        physical_Q_upper=None,probability_computation_performed=False,
        workload=w,AC=ac,transactions=tr,
        service=dict(response_upper_ns=response,max_response_upper_ns=maximum,
            deadline_slack_ns=D-maximum,target_response_slack_ns=target_response-maximum,
            minimum_offer_spacing_ns=spacing,no_queue_induction=isolated,
            arrival_to_release_upper_ns=F(inbound)+tr['full_upper_ns']['write'],
            latest_arrival_ns=last,
            terminal_response_crossings={k:bool(last[k] is not None and last[k]+response[k]>w['horizon_ns']) for k in last},
            extra_blocking_to_target_ns=target_response-maximum,
            blocking_is_alternative_use_of_slack=True,physical_E_certified=False),
        peak=peak,
        price=dict(counts=w['counts'],work_rates_per_s=rates,
            core_mean_bus_fraction_upper=core_sum/(T*NS),
            mean_bus_fraction_upper_at_controller_budget=full_sum/(T*NS),
            mean_bus_controller_coefficients_per_nominal_ns=ccoef,
            full_mean_formula='core + sum(coeff_i*c_i) + B_extra_mean; c_i disjoint from codec/beat/release',
            full_peak_formula='peak_at_c_budget + B_extra_1ms; added blocking also consumes response/aperture slack',
            peak_extra_to_target=F(cc['map_targets']['peak_bus_fraction'])-peak['fraction_upper'],
            peak_extra_to_hard=F(cc['peak_bus_fraction'])-peak['fraction_upper'],
            payload_bytes=4*(nr+nw),payload_Bps=F(4*(nr+nw))/T,
            traffic_formula='payload + (nr+nw)*(request_header_B+reply_header_B)',
            CPU_fraction_formula='sum(rate_action*nonoverlapping_CPU_ns_action)/1e9 + CPU_background',
            energy_formula='sum(count_action*incremental_nonoverlapping_J_action) + T*idle_W + supply_wait_boot_J',
            controller_RAM_bytes=None,LUT=None,BRAM=None,CPU_fraction=None,energy_J=None,
            scalar_weights=None,all_history_and_full_pending_work_paid=True),
        initialization=dict(words=W,encodes=W,write_x16=3*W,
            active_bus_prefix_upper_ns=init_bus,
            selected_wait_upper_ns=span(p,p['post_supply_stable_wait_ns']),
            elapsed_after_supply_stable_excluding_unknown_boot_upper_ns=span(p,p['post_supply_stable_wait_ns'])+init_bus,
            elapsed_from_power_on_upper_ns=None,clean_start_escape_probability=None,
            bus_fraction_amortized=init_bus/(T*NS),
            synchronous_clean_t0_proven=False),
        capacity=dict(useful_bytes=W*4,active_code_bytes=W*44//8,
            allocated_bytes=W*6,installed_bytes=2097152,last_x16_address=3*W-1),
        risk_scope=dict(physical_moments_and_marks=None,physical_environment_exception=None,
            physical_initialization_exception=None,physical_E_and_service_exception=None,
            old_v4_quota_not_transferred=True,duplicate_exception_must_not_be_paid_twice=True),
        conditional_checks=dict(positive_AC_margins=ac['positive_margins'],
            aperture=tr['fits_aperture'],local_20percent=tr['fits_local_target'],
            response_hard=maximum<=D,response_target=maximum<=target_response,
            no_queue=isolated,peak_hard=peak['fraction_upper']<=F(cc['peak_bus_fraction']),
            peak_target=peak['fraction_upper']<=F(cc['map_targets']['peak_bus_fraction'])))
    return result


def sensitivity(p,common):
    rows=[]
    for key, values in p['sensitivity'].items():
        for value in values:
            q=deepcopy(p)
            if key=='cycles_ns':
                q['cycle_ns']=value;q['read_capture_ns']=value-8
                q['write_hold_ns']=value-q['write_setup_ns']-q['write_pulse_ns']
            elif key=='extra_controller_ns':q['controller_budget_ns']+=value
            elif key=='extra_each_codec_ns':q['decode_ns']+=value;q['encode_ns']+=value
            else:raise ValueError(key)
            x=evaluate(q,common)
            rows.append(dict(axis=key,value=value,
                response_ns=x['service']['max_response_upper_ns'],
                mean_bus_fraction=x['price']['mean_bus_fraction_upper_at_controller_budget'],
                peak_fraction=x['peak']['fraction_upper'],
                local_target_slack_ns=x['transactions']['local_target_slack_ns'],
                min_AC_margin_ns=min(x['AC']['maximum_admissible_ns'].values()),
                checks=x['conditional_checks']))
    return rows
