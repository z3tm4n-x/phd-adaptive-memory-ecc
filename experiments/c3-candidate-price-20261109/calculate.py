"""Lifetime risk, primary memory service and the residual control budget for one registered rule."""
import argparse
from fractions import Fraction as F
from math import ceil,exp
from basis import HERE,basis,write_json

REGISTRATION='8472a0a2f3fc0c5521f49c62fd40dd4e736e8bf9'
HANDOFF='https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/186#issuecomment-6748106575'
PROOF='0071e3bb85878e406b4d8928ecff1e9f551d7220'
NS=10**9
FAST=1
SLOW=32
HISTORY=730
VISIBLE_FAST=F('0.000222332599')
VISIBLE_EDGE=F('0.000439149335')
VISIBLE_SLOW=F('0.000092519858')


def rounded_up(value,digits):
    return F(ceil(value*10**digits),10**digits)


def visibility_terms(W,T,D,L,P,B,S1,S2,U,xm,xp,j,aperture):
    """Numerical reconstruction of the three C2 terms (5)–(6)."""
    c=F(39,D);scale=W*c**2/2
    fast_width=xp*L+aperture;rare_width=xp*P+aperture
    history=xm*(HISTORY*P-L)-2*j
    age=xp*((HISTORY+1)*P+L)+aperture+2*j
    ends=[ceil((T+2*j+aperture)/(xm*duration))+3 for duration in (L,P)]
    overlap=age+(ceil((age+2*aperture+2*j)/(xm*P))+3)*aperture
    fast=scale*fast_width*(S2+B**2*ends[0]*aperture)
    variation=scale*rare_width*B*U*overlap
    visible=scale*rare_width*(S1+B*ends[1]*aperture)/(F('2.71828')*c*(W-1)*history)
    assert tuple(rounded_up(x,12) for x in (fast,variation,visible))==(VISIBLE_FAST,VISIBLE_EDGE,VISIBLE_SLOW)
    return {'source_head':PROOF,'fast_exact':fast,'variation_exact':variation,'visibility_coefficient_exact':visible,
            'unweighted_slow_pairs':scale*rare_width*(S2+B**2*ends[1]*aperture),
            'history_lower_s':history,'overlap_upper_s':overlap}


