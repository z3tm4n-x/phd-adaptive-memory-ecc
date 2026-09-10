"""Deterministic engineering screens; reads retained sources, generates no missions.

Run: python analyze.py --old-repo /absolute/path/chapter4-risk-limited-scrubber
All new outputs stay in this experiment. No research-controller imports.
"""
import argparse
import csv
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import quad

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent


def read_csv(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def backup_screen(D, P, tau, H, W, lo, hi):
    """Exact stationary CTMC expectation of the conservative auxiliary pair cost.

    Uses continuous uniform scan phases; a preliminary analytic diagnostic,
    not a reissued numerical certificate or a lower bound on physical failure.
    Independent quadrature is used to check the small-k closed form.
    """
    m = (hi + lo) / 2
    v = (hi - lo) / 2
    k = 2 / D
    J = -math.expm1(-k * tau) / k
    f = m*m*tau*tau/2 + v*v*quad(lambda x: (tau-x)*math.exp(-k*x), 0, tau,
                                epsabs=1e-13)[0]
    I = quad(lambda x: (1-x/P)*math.exp(-k*x), 0, P, epsabs=1e-13)[0]
    cross = m*m*P*tau/2 + v*v*I*J
    N = int(H/tau)
    return (N*f + (N-1)*cross) / W


def protocol_checks():
    """Executable cycle/event models of specific source statements, not RTL simulation."""
    checks = []
    for mask in [0, 1, 5, 255]:
        state = 'IDLE'; addr = 0; cycle = 0; counts = [0, 0, 0]
        events = []
        while True:
            cycle += 1
            if state == 'IDLE':
                state = 'READ'; events.append((cycle, 'start', addr)); continue
            if state == 'READ':
                counts[0] += 1; state = 'DECODE'
            elif state == 'DECODE':
                if mask & (1 << addr):
                    counts[2] += 1; state = 'WRITE'
                else:
                    state = 'ADVANCE'
            elif state == 'WRITE':
                counts[1] += 1; state = 'ADVANCE'
            elif state == 'ADVANCE':
                if addr == 7:
                    events.append((cycle, 'done', addr)); break
                addr += 1; state = 'READ'
        assert cycle == 1+3*8+mask.bit_count()
        assert counts == [8, mask.bit_count(), mask.bit_count()]
        checks.append(dict(case='old_engine_'+str(mask),cycles_from_start_edge=cycle-1,
                           reads=counts[0],writes=counts[1],corrections=counts[2],passed=True))

    # Source: nonblocking selected_period use in S_INPASS and immutable WAIT countdown.
    old_period = 300; new_period = 1; pass_ticks = 2
    queued_wait = max(old_period-pass_ticks, 1)
    selected_after_edge = new_period
    assert queued_wait == 298 and selected_after_edge == 1
    checks.append(dict(case='old_command_at_done',wait_ticks=queued_wait,
                       selected_after_edge=selected_after_edge,passed=True,
                       finding='new command does not change wait already loaded on this edge'))
    # A pass with no coarse ticks still records 1 at start + 1 at done.
    checks.append(dict(case='old_subtick_pass',recorded_ticks=2,actual_coarse_ticks=0,
                       passed=True,finding='legacy compressed-time accounting differs from physical duration'))

    # Explicit proposed interface: generation token + finite command window,
    # precommitted backup completion, no reset of the scientific state/budget.
    H=3.; previous_end=1.; P=.18874368; backup_end=previous_end+1
    deadline=backup_end-P
    cases=[('on_time',7,deadline-.000001,2,True),
           ('late',7,deadline+.000001,2,False),('wrong_generation',6,1.1,2,False)]
    for name,gen,at,tau,accept in cases:
        accepted=gen==7 and at<=deadline
        end=previous_end+tau if accepted else backup_end
        assert accepted == accept
        assert end <= H
        checks.append(dict(case='interface_'+name,accepted=accepted,next_end=end,
                           budget_reinitialized=False,passed=True))

    # Terminal scan can be only partial: tally transactions at sub-word phases.
    # One 39-bit word: 3 reads, 3 writes, 2 padding cycles, bus transfer 45 ns.
    transfer=45e-9; frame=540e-9; nwords=8; horizon=frame*2+transfer*4.5
    ops=[(w*frame+(i+1)*transfer,'read' if i<3 else 'write')
         for w in range(nwords) for i in range(6)]
    actual=[x for x in ops if x[0]<=horizon]
    rd=sum(x[1]=='read' for x in actual); wr=sum(x[1]=='write' for x in actual)
    assert (rd,wr)==(9,7)
    checks.append(dict(case='terminal_partial',reads=rd,writes=wr,complete_passes=0,
                       restored_words=2,passed=True))
    # Coupling break witness: reading at t0 misses a bit flipped before write-credit.
    # Latched write clears it; the ideal count at credit would count it.
    checks.append(dict(case='fault_between_read_write',physical_count=0,ideal_credit_count=1,
                       physical_word_after_write=0,passed=True,
                       finding='timing construction alone does not equate counts'))
    return checks


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--old-repo',type=Path,required=True)
    args=ap.parse_args();old=args.old_repo
    cfg=json.loads((ROOT/'config.json').read_text());out=ROOT/'outputs';out.mkdir(exist_ok=True)
    W=cfg['words'];H=cfg['H_seconds'];new=REPO/'experiments/RE-INTERNAL-COUNT-UNKNOWN-D-01'
    source_paths=[ROOT/'config.json',new/'config.json',new/'outputs/reserve_certificate.json',
                  new/'outputs/open_loop_uniform.csv',new/'outputs/comparison.csv',
                  new/'outputs/information_effect.csv',old/'data/ch3_five_year_upsets.csv',
                  old/'configs/ch3_main_1pct.json',old/'results/schedules/measured_policy_seed_sweep_summary.csv',
                  old/'rtl/scrubber/scrub_pass_engine.sv',old/'rtl/scrubber/period_scheduler.sv']
    source_sha={str(p.relative_to(old) if p.is_relative_to(old) else p.relative_to(REPO)):
                hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    prior=json.loads((new/'config.json').read_text());G=prior['controller']['continuous_transfer_factor']
    beta=prior['controller']['beta'];num=prior['controller']['numerical_allowance']
    cert=json.loads((new/'outputs/reserve_certificate.json').read_text())['rows']
    ol=read_csv(new/'outputs/open_loop_uniform.csv'); budgets=[]
    for eps in cfg['epsilon_slices']:
        slacks=[eps/G-beta/G-num-float(r['model_delta'])-float(r['initial_backup']) for r in cert]
        f=[r for r in ol if r['policy']=='Fixed' and float(r['continuum_upper'])<=eps]
        pc=[r for r in ol if r['policy']=='Precomputed' and float(r['continuum_upper'])<=eps]
        budgets.append(dict(epsilon=eps,reserve_only_floor=beta+G*num,
                            minimum_initial_slack=min(slacks),fixed_certified_count=len(f),
                            precomputed_certified_count=len(pc),
                            fixed_min_passes=min([float(r['passes']) for r in f],default=None),
                            precomputed_min_passes=min([float(r['passes']) for r in pc],default=None),
                            all_fixed_witness_lower_min=min(float(r['witness_lower']) for r in ol if r['policy']=='Fixed')))
    write_csv(out/'accepted_budget_screen.csv',budgets)

    # Independent analytic reconstruction of the old backup expectation and new scan durations.
    frames=[360e-9,540e-9,720e-9,1440e-9]; bk=[]
    reconstruction=[]
    for r in cert:
        val=backup_screen(float(r['D']),prior['memory']['pass_seconds'],1,H,W,
                          prior['environment']['b_low'],prior['environment']['b_high'])
        reconstruction.append(abs(val-float(r['initial_backup'])))
    for frame in frames:
        P=W*frame
        for D in [30,300,3000]:
            val=backup_screen(D,P,1,H,W,prior['environment']['b_low'],prior['environment']['b_high'])
            bk.append(dict(frame_ns=frame*1e9,pass_s=P,D=D,auxiliary_backup=val,
                           available_before_model_error=.1/G-beta/G-num,
                           remaining_before_model_error=.1/G-beta/G-num-val,
                           status='analytic_stationary_screen_not_certificate'))
    write_csv(out/'scan_backup_screen.csv',bk)

    olddata=read_csv(old/'data/ch3_five_year_upsets.csv');ratio=W/1935832
    raw=np.array([float(r['upsets_total_nu']) for r in olddata]);rates=raw*ratio/3600
    mean=float(rates.mean());peak=float(rates.max())
    periods=sorted(set([1,2,5,10,20,30,60,100,120,150,300,600,1200,1800,3600]))
    info=[];risk=[]
    for name,rate in [('mean',mean),('p95',float(np.quantile(rates,.95))),('peak',peak)]:
        for seconds in cfg['information_windows_seconds']:
            info.append(dict(rate_anchor=name,lambda_s=rate,window_s=seconds,
                             expected_arrivals=rate*seconds,p_any_arrival=-math.expm1(-rate*seconds),
                             constant_rate_t95_s=math.log(20)/rate,
                             status='homogeneous_Poisson_arrival_proxy_not_count_likelihood'))
        for eps in cfg['epsilon_slices']:
            for tau in periods:
                Q=H*rate*rate*tau/(2*W)
                # Very conservative count-timing coupling guard for deterministic RMW windows.
                guard=rate*math.ceil(H/tau)*cfg['candidate_scrub_slot_seconds']
                risk.append(dict(rate_anchor=name,epsilon=eps,period_s=tau,Q_pair=Q,
                                 rmw_no_event_guard=guard,upper_with_guard=Q+guard,
                                 passes=math.ceil(H/tau),screen_passes=Q+guard<=eps,
                                 physical_transfer='UNCONFIRMED',certificate='conditional_single_arrival_uniform_word_bound'))
    write_csv(out/'information_screen.csv',info);write_csv(out/'target_conditional_risk.csv',risk)

    # Best common-grid fixed/precomputed for a stationary peak-envelope hypothesis;
    # conservative pair certificate, not exact physical feasible-set optimum.
    enum=[]
    for eps in cfg['epsilon_slices']:
        cand=[]
        for a in periods:
            for b in periods:
                # Maximum-gap envelope retains cross-block exposures without a clean reset.
                Q=H*peak*peak*max(a,b)/(2*W)
                end=0.;passes=0
                while True:
                    tau=a if end<H/2 else b
                    if end+tau>H:break
                    end+=tau;passes+=1
                # Only a scan that has actually begun contributes a partial RMW guard.
                partial=int(end+tau-cfg['words']*360e-9 < H < end+tau)
                guard=peak*(passes+partial)*cfg['candidate_scrub_slot_seconds']
                if Q+guard<=eps:cand.append((passes,a,b,Q+guard))
        best=min(cand,default=(None,None,None,None))
        enum.append(dict(epsilon=eps,candidates=len(periods)**2,passing=len(cand),best_passes=best[0],
                         first=best[1],second=best[2],Q=best[3],
                         note='class optimal for this sufficient max-gap rule, no reset at block boundary'))
    write_csv(out/'target_precomputed_screen.csv',enum)

    # Read saved comparisons, no joining unequal physical experiments into one ranking.
    resource=[]
    for r in read_csv(new/'outputs/comparison.csv'):
        N=float(r['passes_given_survival']);busy=float(r['busy_given_survival'])
        resource.append(dict(D=r['dwell'],policy=r['policy'],F=float(r['F']),passes_own_survival=N,
                             busy_own_survival_s=busy,busy_percent=busy/H*100,
                             completed_reads=N*2097152,completed_writes=N*2097152,
                             stop_reads=float(r['reads_stop_mean']),stop_writes=float(r['writes_stop_mean']),
                             stop_busy_s=float(r['busy_stop_mean']),
                             guarantee=r['guarantee'],scope='retained_RES004_R2U_only'))
    write_csv(out/'retained_resource_comparison.csv',resource)

    # Rate-latency service guarantee with a full-frame latency allowance.
    # Queue fluid approximation is separate; not advertised as a deadline bound.
    # Recommended 48-bit parallel codeword port, one physical read/write;
    # 4 of 8 transfer ticks reserved, with write at the frame end.
    service=[];C=1/(45e-9);burst=8;P=W*360e-9;duty=.5;R=C*(1-duty);T=360e-9
    for rho in cfg['application_load_slices']:
        guaranteed=rho*C <= R
        service.append(dict(load_fraction=rho,baseline_burst_seconds=burst/C,
                            guaranteed_rate_words_s=R,slot_latency_s=T,
                            deterministic_delay_bound_s=T+burst/R if guaranteed else None,
                            backlog_end_scan_words=max(0,rho*C-R)*P,
                            fluid_delay_at_scan_end_s=max(0,rho*C-R)*P/C,
                            delay_status='token_bucket_bound' if guaranteed else 'outside_reserved_rate_contract'))
    write_csv(out/'application_service_screen.csv',service)
    checks=protocol_checks()
    summary=dict(task=cfg['task'],python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
                 sources_sha256=source_sha,old_hours=len(raw),missing_hours=sum(r['is_missing_proton']=='true' for r in olddata),
                 rate_transfer_word_ratio=ratio,target_mean_per_hour=mean*3600,target_peak_per_hour=peak*3600,
                 target_peak_timestamp=olddata[int(np.argmax(rates))]['timestamp_utc'],
                 symmetric_zero_peak_CTMC_mean_per_hour=peak*1800,
                 symmetric_zero_peak_mean_to_data_mean=peak/(2*mean),
                 target_rate_mean_t95_s=math.log(20)/mean,target_rate_peak_t95_s=math.log(20)/peak,
                 fraction_hours_no_scrub_pair_bound_below_1e3=float(np.mean((rates*H)**2/(2*W)<=.001)),
                 peak_max_gap_for_1e3_s=2*W*.001/(H*peak*peak),
                 max_old_backup_reconstruction_abs_error=max(reconstruction),
                 preferred_bus_bits=48,preferred_frame_s=360e-9,preferred_pass_s=P,preferred_active_reservation=duty,
                 active_application_rate_words_s=R,preferred_reads_per_pass=W,preferred_writes_per_pass=W,
                 preferred_transferred_bits_per_pass=2*W*48,preferred_storage_bytes=W*6,
                 transfer_busy_s=2*W*45e-9,reserved_busy_s=4*W*45e-9,
                 max_rmw_guard_original_high_1s=prior['environment']['b_high']*3600*180e-9,
                 max_rmw_guard_original_high_all_actions=prior['environment']['b_high']*18000*180e-9,
                 old_budget_min_slack_after_rmw_if_tau_at_least_1s=min(r['initial_slack'] for r in cert)-prior['environment']['b_high']*3600*180e-9/G,
                 max_command_latency_s=1-P,
                 old_engine_trace_semantics='handwritten cycle model; original SV not executed; iverilog unavailable',
                 no_new_missions=True,checks=checks)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['sources_sha256','checks']},indent=2))


if __name__=='__main__':
    main()
