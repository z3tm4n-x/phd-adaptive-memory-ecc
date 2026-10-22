"""One app-only t2 candidate; accepted inputs/calculation stay read-only."""
from fractions import Fraction as F
from math import gcd
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ACCEPTED = HERE.parent/'code-strength'
sys.path.insert(0, str(ACCEPTED))
from comparison import NS, count_apps, risk, service


def calendar_audit(cfg):
    a=cfg['application'];W=cfg['words'];H=int(F(cfg['mission_s'])*NS)
    assert H==F(cfg['mission_s'])*NS
    epoch=a['epoch_ns'];first=a['first_ns']+a['write_offset_ns'];D=cfg['constraints']['application_deadline_ns']
    multiplier=a['address_multiplier'];P=W*epoch
    if gcd(multiplier,W)!=1 or not 0<=first<epoch or D>=epoch:
        raise ValueError('application permutation/aperture premise fails')
    inv=pow(multiplier,-1,W)
    counts=[];first_cells=[];tail_cells=[];partial=0;seen=set()
    for word in range(W):
        q=word*inv % W;seen.add(q);start=first+q*epoch
        count=max(0,(H-1-start)//P+1)
        last=start+(count-1)*P if count else None
        counts.append(count);first_cells.append(min(H,start))
        tail_cells.append(H-last if count else H)
        if count and last+D>H:partial+=1
    if len(seen)!=W or max(first_cells+tail_cells)>P:
        raise ValueError('initial/terminal deterministic cell exceeds the proposed period')
    expected=int(count_apps(cfg)['write'])
    if sum(counts)!=expected:raise ValueError('per-word counts differ from global offered writes')
    return dict(words_checked=W,period_ns=P,aperture_ns=D,
        first_write_arrival_ns=first,last_first_write_arrival_ns=first+(W-1)*epoch,
        max_initial_cell_ns=max(first_cells),max_terminal_cell_ns=max(tail_cells),
        writes_before_T=expected,min_writes_per_word=min(counts),max_writes_per_word=max(counts),
        terminal_apertures_clipped=partial,first_and_last_cells_bounded=True,
        arrivals_are_deterministic_model_ns=True,realized_starts_used_as_fixed=False,
        synthetic_E_at_T=False,clean_initial_required=True)


def service_audit(cfg):
    a=cfg['application'];cal=cfg['calendar'];s=service(cfg,44)
    D=cfg['constraints']['application_deadline_ns'];L=cfg['constraints']['peak_window_ns']
    offset=a['write_offset_ns']-a['read_offset_ns']
    spacing=min(offset,a['epoch_ns']-offset)
    response=F(a['inbound_ns']+a['ready_ns']+a['outbound_ns']+a['backpressure_ns'])+cal['frame_ticks']*s['xplus']+s['J']+s['upper']['app_write']
    aperture=(cal['frame_ticks']-cal['application_grant_phase_ticks'])*s['xminus']-s['J']
    # An operation intersecting any [t,t+L] was offered in [t-D,t+L].
    # Inclusive endpoints: at most floor((L+D)/epoch)+1 offers per stream.
    each=(L+D)//a['epoch_ns']+1
    peak=each*(s['upper']['app_read']+s['upper']['app_write'])/L
    extra=min(aperture-s['upper']['app_write'],D-response,
              (F(cfg['constraints']['peak_bus_fraction'])-peak)*L/(2*each))/s['xplus']
    return dict(application_response_upper_ns=response,deadline_slack_ns=D-response,
        application_grant_aperture_ns=aperture,full_write_upper_ns=s['upper']['app_write'],
        read_upper_ns=s['upper']['app_read'],minimum_offer_spacing_ns=spacing,
        application_slots_preserved=True,control_starts=0,startup_scrub_starts=0,
        peak_window_ns=L,offers_each_in_expanded_peak_window=each,
        all_history_peak_core_upper=peak,
        peak_remaining_for_controller=F(cfg['constraints']['peak_bus_fraction'])-peak,
        map_response_target_slack_ns=F(cfg['constraints']['map_targets']['response_ns'])-response,
        map_peak_target_slack=F(cfg['constraints']['map_targets']['peak_bus_fraction'])-peak,
        extra_decode44_ns_service_limit=max(F(0),extra),
        hard_service_conditions_hold=spacing>D and response<=D and s['upper']['app_write']<=aperture and peak<=F(cfg['constraints']['peak_bus_fraction']),
        scope='conditional all-history service, not hardware measurement; additional controller work must fit the same windows')


def full_cost(cfg,accepted):
    s=service(cfg,44);T=F(cfg['mission_s']);W=cfg['words'];apps=count_apps(cfg)
    nr,nw=apps['read'],apps['write']
    upper=(nr*s['upper']['app_read']+nw*s['upper']['app_write']+W*s['upper']['initial'])/(T*NS)
    lower=(max(F(0),nr-1)*s['lower']['app_read']+max(F(0),nw-1)*s['lower']['app_write']+W*s['lower']['initial'])/(T*NS)
    rates=dict(application_reads=nr/T,application_writes=nw/T,
        decodes=(nr+nw)/T,encodes=(nw+W)/T,read_beats=3*(nr+nw)/T,
        write_beats=3*(nw+W)/T,turnarounds=(nw+W)/T,
        app_dispatch=(nr+nw)/T,application_grants=(nr+nw)/T,initialization=F(W)/T,
        scrub_reads=F(0),scrub_repairs=F(0),scrub_decisions=F(0),scrub_timer_events=F(0),
        cuts=F(0),captures=F(0),records=F(0))
    energy={**rates,'transport_requests':(nr+nw)/T,'transport_replies':(nr+nw)/T}
    return dict(offered_reads=nr,offered_writes=nw,all_history_core_SRAM_upper=upper,
        core_SRAM_lower=lower,expected_core_SRAM_upper=upper,
        full_SRAM_formula='core + B_controller; mean and peak constraints separately',
        full_cost_rates=rates,CPU_fraction_coefficients={k+'_ns':rates[k]/NS for k in ('app_dispatch','application_grants','initialization')},
        CPU_formula='sum(rate*disjoint_action_ns)/1e9 + CPU_background_fraction',
        energy_coefficients_per_second=energy,
        energy_formula='T*sum(rate*incremental_nonoverlapping_J_per_action)+T*idle_W; controller/transport remain parameters',
        payload_bytes=4*(nr+nw),payload_rate_Bps=4*(nr+nw)/T,
        traffic_formula='payload + (reads+writes)*(request_header_bytes+reply_header_bytes)',
        codec_resources=accepted['resources']['2'],additional_adaptive_transport_state_bytes=0,
        unknown_memory_addends=['application_scheduler_state_bytes','payload_buffer_bytes','codec_register_bytes'],
        unknown_hardware_caps=cfg['constraints']['capacity_caps'],
        initialization=dict(encodes=W,write_beats=3*W,turnarounds=W,
            prefix_bus_upper_ns=W*s['upper']['initial'],amortized_fraction=W*s['upper']['initial']/(T*NS)),
        full_started_work_and_pending_paid=True,post_A_and_bad_history_work_paid=True,
        application_write_has_one_final_write=True,scalar_price=None,hardware_winner=None)


def evaluate(cfg,basis,accepted):
    cal=calendar_audit(cfg);svc=service_audit(cfg)
    result=dict(calendar=cal,service=svc,input_changed=False,accepted_table_changed=False,
                candidate='t2, empty dedicated scrub schedule',Q_upper=None,full_price=None,
                specific_theory_basis=basis)
    if basis['status']!='applicable':
        result['status']='PREPARED_PENDING_SPECIFIC_THEORY_BASIS'
        return result
    if not basis.get('theorist_commit') or not basis.get('theorist_reply_url'):
        raise ValueError('specific theorist evidence missing')
    if basis['application_arrival_period_ns']!=cal['period_ns'] or basis['arrival_to_deadline_aperture_ns']!=cal['aperture_ns']:
        raise ValueError('theorist period/aperture binding mismatch')
    if not svc['hard_service_conditions_hold']:
        raise ValueError('declared arrival-to-deadline service is not established at this point')
    r=risk(cfg,44,2,cal['period_ns'],cal['aperture_ns'])
    r['basis']='T196 deterministic application-arrival apertures; specific basis in basis.json'
    result.update(status='CONDITIONAL_APP_ONLY_T2_READY_FOR_REVIEW',Q_upper=r['upper'],risk=r,
                  full_price=full_cost(cfg,accepted),meets_epsilon=r['upper']<=F(cfg['epsilon']),
                  meets_half_epsilon_target=r['upper']<=F(cfg['epsilon'])/2)
    return result
