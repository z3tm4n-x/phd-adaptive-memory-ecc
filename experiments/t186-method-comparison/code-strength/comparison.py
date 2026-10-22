"""Exact conditional three-row comparison, with explicitly parameterized cost.

No Monte Carlo, physical qualification, or optimized-class claim is made.
All probabilistic quantities are bounds over the whole declared horizon.
"""
from fractions import Fraction as F
from math import comb
from copy import deepcopy

from cost import per_bit_moment_caps, periodic_starts
from parents import projected_groups, witness_coefficients

NS=10**9

def ceil(x):
    x=F(x)
    return -(-x.numerator//x.denominator)


def service(cfg,n):
    s=cfg['service']; xp=F(s['clock_upper']); xm=F(s['clock_lower'])
    J=F(s['operation_endpoint_span_ns'])
    r=3*s['read_beat_ns']; wr=3*s['write_beat_ns']; u=s['turnaround_ns']
    d=s[f'decode{n}_ns']; e=s[f'encode{n}_ns']
    nominal=dict(R=r+d,E=r+d+wr+u,app_read=r+d,
                 app_write=r+d+e+wr+u,initial=e+wr+u)
    return dict(nominal=nominal,upper={k:F(v)*xp+J for k,v in nominal.items()},
                lower={k:max(F(0),F(v)*xm-J) for k,v in nominal.items()},
                xminus=xm,xplus=xp,J=J,decode=d,encode=e)


def risk(cfg,n,t,P_ns,d_ns,p=None):
    """T196(5),(6) with explicit deterministic E-cross majorant.

    For constant p, Phi(x)=A2*x²+A3*x³ in per-bit integrated mass x.
    J intervals are disjoint; H need only have mass <= B*d. Therefore
    sum J²<=P*S2 and sum J<=S1 control every cross term separately.
    """
    p=p or {1:F(1)}
    m=per_bit_moment_caps(cfg)
    a=witness_coefficients(n,t,projected_groups(n,p))
    W=cfg['words'];P=F(P_ns,NS);d=F(d_ns,NS);B=m['peak_per_bit']
    direct=W*a['linear_direct']*m['M1']
    quadratic=W*a['quadratic']*P*m['M2']
    cubic=W*a['cubic']*P*P*m['M3']
    cross2=W*2*a['quadratic']*B*d*m['M1']
    cross3=W*3*a['cubic']*(B*d*P*m['M2']+B*B*d*d*m['M1'])
    delta=F(cfg['lifetime_other_budget'])
    raw=delta+direct+quadratic+cubic+cross2+cross3
    eps=F(cfg['epsilon'])
    return dict(upper=min(F(1),raw),unclipped=raw,slack=eps-min(F(1),raw),
                relative_slack=(eps-min(F(1),raw))/eps,
                terms=dict(lifetime_exceptions=delta,direct=direct,initial=F(0),
                           quadratic=quadratic,cubic=cubic,E_cross_quadratic=cross2,E_cross_cubic=cross3),
                coefficients=a,moments=m,
                basis='T196(5), deterministic mandatory support; extra correct E writes ignored',
                exact_probability=None,physical_unconditional_probability=None)


def period(cfg,k):
    s=cfg['service'];P=cfg['words']*cfg['calendar']['g_ticks']*k
    return dict(nominal_ns=P,upper_ns=P*F(s['clock_upper'])+F(s['operation_endpoint_span_ns']),
                lower_ns=P*F(s['clock_lower'])-F(s['operation_endpoint_span_ns']))


def select_fixed(cfg,n,t):
    d=service(cfg,n)['upper']['E'];target=F(cfg['epsilon'])/2
    def valid(k):return risk(cfg,n,t,period(cfg,k)['upper_ns'],d)['upper']<=target
    if not valid(1):raise ValueError('no fixed candidate on the preregistered grid')
    lo,hi=1,2
    while valid(hi):
        lo,hi=hi,2*hi
        if hi>cfg['fixed']['search_cap_k']:raise ValueError('selection search cap reached')
    while hi-lo>1:
        mid=(lo+hi)//2
        if valid(mid):lo=mid
        else:hi=mid
    return lo


def read_bounds(cfg,k):
    """First fast pass plus periodic support, arbitrary bounded initial phase.

    Whole started operations including a terminal unfinished operation are
    charged. +2W pays startup/edge effects without replacing them by zero.
    """
    H=cfg['mission_s']*NS;W=cfg['words'];P=period(cfg,k)
    return dict(upper=W*(F(H)/P['lower_ns']+2),
                lower=max(F(0),W*(F(H)/P['upper_ns']-2)))


def count_apps(cfg):
    a=cfg['application'];H=cfg['mission_s']*NS
    return dict(read=F(periodic_starts(a['first_ns']+a['read_offset_ns'],a['epoch_ns'],H)),
                write=F(periodic_starts(a['first_ns']+a['write_offset_ns'],a['epoch_ns'],H)))


def timing(cfg,n,k):
    s=service(cfg,n);cal=cfg['calendar'];a=cfg['application']
    xp,xm,J=s['xplus'],s['xminus'],s['J']
    E=s['upper']['E'];aw=s['upper']['app_write'];frame=cal['frame_ticks']
    aperture=(frame-cal['application_grant_phase_ticks'])*xm-J
    control_gap=cal['c_ticks']*xm-J
    response=F(a['inbound_ns']+a['ready_ns']+a['outbound_ns']+a['backpressure_ns'])+frame*xp+J+aw
    L=cfg['constraints']['peak_window_ns']
    # Every interval intersecting [a,a+L] started in [a-E,a+L]. Count all
    # intersecting frames, all 8 starts in each. No stationary-average shortcut.
    frames=2+ceil((F(L)+max(E,aw)+J)/(frame*xm))
    controls=cal['batch_size']*frames
    # Each application stream: events in the deadline-left-expanded interval.
    app_each=1+ceil((F(L)+cfg['constraints']['application_deadline_ns'])/a['epoch_ns'])
    peak=(controls*E+app_each*(s['upper']['app_read']+aw))/L
    deadline=F(cfg['constraints']['application_deadline_ns'])
    peak_cap=F(cfg['constraints']['peak_bus_fraction'])
    delay_decode=min(control_gap-E,aperture-aw,deadline-response,
                     (peak_cap-peak)*L/(controls+2*app_each))
    # Decode delta is a nominal ns change, hence upper clock conversion.
    return dict(control_E_ns=E,app_write_ns=aw,mandatory_aperture_ns=control_gap,
                application_aperture_ns=aperture,app_response_upper_ns=response,
                app_deadline_slack_ns=deadline-response,
                app_target_slack_ns=F(cfg['constraints']['map_targets']['response_ns'])-response,
                peak_bus_core_upper=peak,peak_bus_remaining_for_other_work=peak_cap-peak,
                peak_target_slack=F(cfg['constraints']['map_targets']['peak_bus_fraction'])-peak,
                control_slack_ns=control_gap-E,application_aperture_slack_ns=aperture-aw,
                counted_control_operations=controls,counted_apps_each=app_each,
                extra_decode_nominal_ns_limit=max(F(0),delay_decode/xp),
                lower_clock=xm,upper_clock=xp,endpoint_span_ns=J,
                status='conditional service-area check; unmeasured extra bus work must fit reported residual',
                physical_WCET_confirmed=False)


def timers(cfg,k):
    s=service(cfg,39);xp,xm,J=s['xplus'],s['xminus'],s['J']
    q=cfg['adaptive']['timer_quantum_ticks'];fresh=cfg['adaptive']['source_to_fresh_rule_upper_ns']
    P=period(cfg,k)['upper_ns'];tau=(P+s['upper']['E']+fresh)/NS
    def timer(seconds):
        count=ceil(F(seconds)*NS/(q*xm))+1
        return dict(count=count,lower_s=(count-1)*q*xm/NS,
                    upper_s=(count*q*xp+J)/NS)
    short=timer(F(cfg['adaptive']['short_hold_s']))
    long=timer(F(cfg['adaptive']['long_hold_s']))
    recovery=timer(long['upper_s']+tau)
    return dict(short=short,long=long,recovery=recovery,tau_birth_to_fresh_s=tau,
                guard_holds_cover_tau=short['lower_s']>tau,
                NR_covers_h_plus_tau=recovery['lower_s']>=long['upper_s']+tau,
                counts_fit_34_bits=max(short['count'],long['count'],recovery['count'])<2**34,
                informational_q_majorant=None)


def adaptive_reads(cfg,k,U,Fparents,information_calendar=None):
    """Conservative price without informational T119 improvement.

    On good histories each parent causes <=2 logical ERR publications:
    a weak-E aperture observation and the following correcting E. All
    ordinary hold windows are covered by charging each publication a full
    long hold. Bad histories pay all potential starts. Union bounds only.
    Extra source veto is kept as a separate rate parameter v.
    """
    T=F(cfg['mission_s']);s=service(cfg,39);tm=timers(cfg,k)
    if information_calendar is not None:
        c=information_calendar
        convert=lambda t:dict(count=t['count'],lower_s=t['lower'],upper_s=t['upper'])
        tm=dict(short=convert(c['short_timer']),long=convert(c['long_timer']),recovery=convert(c['recovery']),
                tau_birth_to_fresh_s=c['tau'],guard_holds_cover_tau=c['w']>c['tau'],
                NR_covers_h_plus_tau=c['recovery']['lower']>=c['long_timer']['upper']+c['tau'],
                counts_fit_34_bits=max(c[x]['count'] for x in ('short_timer','long_timer','recovery'))<2**34)
    a=cfg['adaptive'];ob=cfg['observation'];cal=cfg['calendar']
    revisit=F(cfg['words']*cfg['application']['epoch_ns'],NS)
    age=(period(cfg,k)['upper_ns']+s['upper']['E'])/NS
    if cfg['application'].get('ordinary_read_publishes_ERR_G',True):
        raise ValueError('current informational price requires no app-read ERR publication')
    # Covers endpoint jitter of start timestamps as well as timer execution.
    min_gap=cal['c_ticks']*s['xminus'];J=s['J']
    def slots(seconds):return F(2+ceil((F(seconds)*NS+J)/min_gap))
    fresh=F(a['source_to_fresh_rule_upper_ns'],NS)
    hold_length=tm['long']['upper_s']+tm['tau_birth_to_fresh_s']+fresh
    ordinary_flags=2*Fparents+F(a['ordinary_false_expected_per_s'])*T
    recoveries=F(a['recoveries_upper']+1) # +startup, charged even with clean state
    loss_intervals=F(a['ordinary_loss_episodes_upper'])
    outage_time=F(a['ordinary_outage_fraction'])*T
    support=read_bounds(cfg,k);hard=read_bounds(cfg,1)
    extra_ordinary=(ordinary_flags*slots(hold_length)
        +recoveries*slots(tm['recovery']['upper_s']+fresh)
        +outage_time*NS/min_gap+2*loss_intervals)
    ordinary_upper=min(hard['upper'],support['upper']+extra_ordinary+U*hard['upper'])
    veto_slots=slots(fresh)
    source_edge_rate=F(NS)/(4*s['xminus'])+2/T
    # Quota bad histories may emit on every source edge. Extra G confirmations
    # are outside episode quotas and remain an independent addend v.
    ordinary_record_rate=min(source_edge_rate,ordinary_flags/T+2*loss_intervals/T+U*source_edge_rate)
    return dict(reads_zero_extra_veto_upper=ordinary_upper,
                reads_lower=support['lower'],reads_hard_upper=hard['upper'],
                reads_extra_per_veto=veto_slots,
                ordinary_added_reads_upper=extra_ordinary,bad_history_reads_upper=U*hard['upper'],
                source_records_zero_extra_veto_per_s_upper=ordinary_record_rate,
                source_edge_rate_upper=source_edge_rate,
                v_domain='0<=v<=source_edge_rate; raw notifications, not loss episode count',
                source_rate_formula='min(source_edge_rate,ordinary_record_rate+v)',
                read_rate_formula='min(hard,zero_v_upper+reads_extra_per_veto*v)',
                hold_length_s=hold_length,ordinary_publications_upper=ordinary_flags,
                publication_bound_basis='weak-E aperture repeat then next correcting E; no app-read ERR',
                app_same_word_revisit_s=revisit,mandatory_age_s=age,timers=tm)


def cost_result(cfg,n,t,k,U,adaptive=False,information_calendar=None):
    W=cfg['words'];T=F(cfg['mission_s']);H=T*NS;s=service(cfg,n)
    groups=projected_groups(n,{1:F(1)})
    Fparents=W*sum(groups[1:])*per_bit_moment_caps(cfg)['M1']
    apps=count_apps(cfg);Nar,Naw=apps['read'],apps['write'];support=read_bounds(cfg,k)
    ad=adaptive_reads(cfg,k,U,Fparents,information_calendar) if adaptive else None
    N=ad['reads_zero_extra_veto_upper'] if adaptive else support['upper']
    Hard=ad['reads_hard_upper'] if adaptive else support['upper']
    # A birth observed inside weak E may survive that release and require
    # a second repair at the next E. At most two repairs per parent before
    # the global bad event; after it, all mandatory/potential reads can write.
    repairs=min(N,2*Fparents+U*Hard)
    R,E,ar,aw,ini=(s['upper'][x] for x in ('R','E','app_read','app_write','initial'))
    common=ar*Nar+aw*Naw+ini*W
    core=(R*N+(E-R)*repairs+common)/H
    hard=(E*Hard+common)/H
    # Omit a terminal offer in each stream from the LOWER: its service may
    # finish after T. The upper charges all offered work, including the tail.
    lower=(s['lower']['R']*support['lower']+s['lower']['app_read']*max(F(0),Nar-1)
           +s['lower']['app_write']*max(F(0),Naw-1)+s['lower']['initial']*W)/H
    cut_rate=F(NS)/(cfg['observation']['cut_ns']*s['xminus'])+2/T if adaptive else F(0)
    capture_rate=ad['source_records_zero_extra_veto_per_s_upper'] if adaptive else F(0)
    decision_rate=read_bounds(cfg,1)['upper']/T if adaptive else N/T
    timer_rate=2*capture_rate+F(2*(cfg['adaptive']['recoveries_upper']+1),T) if adaptive else N/T
    rates=dict(scrub_reads=N/T,scrub_corrections=repairs/T,
               application_reads=Nar/T,application_writes=Naw/T,
               decodes=(N+Nar+Naw)/T,encodes=(Naw+W)/T,
               read_beats=3*(N+Nar+Naw)/T,write_beats=3*(repairs+Naw+W)/T,
               turnarounds=(repairs+Naw+W)/T,
               app_dispatch=(Nar+Naw)/T,initialization=F(W)/T,
               cuts=cut_rate,captures=capture_rate,records=capture_rate,
               decisions=decision_rate,timer_events=timer_rate)
    # All coefficients have rates in operations/s. CPU_ns coefficients divide
    # by 1e9; energy_J coefficients multiply by mission seconds.
    cpu={name+'_ns':rate/NS for name,rate in rates.items()
         if name in ('app_dispatch','initialization','cuts','captures','records','decisions','timer_events')}
    ctrl_memory=131136 if adaptive else 0
    boundary_v=None
    if adaptive:
        slope=E*ad['reads_extra_per_veto']/NS
        boundary_v=(hard-core)/slope
    energy_rates={**rates,'transport_requests':(Nar+Naw)/T,'transport_replies':(Nar+Naw)/T,
                  'transport_records':capture_rate,'transport_cuts':cut_rate}
    extra_veto_rates=({
        'scrub_reads':ad['reads_extra_per_veto'],'scrub_corrections':ad['reads_extra_per_veto'],
        'decodes':ad['reads_extra_per_veto'],'read_beats':3*ad['reads_extra_per_veto'],
        'write_beats':3*ad['reads_extra_per_veto'],'turnarounds':ad['reads_extra_per_veto'],
        'captures':F(1),'records':F(1),'timer_events':F(2),'extra_veto':F(1),
        'transport_records':F(1)} if adaptive else {})
    return dict(core_SRAM_fraction_upper=core,core_SRAM_fraction_lower=lower,
                full_SRAM_formula='core_upper + B_controller_average; extra bus work is not assumed free',
                all_history_SRAM_core_upper=hard,
                zero_extra_veto_slice=adaptive,
                adaptive=ad,expected_parent_count_upper=Fparents,
                read_count_upper=N,repair_count_upper=repairs,full_cost_rates=rates,
                CPU_fraction_coefficients=cpu,
                CPU_extra_veto_formula='v*(capture_ns+record_ns+2*timer_event_ns+extra_veto_ns)/1e9; capped source rate, unchanged decision/cut schedule' if adaptive else None,
                codec_busy_fraction=(F(s['decode'])*rates['decodes']+F(s['encode'])*rates['encodes'])/NS,
                energy_coefficients_per_second=energy_rates,
                energy_formula='T*sum(rate_a*incremental_nonoverlapping_energy_J_per_action_a)+T*idle_W; transport and controller included',
                extra_veto_action_rates_per_unit_v=extra_veto_rates,
                payload_data_bytes=4*(Nar+Naw),payload_rate_Bps=4*(Nar+Naw)/T,
                traffic_formula='payload + requests*request_header + replies*reply_header +32*source_records + cuts*cut_header',
                source_record_rate_Bps=32*capture_rate,
                transport_plus_loss_state_bytes=ctrl_memory,
                unknown_memory_addends=['policy_state_bytes','payload_buffer_bytes','codec_register_bytes'],
                initialization=dict(encodes=W,write_beats=3*W,turnarounds=W,
                                    full_prefix_bus_ns=ini*W,amortized_fraction=ini*W/H,
                                    outside_mission_risk=True),
                veto_core_fraction_slope_per_notification_per_s=(E*ad['reads_extra_per_veto']/NS if adaptive else F(0)),
                veto_hard_cap_reached_per_s=boundary_v,
                lower_scope='chosen candidate only, not lower for every admissible fixed policy',
                bad_history_paid=True,pending_paid=True,after_A_paid=True,
                scientific_status='conditional affine resource account; hardware coefficients remain parameters')


def calculate(cfg,information=None):
    from informational import candidates as information_candidates
    if information is None:
        information=information_candidates(cfg)
    if information['selected'] is None:
        raise ValueError('no informational adaptive point at the target; mandatory diagnostic cannot replace it')
    chosen=[('t1_constant',39,1,select_fixed(cfg,39,1),False)]
    candidates=[k for k in cfg['adaptive']['candidate_ka'] if
        risk(cfg,39,1,period(cfg,k)['upper_ns'],service(cfg,39)['upper']['E'])['upper']<=F(cfg['epsilon'])/2]
    if not candidates:raise ValueError('no adaptive mandatory candidate')
    chosen.append(('t1_adaptive',39,1,information['selected']['k'],True))
    chosen.append(('t2_constant',44,2,select_fixed(cfg,44,2),False))
    rows={}
    for name,n,t,k,ad in chosen:
        P=period(cfg,k);mandatory=risk(cfg,n,t,P['upper_ns'],service(cfg,n)['upper']['E'])
        r=information['selected']['risk'] if ad else mandatory
        tm=timing(cfg,n,k)
        rows[name]=dict(n=n,k_data=32,t=t,k_passes=k,period=P,risk=r,timing=tm,
                       mandatory_risk_diagnostic=mandatory if ad else None,
                       cost=cost_result(cfg,n,t,k,r['upper'],ad,information['selected']['calendar'] if ad else None),
                       class_optimum_lower=None,informational_adaptive_bound=bool(ad),
                       physical_acceptance=False)
    sensitivity=[]
    for p2s in cfg['environment']['conditional_sensitivity']['p2']:
        for p3s in cfg['environment']['conditional_sensitivity']['p3']:
            p2,p3=F(p2s),F(p3s);p={1:1-p2-p3,2:p2,3:p3}
            point={'p_s':p,'risk':{}}
            for name,row in rows.items():
                point['risk'][name]=risk(cfg,row['n'],row['t'],row['period']['upper_ns'],
                    service(cfg,row['n'])['upper']['E'],p)
            point['scope']='same periods, no refitting; adaptive mixture uses mandatory-only upper, not singleton informational certificate; physical p_s unknown; upper>epsilon is not exclusion'
            sensitivity.append(point)
    a=rows['t1_adaptive']['cost'];b=rows['t2_constant']['cost']
    # Compare a sufficient upper for t2 with a lower for this chosen adaptive
    # support. This is stronger than ranking two upper bounds, but remains
    # candidate-specific and requires the extra service cost to fit the grid.
    q2=b['full_cost_rates']['decodes']
    threshold=(a['core_SRAM_fraction_lower']-b['core_SRAM_fraction_upper'])*NS/q2
    perturbed=deepcopy(cfg)
    extra=rows['t2_constant']['timing']['extra_decode_nominal_ns_limit']
    perturbed['service']['decode44_ns']+=extra
    perturbed_risk=risk(perturbed,44,2,rows['t2_constant']['period']['upper_ns'],service(perturbed,44)['upper']['E'])
    perturbed_cost=cost_result(perturbed,44,2,rows['t2_constant']['k_passes'],perturbed_risk['upper'])
    return dict(rows=rows,sensitivity=sensitivity,informational_certificate=information,
        diagnostic_mandatory_only=dict(k=max(candidates),status='diagnostic support slice, not main information row'),
        conditional_bus_comparison=dict(t2_upper_below_selected_adaptive_lower=b['core_SRAM_fraction_upper']<a['core_SRAM_fraction_lower'],
            t1_fixed_upper_below_selected_adaptive_lower=rows['t1_constant']['cost']['core_SRAM_fraction_upper']<a['core_SRAM_fraction_lower'],
            adaptive_upper_below_selected_t1_fixed_lower=a['core_SRAM_fraction_upper']<rows['t1_constant']['cost']['core_SRAM_fraction_lower'],
            extra_veto_rate_before_losing_selected_fixed_lower_comparison=(rows['t1_constant']['cost']['core_SRAM_fraction_lower']-a['core_SRAM_fraction_upper'])/a['veto_core_fraction_slope_per_notification_per_s'],
            allowance_for_t2_extra_bus_fraction=a['core_SRAM_fraction_lower']-b['core_SRAM_fraction_upper'],
            extra_t2_decode_bus_ns_cost_threshold=threshold,
            algebraic_threshold_scope='fixed action-count coefficients only; service/risk must be rechecked when latency changes',
            service_limit_extra_t2_decode_ns=rows['t2_constant']['timing']['extra_decode_nominal_ns_limit'],
            t2_at_service_decode_limit=dict(extra_nominal_decode_ns=extra,Q_upper=perturbed_risk['upper'],
               SRAM_core_upper=perturbed_cost['core_SRAM_fraction_upper'],
               below_selected_adaptive_lower=perturbed_cost['core_SRAM_fraction_upper']<a['core_SRAM_fraction_lower']),
            scope='selected candidates and declared serial bus model; other controller costs may reverse order, no class-optimum/global-price claim'),
        total_scalar_price=None,physical_winner=None)