def fixed_point():
    base=basis()
    W=base['W'];T=base['T_s'];D=base['D'];eps=base['epsilon']
    xm=F(99999,100000);xp=F(100001,100000);j=F(1,2*NS)
    L=F(196*W,NS);P=SLOW*L;H=HISTORY*P
    assert ceil(F(300)/P)==HISTORY
    pminus=P*xm-2*j;pplus=P*xp+2*j
    # Count N+1 cells to cover a partial reset/end cell (the C2 price handoff).
    history_plus=(HISTORY+1)*pplus;scan_plus=L*xp+j
    b=base['b'];B=base['B'];Fsun=base['F'];S1=F(187464)
    S2=b*b*T+(B+b)*Fsun
    c=F(39,D); delta=F(3,500000)
    aperture=124*xp/NS+3*j
    # Ignore all extra fast E for the deterministic-core certificate; on each
    # execution completing the core the word phases are identical at every anchor.
    k=F(39*38*W,2*D**2)
    accumulation=k*(pplus+aperture)*S2;edge=k*2*B*aperture*S1
    anchor_q=min(F(1),delta+accumulation+edge)
    def history_q(gamma,d=F(0),other=F(0)):
        return min(1,delta+d+other+VISIBLE_FAST+VISIBLE_EDGE+VISIBLE_SLOW/gamma)
    terms=visibility_terms(W,T,D,L,P,B,S1,S2,base['J_cap'],xm,xp,j,aperture)
    gamma=F(1,2)
    q=rounded_up(history_q(gamma),9)  # match the issued C2 price passport
    assert q<eps and history_q(gamma,F(1,10000))<eps<anchor_q
    # Dropping the empty-history weight in (3) also covers a hit on an already
    # occupied word at the same position. The physical upper from the core alone
    # uses a distinct-bit pair coefficient and need not bound all such stops.
    no_visibility_stop=min(F(1),delta+terms['fast_exact']+terms['unweighted_slow_pairs'])
    max_cells=ceil(T/pminus)+2
    visits_cap=base['maximum_word_visits']
    hits=2*W*c*S1
    read=48*xp/NS+j;write=56*xp/NS+j;serial_read=68*xp/NS+j
    late=base['late_ramp_300s']
    mean=W*c*(b*(H+L)+late['excess_exposure'])

    def upper(eta,stop=q):
        # eta is an expectation of bad cell closures before stopping, not the
        # number of deliveries or duplicates. Maintain the registered lattice through T.
        tf=T if eta is None else min(T,scan_plus+history_plus*(1+hits+eta)+stop*T)
        switches=max_cells if eta is None else min(max_cells,1+2*(hits+eta)+stop*max_cells)
        # One mandatory scan per cell, with 31 more for a fast cell. Two boundary
        # allowances on both counts pay incomplete intervals and a last started pass.
        pass_cap=ceil(T/(xm*L-2*j))+2
        passes=min(F(pass_cap),T/pminus+2+(SLOW-1)*(tf/pminus+2))
        visits=min(visits_cap,W*passes)
        repairs=min(visits,hits+stop*visits_cap)
        primary=read*visits;repair=write*repairs;total=primary+repair
        return {'eta':eta,'E_Tfast_upper_s':tf,'fast_fraction_upper':tf/T,
                'E_switch_upper':switches,'E_pass_reports_upper':passes,'E_cell_closures_upper':max_cells,
                'E_primary_word_reads_upper':visits,'E_repairs_upper':repairs,'physical_read_s':primary,
                'repair_bus_s':repair,'known_primary_bus_upper_s':total,'known_primary_bus_upper_percent':100*total/T,
                'serial_primary_upper_s':serial_read*visits+repair,
                'stop_probability_charge':stop,'post_stop_worst_extra_repairs':stop*visits_cap,
                'signed_sufficient_extra_bus_s':base['sufficient_half_s']-total,
                'signed_sufficient_extra_bus_percent':100*(base['sufficient_half_s']-total)/T}

    izero=upper(F(0)); worst=upper(None)
    # More general handoff: charge the good prefix and the whole hard word count
    # on stopped histories, even if the nominal visit geometry changes there.
    prehold=min(T,scan_plus+history_plus*(1+hits))
    hfast=xm*L-2*j;hslow=xm*P-2*j
    before_reads=W*(2+T/hslow+(1/hfast-1/hslow)*prehold)
    general_reads=before_reads+q*visits_cap
    general_repairs=hits+q*visits_cap
    general_total=general_reads*read+general_repairs*write
    price_per_invalid=W*(1/hfast-1/hslow)*history_plus*read
    c2_switch_cap=ceil((T+2*j)/(xm*P))+2
    general_slack=base['sufficient_half_s']-general_total
    # On the admitted ordinary permanent-invalid execution choose nominal clocks
    # and no execution exceptions. Every complete L-round is serviced, at least
    # 48 nominal ns per word even with no writes; continue the registered lattice.
    reads_all_fast=(T//L)*W
    fast_floor_bus_s=reads_all_fast*F(48,NS)
    quiet_passes_upper=min(F(ceil(T/L)+2),T/P+2+(SLOW-1)*((H+L)/P+2))
    empty_read_upper=quiet_passes_upper*W*F(48,NS)
    all_fast_rounds=T//L
    # An invalid at least every 730th closure forces FAST, regardless of real
    # corrections. Compare this with a declared cap on invalid cells, if any.
    sparse_resets=int((T//P)//HISTORY)
    management_frames=ceil((T+2*j)/(F(1568,NS)*xm))+2
    charged_management_limit=management_frames*(64*xp/NS+j)
    # Extra guard E may use a free core slot, including when the policy stays
    # fast. Cap the joint primary+guard count by the hardware slot envelope.
    slot_repairs=min(visits_cap,hits+q*visits_cap)
    slot_bus=visits_cap*read+slot_repairs*write
    slot_serial=visits_cap*serial_read+slot_repairs*write
    full_slots_upper=slot_bus+charged_management_limit
    full_fixed_upper=base['fixed_candidate_upper_s']+charged_management_limit
    broad_slot_repair=min(visits_cap,hits+no_visibility_stop*visits_cap)
    broad_slots_upper=visits_cap*read+broad_slot_repair*write+charged_management_limit
    # Relative endpoint uncertainty is covered at both boundaries. Use the whole
    # weak-E aperture, including its conservative edge allowance.
    last_release_slack_ns=420*xm-2*j*NS-aperture*NS
    pre_tf=min(T,scan_plus+history_plus*(1+hits))
    good_passes=min(F(ceil(T/(xm*L-2*j))+2),T/pminus+2+(SLOW-1)*(pre_tf/pminus+2))
    good_primary=read*min(visits_cap,W*good_passes)+write*hits
    post_limit=(base['sufficient_half_s']-good_primary)/q
    ncomplete=T//P
    def prefix_floor(n):
        fast_cells=min(ncomplete,(n+1)*HISTORY)
        return W*(ncomplete+(SLOW-1)*fast_cells)*F(48,NS)
    lo,hi=0,sparse_resets
    while hi-lo>1:
        mid=(lo+hi)//2
        if prefix_floor(mid)>base['exclusion_half_s']:hi=mid
        else:lo=mid
    assert prefix_floor(lo)<=base['exclusion_half_s']<prefix_floor(hi)
    r={'candidate_registration':REGISTRATION,'T':T,'W':W,'D':D,'epsilon':eps,
        'L_s':L,'slow_step_s':P,'history_cells':HISTORY,'history_nominal_s':H,
        'Hplus_s':history_plus,'Do_plus_bound_s':scan_plus,'cell_min_s':pminus,'cell_max_s':pplus,
        'architecture':'D_o + I_o <= L; mandatory full scans, protected registration, known clock range',
        'late_report_and_install_aperture_ns':last_release_slack_ns,
        'sufficient_peak_room_per_1ms_us':F(base['peak']['remaining_serial_pp'])*10,
        'R':B-b,'S2_max':S2,'weak_E_aperture_s':aperture,'direct_default':0,'delta_exec':delta,
        'anchored_Q_upper':anchor_q,'anchor_contributions':{'accumulation':accumulation,'weak_E_edge':edge,'execution':delta},
        'history_certificate':{'source':HANDOFF,'numeric_replay':terms,'fast_contribution':VISIBLE_FAST,'edge_contribution':VISIBLE_EDGE,
            'inverse_visibility_coefficient':VISIBLE_SLOW,'working_visibility_floor':gamma,'priced_q':q,
            'gamma_threshold_by_direct_budget':{str(d):VISIBLE_SLOW/(eps-delta-d-VISIBLE_FAST-VISIBLE_EDGE)
                                               for d in (F(0),F(1,100000),F(1,10000))},
            'examples':[{'gamma':y,'d':d,'Q_upper':history_q(y,d),'risk_headroom':eps-history_q(y,d)}
                        for y in (F(1),gamma) for d in (F(0),F(1,100000),F(1,10000))]},
        'anchored_Q_upper_with_d':{str(d):min(1,anchor_q+d) for d in (F(1,100000),F(1,10000))},
        'without_a_visibility_floor':{'physical_Q_upper_from_core':anchor_q,'joint_stops_upper_eq3':no_visibility_stop,
            'price_geometry_and_stops':'all fast and potential slow pair intervals in (3), empty-history weight bounded by one; charge first occupied-word, direct or execution stop',
            'eta0':upper(F(0),no_visibility_stop),'unbounded_eta':upper(None,no_visibility_stop),
            'full_bus_upper_on_registered_slots_s':broad_slots_upper,
            'full_bus_upper_on_registered_slots_percent':100*broad_slots_upper/T},
        'late_high_at_actual_first_slow':{'height':(B-b)/2,'ramp_s':late['duration_s'],
           'latest_nominal_decision_s':H+L,'mu_bank_upper':mean,'prob_no_parent_lower':exp(-float(mean))},
        'true_closure_resets_before_stops_upper':hits,'hard_cell_count':max_cells,
        'zero_invalid_budget':izero,'unbounded_invalid_budget':worst,
        'C2_general_hard_caps':{'conditions':'Good prefix is charged by visit geometry; q times full hard bounds is charged on stopped histories. If no hard cap applies to remaining management/guard work, that contribution stays parameterized.',
            'source_head':PROOF,'priced_q':q,'eta0_pre_fast_s_upper':prehold,'eta0_E_Tfast_upper_s':prehold+q*T,
            'eta0_E_switch_upper_given_cell_command_cap':1+2*hits+q*c2_switch_cap,
            'pre_reads_upper':before_reads,'post_stop_word_visits_upper':q*visits_cap,
            'eta0_reads_upper':general_reads,'eta0_repairs_upper':general_repairs,
            'eta0_read_bus_s_upper':general_reads*read,'eta0_repair_bus_s_upper':general_repairs*write,
            'eta0_primary_total_bus_s_upper':general_total,'eta0_primary_percent_upper':100*general_total/T,
            'eta0_full_extra_s_budget':general_slack,'extra_bus_s_per_invalid':price_per_invalid,
            'last_integer_I_for_general_primary_only':general_slack//price_per_invalid,
            'eta0_primary_serial_upper_s':general_reads*serial_read+general_repairs*write},
        'budget_sensitivities':[{'gamma':y,'d':d,'q':rounded_up(history_q(y,d),9),
                                 'at_eta0':upper(F(0),rounded_up(history_q(y,d),9))}
                                for y,d in [(F(1),F(0)),(gamma,F(1,10000))]],
        'bounded_full_service':{'condition':'All normal and post-stop primary/guard E occupy existing E slots. All extra protected-bus management (registration, switching, state etc.) fits the retained reserved slot, including after a stop.',
            'maximum_management_frames':management_frames,'all_management_bus_upper_s':charged_management_limit,
            'all_primary_and_guard_bus_upper_s':slot_bus,'full_bus_upper_s':full_slots_upper,'full_bus_upper_percent':100*full_slots_upper/T,
            'all_primary_and_guard_serial_upper_s':slot_serial,'full_serial_upper_s':slot_serial+charged_management_limit,
            'fixed_candidate_with_same_management_cap_s':full_fixed_upper,'half_of_that_full_fixed_s':full_fixed_upper/2,
            'read_witness_exceeds_even_this_extended_half_s':fast_floor_bus_s-full_fixed_upper/2},
        'unscheduled_after_stop':{'condition':'Pre-stop estimate plus q times an independent hard upper for all remaining stopped-path work; replaces the scheduled-path estimate.',
            'no_invalid_pre_stop_primary_bus_upper_s':good_primary,
            'hard_post_stop_bus_budget_if_eta0_and_other_extra_terms_absent_s':post_limit},
        'persistent_invalid':{'Tfast_s':T,'fast_fraction':1,'switches':0,'nominal_full_rounds':all_fast_rounds,
            'mandatory_word_reads':reads_all_fast,'known_read_lower_s':fast_floor_bus_s,
            'known_read_lower_percent':100*fast_floor_bus_s/T,
            'excess_above_possible_half_s':fast_floor_bus_s-base['exclusion_half_s'],
            'deficit_sufficient_half_s':fast_floor_bus_s-base['sufficient_half_s'],
            'same_witness_with_one_invalid_per_730_cells':sparse_resets},
        'prefix_witness':{'first_invalid_resets_proving_exclusion':hi,'word_read_bus_lower_s':prefix_floor(hi),
            'bus_lower_percent':100*prefix_floor(hi)/T,'previous_count_lower_s':prefix_floor(lo),
            'condition':'admissible nominal execution may schedule that many isolated invalid closures; all work continues on the published lattice'},
        'fully_valid_empty_nominal_history':{'switches':1,'Tfast_s':'730*32L + D_o',
            'Tfast_upper_s':H+L,'fast_fraction_upper':(H+L)/T,'no_repair':True,
            'pure_reads_upper_s':empty_read_upper,'scope':'one possible history; not its expectation'},
        'peak':base['peak'],'fixed_comparator':{key:base[key] for key in ('fixed_class_lower_s',
             'fixed_candidate_upper_s','sufficient_half_s','exclusion_half_s','common_app_upper_s','common_init_upper_s')}}
    # A residual budget is joint. Axis intercepts set only the other *extra* terms
    # to zero to describe the boundary and do not qualify a physical implementation.
    if izero['signed_sufficient_extra_bus_s']>0:
        money=izero['signed_sufficient_extra_bus_s'];counts={
            'per_primary_word':izero['E_primary_word_reads_upper'],'per_complete_pass':izero['E_pass_reports_upper'],
            'per_closed_cell':izero['E_cell_closures_upper'],'per_mode_switch':izero['E_switch_upper'],
            'per_unique_primary_ERR_publication':izero['E_repairs_upper']}
        r['eta0_joint_budget_axis_intercepts_ns']={key:money*NS/n for key,n in counts.items()}
        r['eta0_added_full_guard_E_count_budget']=money/(read+write)
    if izero['known_primary_bus_upper_s']<=base['sufficient_half_s']<worst['known_primary_bus_upper_s']:
        lo=0;hi=max_cells
        while hi-lo>1:
            mid=(lo+hi)//2
            if upper(mid)['known_primary_bus_upper_s']<=base['sufficient_half_s']:lo=mid
            else:hi=mid
        r['eta_for_primary_only']={'last_integer_meeting':lo,'first_integer_exceeding':hi}
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    data=fixed_point();write_json('result.json',data,args.check)
    print('Q+ at gamma=1/2:',float(data['history_certificate']['priced_q']),
          'primary bus upper at I=0, s:',float(data['C2_general_hard_caps']['eta0_primary_total_bus_s_upper']),
          'ordinary all-invalid bus lower, %:',float(data['persistent_invalid']['known_read_lower_percent']))
