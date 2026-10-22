"""Directed checks of changed timing/count/price claims, not an old-Q replay."""
from copy import deepcopy
from fractions import Fraction as F
from service import NS, ac_limits, count_before, evaluate, peak_bound, span, transaction, workload


def run(p, common):
    names=[]
    def check(name, condition):
        if not condition:raise AssertionError(name)
        names.append(name)
    r=evaluate(p,common);tr=r['transactions'];s=r['service']
    check('selected_point_has_all_conditional_margins',all(r['conditional_checks'].values()))
    # Independent explicit serialized stage list; no overlap discounts.
    stages={'read':[64,64,64,64,32,32],
            'write':[64,64,64,64,32,32,32,64,64,64,32],
            'initial':[64,32,64,64,64,32]}
    check('full_stage_sums_320_576_320',all(F(sum(stages[k]))==tr['core_nominal_ns'][k]+64 for k in stages))
    check('end_to_end_no_frame_wait',s['max_response_upper_ns']==F(139650576,100000))
    check('release_before_reply_deadline',s['arrival_to_release_upper_ns']<3000)
    check('selected_service_is_not_periodically_padded',not tr['padding_reserved'])
    # Clock/J are one interval envelope for transaction and individual AC guards.
    check('single_span_not_J_per_stage',tr['full_upper_ns']['write']==F(576)*F(100001,100000)+F(1,2))
    check('pulse_40ns_provides_4p4996ns_skew',ac_limits(p)['maximum_admissible_ns']['WE_pulse_shrink_ns']==F(11249,2500))
    check('read_56ns_has_10p49944ns_board_capture',ac_limits(p)['maximum_admissible_ns']['read_address_CE_BE_board_capture_ns']==F(131243,12500))
    # Positive/nonpositive interval cases at actual AC boundaries.
    bad=deepcopy(p);bad.update(write_pulse_ns=35,write_hold_ns=21)
    check('nominal_35ns_pulse_rejected_with_clock_J',not ac_limits(bad)['positive_margins'])
    bad=deepcopy(p);bad['read_capture_ns']=45
    check('nominal_45ns_capture_rejected_with_clock_J',not ac_limits(bad)['positive_margins'])
    bad=deepcopy(p);bad['read_release_ns']=18
    check('nominal_18ns_release_rejected_with_clock_J',not ac_limits(bad)['positive_margins'])
    bad=deepcopy(p);bad['post_supply_stable_wait_ns']=200000
    check('nominal_200us_wait_insufficient_under_clock_J',not ac_limits(bad)['positive_margins'])
    # Independent output-edge witnesses at extremes of a common clock and
    # endpoint errors +/-0.25 ns. Slower assertion can shorten the WE pulse;
    # the interval allowance is a joint path bound, not per-edge credit.
    edge_cases=0
    for scale in (F(99999,100000),F(1),F(100001,100000)):
        for left in (-F(1,4),F(1,4)):
            for right in (-F(1,4),F(1,4)):
                pulse=(48*scale+right)-(8*scale+left+F(11249,2500))
                capture=56*scale+right-(left+45+F(131243,12500))
                if pulse<35 or capture<0:raise AssertionError('edge oracle')
                edge_cases+=1
    check('clock_and_board_edge_oracle',edge_cases==12)
    check('excess_WE_board_skew_breaks_35ns',48*F(99999,100000)-F(1,4)-(8*F(99999,100000)+F(1,4)+F(11249,2500)+F(1,1000))<35)
    lim=tr['total_controller_limit_at_fixed_codec_ns']
    q=deepcopy(p);q['controller_budget_ns']=lim
    check('joint_controller_target_boundary_attained',transaction(q)['local_target_slack_ns']==0)
    q['controller_budget_ns']+=F(1,1000)
    check('controller_above_boundary_fails',not transaction(q)['fits_local_target'])
    q=deepcopy(p);q['decode_ns']+=20;q['encode_ns']+=20
    check('codec_must_share_controller_margin',not transaction(q)['fits_local_target'])
    q=deepcopy(p);q['transaction_aperture_ns']=512
    check('512_window_cannot_hold_selected_service',not transaction(q)['fits_aperture'])
    q=deepcopy(common);q['application']['epoch_ns']=1000;q['application']['write_offset_ns']=500
    check('closely_spaced_offers_do_not_get_no_queue_claim',not evaluate(p,q)['service']['no_queue_induction'])
    q=deepcopy(common);q['application']['inbound_ns']+=1100
    check('added_transport_delay_consumes_response_target',not evaluate(p,q)['conditional_checks']['response_target'])
    # A small, directly generated physical-time calendar, including exact T hits.
    small_cases=0
    for H in (0,1,100,101,600,601,1000,1100,1101,1600,1601,5101):
        for first in (100,600):
            actual=[a for a in range(first,H,1000)]
            checkname=count_before(H,first,1000)==len(actual)
            if not checkname:raise AssertionError((H,first))
            small_cases+=1
    check('small_calendar_including_exact_T',small_cases==24)
    w=r['workload'];counts=w['counts']
    check('frozen_offer_counts',counts=={'read':315569688607,'write':315569688606})
    check('frozen_period_and_D',w['period_per_word_ns']==131074621440 and w['deadline_ns']==3000)
    check('fixed_v4_tail_does_not_need_after_T_help',not any(s['terminal_response_crossings'].values()))
    toy=deepcopy(common);toy['mission_s']=F(600001,NS)
    t=evaluate(p,toy)
    check('pending_final_write_charged_in_full',t['service']['terminal_response_crossings']['write'] and t['price']['counts']['write']==1)
    # Exact busy-interval intersection oracle on a toy merged workload. Include
    # all breakpoints at which a sliding-window busy integral can change slope.
    pw={'deadline_ns':7,'step_ns':20,'spacing_ns':9}
    durations={'read':F(3),'write':F(5)};oracle_cases=0
    for delay_r in (0,1,2):
        for delay_w in (0,1,2):
            intervals=[]
            for qn in range(12):
                intervals.extend([(20*qn+delay_r,20*qn+delay_r+3),
                                  (20*qn+9+delay_w,20*qn+9+delay_w+5)])
            for L in (1,7,20,21,40):
                bound=peak_bound(pw,durations,L)['occupied_ns_upper']
                starts={x for pair in intervals for e in pair for x in (e,e-L)}
                for u in starts:
                    actual=sum(max(0,min(v,u+L)-max(a,u)) for a,v in intervals)
                    if actual>bound:raise AssertionError(('peak oracle',u,L,actual,bound))
                    oracle_cases+=1
    check('sliding_window_oracle_all_breakpoints',oracle_cases>1000)
    check('merged_peak_count_is_three_not_four',r['peak']['merged_count_upper']==3)
    check('maximum_relaxed_peak_two_write_one_read',r['peak']['maximizing_relaxed_counts']=={'read':1,'write':2})
    # Two writes separated by >1 ms still both intersect a 1-ms window.
    near_edges=[(-300,F(-300)+tr['full_upper_ns']['write']),
                (499720,F(499720)+tr['full_upper_ns']['read']),
                (999720,F(999720)+tr['full_upper_ns']['write'])]
    busy=sum(max(0,min(v,1000000)-max(a,0)) for a,v in near_edges)
    check('two_edge_writes_and_middle_read_paid',all(v>0 and a<1000000 for a,v in near_edges) and busy<=r['peak']['occupied_ns_upper'])
    # Cost is independent of radiation path, error state and success stopping.
    q=deepcopy(common);q['environment']={'unavailable':True};q['lifetime_other_budget']='9/10'
    check('no_old_per_bit_or_quota_used',evaluate(p,q)==r)
    check('no_physical_Q_or_MC_claim',r['physical_Q_upper'] is None and not r['probability_computation_performed'])
    check('full_price_charges_control_and_initialization',r['price']['mean_bus_fraction_upper_at_controller_budget']>r['price']['core_mean_bus_fraction_upper'] and r['initialization']['bus_fraction_amortized']>0)
    check('initialization_all_words_and_beats',r['initialization']['write_x16']==3*common['words'] and r['initialization']['encodes']==common['words'])
    check('unknown_supply_clean_E_energy_preserved',r['initialization']['elapsed_from_power_on_upper_ns'] is None and r['initialization']['clean_start_escape_probability'] is None and not s['physical_E_certified'] and r['price']['energy_J'] is None)
    check('post_A_and_pending_not_cut_off',r['price']['all_history_and_full_pending_work_paid'])
    check('allocated_capacity_and_payload',r['capacity']['allocated_bytes']==786432 and r['capacity']['useful_bytes']==524288)
    return dict(passed=len(names),checks=names,toy_count_cases=small_cases,
                sliding_window_oracle_cases=oracle_cases,
                scope='directed author checks; no independent review or physical validation')
