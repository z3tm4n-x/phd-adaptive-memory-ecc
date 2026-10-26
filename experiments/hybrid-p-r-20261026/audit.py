"""PR250 service extraction and bounded T36 diagnostics, not a hybrid Q.

Only repository sources and standard-library arithmetic. No old Q campaign.
The candidate controller is not implemented and no acceptance is self-assigned.
"""
import argparse
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT/'experiments/t186-method-comparison/code-strength'
sys.path.insert(0, str(BASE))
from codec import Code

spec = importlib.util.spec_from_file_location('hybrid_directed', ROOT/'experiments/t114-two-stage-err/intervals.py')
iv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iv)
I = iv.I
NS = 10**9


def encoded(value):
    return (json.dumps(value, default=str, indent=2, sort_keys=True)+'\n').encode()


def ceil(value):
    return -(-value.numerator//value.denominator)


def load():
    inp = json.loads((HERE/'inputs.json').read_text('utf-8'))
    for name, digest in inp['source_sha256'].items():
        raw = (ROOT/name).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Frozen source changed: '+name)
    cfg = json.loads((ROOT/inp['fixed']['source']).read_text('utf-8'))
    return inp, cfg


def mu(v, a, P, g):
    """T36 appendix B.1, exact lower exposure before the scan."""
    if a < P or min(v,g) < 0:
        raise ValueError('invalid T36 exposure input')
    if a == P or v <= g*P:
        return F(0)
    if not g:
        return v*(a-P)
    if v < g*a:
        return (v-g*P)**2/(2*g)
    return (a-P)*(v-g*(a+P)/2)


def poisson_quantile(M, zeta):
    """Directed 48-digit Poisson CDF; upper tail used for the decision."""
    if M == 0:
        return dict(Q=0, tail_upper=F(0))
    term = total = F(1)
    for k in range(100):
        if k:
            term *= M/k
            total += term
        tail = I(1)-(I(-M)).exp()*I(total)
        upper = max(F(0), F(tail.hi))
        if upper <= zeta:
            return dict(Q=k, tail_upper=upper)
    raise ArithmeticError('Pilot tail limit exceeded')


def start_ticks(index, calendar):
    return (index//calendar['batch_size'])*calendar['frame_ticks'] + (index%calendar['batch_size'])*calendar['c_ticks']


def weak_e_trace(W, block_ticks):
    """One permitted late parent; real full39 codec, no second hit or A.

    This is an interface counterexample to *literal* T36 auxiliary deletion,
    not a newly simulated mission or an assertion that all E implementations
    preserve every newborn error. The service explicitly permits this survivor.
    """
    codec = Code(1)
    clean = codec.encode(0x13579bdf)
    birth = 165
    real = {0:birth}
    aux = [birth]
    history = []
    for index, start in enumerate((164,164+block_ticks)):
        snapshot, release = start+48, start+124
        decoded = codec.decode(clean ^ sum(1<<bit for bit in real))
        C_real = int(decoded['ERR'])
        C_aux = sum(t<=snapshot for t in aux)
        # PR250 E: older-than-start errors must disappear; late one may remain.
        real = {bit:t for bit,t in real.items() if t>=start}
        # Literal T36: a nonzero auxiliary reading deletes all marks at v_w.
        if C_aux:
            aux = [t for t in aux if t>release]
        history.append(dict(pass_index=index+1, word=3, start_ns=start,
            snapshot_ns=snapshot, release_ns=release, real_pass_C=C_real,
            literal_T36_aux_C=C_aux, residual_real_errors=len(real),
            residual_aux_marks=len(aux)))
    return dict(parents=1, parent_ns=birth, maximum_error_weight=1,
        second_parent=False, physical_A=False, T36_defined_second_hit_break=False,
        history=history, result='literal auxiliary counters disagree on pass 2',
        scope='permitted weak-E interface witness, not every physical implementation')


def calculate():
    inp,cfg = load()
    W=inp['fixed']['words']; T=F(inp['fixed']['mission_s']); eps=F(inp['fixed']['epsilon'])
    s,cal,obs=cfg['service'],cfg['calendar'],cfg['observation']
    xm,xp,J=map(F,(s['clock_lower'],s['clock_upper'],s['operation_endpoint_span_ns']))
    nominal_read=3*s['read_beat_ns']+s['decode39_ns']
    nominal={'read':F(nominal_read),
        'E':F(nominal_read+3*s['write_beat_ns']+s['turnaround_ns']),
        'initial':F(s['encode39_ns']+3*s['write_beat_ns']+s['turnaround_ns'])}
    upper={k:v*xp+J for k,v in nominal.items()}
    lower={k:v*xm-J for k,v in nominal.items()}
    fast_ticks=W*cal['g_ticks']
    fresh=F(inp['diagnostic']['counter_drain_source_ns'])
    drain_frames=ceil((fresh+J)/(cal['frame_ticks']*xm))
    block_ticks=fast_ticks+drain_frames*cal['frame_ticks']
    # Nominal clock and zero jitter are one permitted execution, not all timing.
    P=F(block_ticks,NS)
    Pminus=(block_ticks*xm-J)/NS
    Pplus=(block_ticks*xp+J)/NS
    last=start_ticks(W-1,cal)
    phase_points=[0,1,7,8,W-1]
    env=inp['proposed_environment']; r=env['residual']; p=env['p']
    b,B,Fs,ell=map(F,(env['background'],env['total_peak'],env['total_solar_mass'],env['old_growth_threshold']))
    amp=F(p['amplitude_above_background']); cycle=F(p['cycle_s']); width=F(p['width_s'])
    R,g,Fr=map(F,(r['cap_R'],r['growth_g'],r['mass_F_r']))
    total_g=2*amp/width+g
    assert b+amp+R==B and T/cycle*(width*amp/2)+Fr==Fs
    assert total_g==F(env['old_growth_rho_per_s'])*ell and g>0 and R>0
    rise=R/g; rise_mass=R*rise/2; plateau=(Fr-rise_mass)/R
    assert plateau>=0 and rise+plateau<T
    alpha,zeta=F(inp['diagnostic']['alpha_star']),F(inp['diagnostic']['zeta_star'])
    e0=F(inp['fixed']['lifetime_other_budget'])+alpha+zeta
    gamma=(eps-e0)/2; delta=(eps+e0)/2
    N=int(T/P)
    tail=poisson_quantile(B*P,zeta/N)
    K=tail['Q']; q=chi=F(1,W)
    threshold=(I(F(N)/alpha)).ln()
    new_pairs=chi*B*B*P*T/2
    residue=q*K*B*T
    V=new_pairs+residue
    # Even dropping all K/observation costs cannot fix original reserve (11).
    physical_bus_scan_lower=W*(3*s['read_beat_ns']*xm-J)/NS
    universal_pair_floor=chi*B*B*physical_bus_scan_lower*T/2
    actions=[]
    for k in inp['diagnostic']['action_block_multipliers']:
        a=k*P
        exposure=mu(B,a,P,total_g)
        actions.append(dict(k_block=k,period_nominal_s=a,
            optimistic_K0_first_bill=chi*(B*a)**2/2,
            zero_count_lower_exposure_at_B=exposure,
            zero_count_can_lower_B=exposure>F(threshold.hi),
            actual_admission='NOT_EVALUATED: original reserve invariant fails'))
    # Whole-horizon hard service cap. No early stopping at hidden A.
    passes=ceil(T/Pminus)
    reads=W*passes
    app=cfg['application']
    appreads=ceil((T*NS-app['first_ns']-app['read_offset_ns'])/app['epoch_ns'])
    read_bus=3*s['read_beat_ns']*xp+J
    write_bus=(3*s['write_beat_ns']+s['turnaround_ns'])*xp+J
    source_edge=F(NS)/(4*xm)+2/T
    cuts=F(NS)/(obs['cut_ns']*xm)+2/T
    rates=dict(scrub_reads=F(reads)/T,scrub_repair_hard=F(reads)/T,
        read_beats=F(3*reads)/T,write_beats_hard=F(3*reads)/T,
        decodes=F(reads)/T,turnarounds_hard=F(reads)/T,
        cuts=cuts,raw_source_records_hard=source_edge,
        logical_counter_increments_hard=F(reads)/T,
        pass_finalizations_hard=F(passes)/T,
        future_bound_inversions_hard=F(passes)/T,
        action_decisions_hard=F(passes)/T,
        retained_slot_gates_hard=F(NS)/(cal['g_ticks']*xm)+2*F(W)/T)
    output=dict(status='INITIAL_SERVICE_AND_T36_GATE_READY_NOT_HYBRID_ACCEPTANCE',
      input_status=inp['status'],source_count=len(inp['source_sha256']),
      input_sha256=hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest(),
      service=dict(W=W,code=[39,32],raw_bytes=6*W,nominal_ns=nominal,upper_ns=upper,
        lower_ns=lower,frame_ticks=cal['frame_ticks'],fast_cycle_ticks=fast_ticks,
        proposed_counter_drain_frames=drain_frames,proposed_block_ticks=block_ticks,
        proposed_P_nominal_s=P,proposed_P_lower_s=Pminus,proposed_P_upper_s=Pplus,
        phase_examples=[dict(control_index=j,word=(3*j)%W,start_ticks=start_ticks(j,cal)) for j in phase_points],
        control_gap_lower_ns=cal['c_ticks']*xm-J,
        control_E_slack_ns=cal['c_ticks']*xm-J-upper['E'],
        drain_after_last_release_lower_ns=(block_ticks-last)*xm-J-upper['E'],
        source_to_fresh_upper_ns=fresh,
        pending_at_decision='candidate must wait for operation release AND closed delivery frontier; not yet signed',
        pass_counter_bits=(W+1).bit_length(),time_ns_bits=int(T*NS).bit_length(),
        pass_index_bits=(ceil(T/Pminus)+1).bit_length(),
        phase_contract='bounded physical phases, nominal examples only; new T36 transfer required'),
      environment=dict(array_background=b,array_peak=B,array_solar_mass=Fs,
        known_amplitude=amp,known_extra_mass=T/cycle*width*amp/2,
        residual_R=R,residual_g=g,residual_F_r=Fr,total_growth_upper=total_g,
        lambda_cap_and_mass_preserved=True,physical_SAA=False,
        translated_r_witness=dict(rise_s=rise,plateau_s=plateau,mass=Fr,
          latest_onset_s=T-rise-plateau,fall='instantaneous down is permitted',
          scope='admissible shifted profiles; no schedule-class lower lemma claimed')),
      t36_gate=dict(e0=e0,delta=delta,gamma=gamma,N_full_mission=N,
        new_counter_exception_budget=None,
        budget_scope='optimistic transfer of the old 6e-6 only; new aggregation correctness/exception coverage not established',
        statistical_alpha_per_step=alpha/N,residue_zeta_per_step=zeta/N,
        log_threshold_lower=F(threshold.lo),log_threshold_upper=F(threshold.hi),
        residual_poisson_mean=B*P,residual_quantile=tail,K_star=K,
        V_pair_term=new_pairs,V_residual_term=residue,V_total=V,
        reserve_passes=V<=gamma,optimistic_K0_reserve_passes=new_pairs<=eps/2,
        pair_only_V_over_absolute_gamma_max=new_pairs/(eps/2),
        scan_raw_bus_lower_s=physical_bus_scan_lower,
        any_period_pair_floor=universal_pair_floor,
        any_period_pair_floor_over_absolute_gamma_max=universal_pair_floor/(eps/2),
        original_peak_reserve_fails_even_without_observation_and_residue=universal_pair_floor>eps/2,
        actions=actions,reachable_informative_history=None,admissible_relaxation=None,
        precise_blocker='T36(11) with B for all remaining T fails before first action; requires a proved different reserve, not a smaller numerical tolerance',
        interpretation='failure of this sufficient construction, not impossibility of A or failure of accepted PR250'),
      interface_witness=weak_e_trace(W,block_ticks),
      horizon_cost=dict(scope='hard full-horizon candidate always-scan service account, not a certified hybrid or expected saving',
        horizon_s=T,full_passes_upper=passes,reads_upper=reads,repairs_upper=reads,
        control_pure_bus_upper=F(reads)*(read_bus+write_bus)/(T*NS),
        control_serial_core_upper=F(reads)*upper['E']/(T*NS),
        initial_core_upper=F(W)*upper['initial']/(T*NS),
        initial_encodes=W,initial_write_beats=3*W,initial_turnarounds=W,
        application_read_count=appreads,application_write_count=0,
        application_core_upper=F(appreads)*upper['read']/(T*NS),
        application_payload_nominal=F(appreads)*32/(T*NS),
        common_ECC_nominal=F(appreads)*36/(T*NS),
        full_started_terminal_pass_paid=True,continued_after_hidden_A=True,
        ordinary_loss_recovery_and_false='retained quotas; any resulting FAST is inside universal all-E service cap, not assigned zero',
        retained_quotas=inp['retained_quotas'],extra_veto='unknown; all-E cap for SRAM does not make source/CPU work free',
        rates_per_s=rates,CPU_formula='sum(rate_i * unknown_CPU_ns_i)/1e9 + app/init CPU; no unit costs measured',
        energy_formula='T*sum(rate_i*incremental_nonoverlapping_J_i)+T*idle_W+app/init energy',
        transport_loss_state_bytes=131136,unknown_costs=inp['unknown_costs'],
        physical_or_hybrid_Q=None,full_hardware_winner=None),
      acceptance=False,old_Q_recomputed=False)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    value=calculate(); payload=encoded(value)
    target=HERE/'outputs/result.json'
    if args.check:
        if target.read_bytes()!=payload: raise AssertionError('Byte replay mismatch')
    else:
        target.parent.mkdir(exist_ok=True); target.write_bytes(payload)
    g=value['t36_gate']
    print(json.dumps(dict(sha256=hashlib.sha256(payload).hexdigest(),
        service_P_s=float(value['service']['proposed_P_nominal_s']),
        gamma=float(g['gamma']),V_pair=float(g['V_pair_term']),
        V_residual=float(g['V_residual_term']),K=g['K_star'],
        any_period_pair_floor=float(g['any_period_pair_floor']),
        reserve_passes=g['reserve_passes'],old_Q_recomputed=False)))
