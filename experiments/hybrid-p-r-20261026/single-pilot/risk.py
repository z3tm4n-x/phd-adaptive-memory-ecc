"""One rational substitution of published A1-A11, not a new theorem."""
from fractions import Fraction as F
import json
from sources import ceil, digest

M, USED, TAIL, BASE, RARE, THRESHOLD = 120000, 119989, 11, 2, 12000, 3
ALPHA, ZETA, BETA, DELTA_C_REQUIREMENT = F('1e-4'), F('1e-4'), F('.00055'), F('.00005')

def calculate(inp, cfg, hist):
    f, e = inp['fixed'], inp['proposed_environment']
    W, T, eps = f['words'], F(f['mission_s']), F(f['epsilon'])
    assert (W,T,eps,f['code']) == (131072,315576000,F('.001'),[39,32,1])
    assert f['initial_K0']==0 and f['useful_writes']==0
    assert not f['ordinary_reads_repair'] and not f['ordinary_reads_publish_ERR']
    b, amp = F(e['background']), F(e['p']['amplitude_above_background'])
    R,g,Fr = (F(e['residual'][k]) for k in ('cap_R','growth_g','mass_F_r'))
    Fs,B = F(e['total_solar_mass']), F(e['total_peak'])
    assert B==b+amp+R and Fs==2*Fr and e['residual']['distribution_over_paths'] is None
    s0,s1,a0,a1,P = map(F,('.025700','.025702','.051400','.051404','.025702'))
    tau0,tau1 = s0+M*a0,s1+M*a1
    delta,w,u = tau1-tau0,a0-P,R/2
    assert ceil(delta/a0)+1==TAIL and M-TAIL==USED
    first,last = TAIL+1,min(M,ceil((u/g-delta)/a0)-1)
    n = max(0,last-first+1)
    mu = w*(USED*b+n*(u-g*delta)-g*a0*F(n*(first+last),2))
    # The exact rational series certificates for .63 and 9.22 are published in check.py.
    score = F('.63')*mu-THRESHOLD
    assert score>F('9.22')
    ae,h = F('308.42'),F('.078')
    intp2 = b*b*T+b*Fs+amp*Fs/3
    s2 = intp2+(2*(b+amp)+R)*Fr
    qb = h*s2/W
    tail = (B*P)**2/2
    me = (b+amp+u)*ae+g*ae**2/2
    be = (me+me**2/2)/W
    q0 = qb+F(f['lifetime_other_budget'])+ALPHA+ZETA+BETA
    q = q0+DELTA_C_REQUIREMENT
    assert tail<ZETA and be<BETA and q<eps
    published = json.loads(hist['theory_result.json'])
    assert published['checker_sha256']==digest(hist['theory_check.py'].encode())
    exact = dict(exposure_lower=mu,log_test_lower_C3=score,Qbase_upper=qb,
                 residual_tail_upper=tail,excursion_mass_upper=me,excursion_risk_upper=be,
                 Q_upper_excluding_deltaC=q0,deltaC_allowable_upper=eps-q0,
                 Q_upper_if_example_requirement_met=q)
    for key,value in exact.items():
        assert value==F(published['exact_checks'][key]['exact']),key
    svc,cal=cfg['service'],cfg['calendar']
    xm,xp,J=map(F,(svc['clock_lower'],svc['clock_upper'],svc['operation_endpoint_span_ns']))
    ticks=W*cal['g_ticks']+7*cal['frame_ticks']
    block=F(ticks,10**9)
    assert s0<=block*xm-J/10**9 and block*xp+J/10**9<=s1
    assert a0<=BASE*block*xm-J/10**9 and BASE*block*xp+J/10**9<=a1
    assert RARE*block*xp+J/10**9<=ae and a1+P<=h
    # Conservative absolute-time window; fresh is subtracted again as an explicit reserve.
    last_used_close_upper=s1+USED*a1
    final_window=tau0-last_used_close_upper-F(inp['diagnostic']['counter_drain_source_ns'],10**9)
    assert final_window>0
    last_slot=(W-1)//cal['batch_size']*cal['frame_ticks']+(W-1)%cal['batch_size']*cal['c_ticks']
    Eplus=(3*svc['read_beat_ns']+svc['decode39_ns']+3*svc['write_beat_ns']+svc['turnaround_ns'])*xp+J
    tail_drain=(ticks-last_slot)*xm-J-Eplus
    final_gate=tail_drain-inp['diagnostic']['counter_drain_source_ns']
    assert final_gate>0
    quiet=b/10
    quiet_mass=(b+quiet)*tau1+amp*F(e['p']['width_s'])/2
    assert quiet*T<Fr and 1-quiet_mass>F('.66')
    return dict(status='CONDITIONAL_CANDIDATE_SHARED_ALL_BRANCHES_NOT_ACCEPTED',
        exact=exact,timing=dict(block_ticks=ticks,tau_lower_s=tau0,tau_upper_s=tau1,
            last_used_close_upper_s=last_used_close_upper,group_prepare_window_s=final_window,
            last_tail_main_release_to_query_lower_ns=tail_drain,
            fresh_tail_final_gate_budget_lower_ns=final_gate,
            final_gate_condition='no later relevant guard E; final health/pending/ready gate and install must still fit, otherwise base',
            group_prepare_window_does_not_replace_final_health_fence=True,
            runtime_deadline='decision boundary, earlier than cancellation of next base scan',
            per_batch_processing_limit_ns=cfg['observation']['batch_ready_ns'],
            measured_WCET_ns=None),
        budgets=dict(delta0=F(f['lifetime_other_budget']),alpha_once=ALPHA,zeta_once=ZETA,
            rare_allowance=BETA,base_full_T=qb,delta_C=None,
            delta_C_example_requirement=DELTA_C_REQUIREMENT,
            delta_C_proved_in_delta0=False,hardware_probability_established=False,
            no_reset_after_loss_restore_or_A=True),
        reachability=dict(fixed_path_r=quiet,mass_to_query_upper=quiet_mass,
            no_parent_probability_lower=1-quiet_mass,
            condition='fixed admissible quiet path; healthy channel with usable closed-prefix certificate',
            physical_channel_positive_probability_established=False,
            universal_admission_probability_lower=None,
            allowed_outage_can_cover_whole_training=F(inp['retained_quotas']['ordinary_outage_fraction'])*T>tau1),
        conditional_Q_not_branch_conditioned=True)
