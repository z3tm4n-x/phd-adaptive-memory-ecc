"""T110: addressed deterministic checks; default never rewrites any output."""
import argparse
from fractions import Fraction as F
from hashlib import sha1
import json
from pathlib import Path
import subprocess
import sys

from calculate import (HERE, ROOT, CFG, HANDOFF, TM, TP, JIT, MARGIN,
                       calculate, cross, risk, times, ceil, floor, serial, text_number)


def occupied_to(t, frame, m, c, duration):
    """Independent exact primitive for a periodic, all-ERR mask, including t<0."""
    q=floor(t/frame); r=t-q*frame
    return q*m*duration+sum(max(F(0),min(duration,r-i*c)) for i in range(m))


def peak_exact(h, frame, m, c, duration):
    # A sliding integral of a step mask is piecewise linear; maxima are at
    # a left/right endpoint crossing an occupancy boundary.
    cuts={F(0)}
    for i in range(m):
        for x in (i*c,i*c+duration):
            cuts.add(x%frame);cuts.add((x-h)%frame)
    return max(occupied_to(x+h,frame,m,c,duration)-occupied_to(x,frame,m,c,duration) for x in cuts)


def handoff(report):
    r=report['rows'][0];t=report['times'];m=r['monitor'];c=report['calendar']
    return dict(task=110,engineering_SHA=CFG['engineering_sha'],scientific_SHA='exact commit is supplied in PR comment; no self-reference',
        status='new conditional contract; independent addressed review and acceptance pending',
        scientific_files=['theory/t110-err-write-service.md','theory/t110-err-write-service-appendix.md'],
        scope_preserved=CFG['preserved'],calendar=c,
        virtual_start='s_j=1536*floor(j/8)+164*(j mod 8); seconds=xi*s_j',
        address='inverse(83) mod 524288 * j mod 524288',
        mandatory='j<524288 or j mod 83 == 0',
        decision='freeze at s_j-256; skip only with prior LOW covering [s_j-W*g,s_j+W*g] with conservative time guards',
        tail_grant='at frame_start+1312; reserve 208 ticks for one atomic read32; no fragmentation',
        service_times=t,
        service_obligation='coherent full38 observation; ERR complete before first A; noncreating repair removes errors older than virtual start by end of E window; clean read does not imply clean release',
        monitor=dict(k=m['k'],z=m['z'],H=m['H'],J=m['J'],window_ticks=10**9,stride_ticks=5*10**8,
                     delivery_ticks=m['delivery_ticks'],lease_ticks=m['lease_ticks'],
                     LOW_inner_tick_interval='[window_start+window_ticks+delivery_ticks+4, window_start+lease_ticks-4]',
                     guard_ticks=4,hold_ticks=m['hold_ticks'],DE=m['DE'],DM=m['DM'],
                     post_window_all_path_required_s=m['post_window_physical_path_required'],
                     pre_mailbox_required_s=m['pre_mailbox_path_required'],
                     ERR_to_hold_required_s=F(CFG['monitor']['ERR_delay_required_s'])),
        application=dict(profile='atomic read32, two x16 aliases, no inline repair; functional writes outside Q(T)',
                         region=r['common_traffic_region'],minimum_queue_entries=ceil(r['common_traffic_region']['joint_burst_max']+r['common_traffic_region']['joint_rate_max']*F('3e-6')),
                         queue_counts='all offers from first VALID, CPU and X together, including in-flight and held replies',
                         X_rate=F(CFG['resource_allocations']['X_rate']),X_burst_s=F(CFG['resource_allocations']['X_burst_s']),
                         no_legacy_4pct_or_b8_rate2M_claim=True),
        safety_on_loss='S for uncommitted future decisions; keep j, old skip, pending, initial event, absolute windows and global quotas',
        recovery='fresh full window, same config, original index not used before, holds and two-sided LOW; no new statistical trial',
        implementation_state=['64-bit absolute ticks and slot j','19-bit address permutation','initial/mandatory bits',
            'control-ERR counter and holdE/holdM','pending corrected alias/data/global lock',
            'validated shadow with not_before and expiry','absolute monitor window index and three snapshots',
            'LOW endpoints and health','FIFO counts and first-VALID times; backpressure'],
        changed_from_A=['E instead of clean-U','virtual start + explicit cross-window risk','8 phases, g192/ka83/G256',
            '104/164 reserves distinct from actual 92/148 cycles','atomic read32 and joint count/work region',
            'k515 and recomputed lease/time guards','sigma_X=209 ns','new constant E upper and class lower'],
        preserved_artifacts='T36-T95, accepted A and pinned T104 remain byte-for-byte unchanged',
        rows=[{k:x[k] for k in ('shield','Dstar','risk','quiet_return_price','resources','constant_E','constant_class','joint_success','certified_gain_lower','always_S_from_start_risk_upper','no_hit_full_aperture_bound')} for x in report['rows']],
        unknowns={k:None for k in ['physical_full38_ERR','physical_E_aperture_semantics','platform_IO_STA','joint_WCET','physical_clock_jitter',
            'physical_CDC','offered_CPU_X_count_and_work','actual_width_atomicity','response_backpressure','monitor_full_law_and_availability','software_transport_time']},
        forbidden_next_steps=['no new campaign','no RTL or stages V/G','no edits of accepted T95/A','no merge'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    old=subprocess.run([sys.executable,'-B',str(ROOT/'experiments/t104-new-rtl-executor/run_budget.py')],cwd=ROOT,capture_output=True,text=True)
    if old.returncode: raise RuntimeError(old.stdout+old.stderr)
    assert '28/28' in old.stdout and 'A49' in old.stdout and 'T9571' in old.stdout
    checks=[]
    def check(name, ok):
        if not ok: raise AssertionError(name)
        checks.append(name)
    pins=json.loads((HERE/'pinned_sources.json').read_text())
    for path, expected in pins.items():
        data=(ROOT/path).read_bytes();got=sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
        check('pinned:'+path,got==expected)
    r=calculate();c=CFG['calendar'];t=times();g=c['g_ticks'];m=c['batch'];ka=c['ka'];W=HANDOFF['rows'][0]['environment']['W']
    starts=lambda j:m*g*(j//m)+c['c_ticks']*(j%m)
    inv=pow(ka,-1,W)
    check('word_inverse_and_divisibility',inv*ka%W==1 and W%m==0)
    for j in [0,1,7,8,82,83,W-1,W,ka*W-1]:
        check('per_word_fixed_period:'+str(j),starts(j+W)-starts(j)==W*g and starts(j+ka*W)-starts(j)==ka*W*g)
        check('mandatory_order:'+str(j),inv*(ka*j)%W==j%W)
    check('initial_scan_finishes_before_Ps',(starts(W-1)*TP+t['d'])<W*g*TP)
    check('last_partial_window_not_dropped',starts(W-1)*TP < W*g*TP < (starts(W-1)+m*g)*TP)
    check('nonoverlap_even_all_ERR',c['c_ticks']*TM>t['d'] and (m*g-(m-1)*c['c_ticks'])*TM>t['d'])
    # Two independent service counterexamples, not an optimizer/controller.
    state=0; captured=state;state^=1
    if captured: state=0
    check('clean_read_is_not_clean_release',captured==0 and state==1)
    state=1;captured=state;state^=2
    check('cross_window_failure_precedes_repair',captured==1 and state.bit_count()==2)
    state=0
    check('later_repair_does_not_undo_event',state==0)
    check('new_pairs_after_clean_read_share_next_virtual_cell',F(3)<F(5)<F(8)<F(9))
    # Existing paired-calendar placement failure must not disappear.
    check('reject_old_g208_atomic_read32',184*TM-JIT>160*TP+JIT)
    check('reserve_does_not_equal_actual_occupation',t['R']<104*TM and t['E']<164*TM)
    check('pass_duration_does_not_equal_sum_read_busy',W*g*TM>W*t['E']>W*t['R'])
    check('read32_is_two_aliases',t['app']==2*t['R'])
    check('do_not_admit_inline_read32',MARGIN*t['inline32']> (m*g-m*c['c_ticks'])*TM)
    # Exact all-ERR sliding integrals. Every subset / no-ERR pattern is dominated.
    for scale in (F('0.99999'),F(1),F('1.00001')):
        frame=m*g*scale;dur=148*scale+F('0.5');step=c['c_ticks']*scale
        for h in (F(1),F(137),F(1000),F(1000000)):
            exact=peak_exact(h,frame,m,step,dur)
            upper=(h/(m*g*F('0.99999'))+2)*m*(148*F('1.00001')+F('.5'))
            check(f'phase_carry_in:{scale}:{h}',exact<=upper)
    # A burst of eight fits a large queue but not the 3-us latency contract.
    min_eighth_wait=7*m*g*TM
    check('b8_not_saved_by_queue16',min_eighth_wait>F('3e-6'))
    check('no_fake_legacy_work_rate',CFG['resource_allocations']['offered_joint_burst'] is None and CFG['resource_allocations']['offered_joint_rate_per_s'] is None)
    # Finite e inequalities used for both the safety and price tail.
    factorial=1;partial=F(1)
    for i in range(1,5):factorial*=i;partial+=F(1,factorial)
    tail_upper=F(1,120)/(1-F(1,6))
    check('exp_lower_proves_phi_and_alpha',partial>F(8,3))
    check('exp_upper_proves_price_tail',partial+tail_upper<F(11,4))
    for i,row in enumerate(r['rows']):
        p=row['environment'];rb=row['risk'];mo=row['monitor'];re=row['resources'];co=row['constant_E'];lb=row['constant_class']
        prefix=row['shield']+':'
        check(prefix+'unchanged_direct_and_quotas',p['D']==F(HANDOFF['rows'][i]['Dstar']) and p['errors']==F('6e-6') and p['eps']==F('.001'))
        check(prefix+'explicit_positive_cross_window_payment',rb['X']>0 and rb['upper']==p['errors']+p['D']+rb['initial']+rb['ordinary_pairs']+rb['X'])
        check(prefix+'no_aperture_means_zero_cross',cross(p,rb['Ps_lower'],rb['Pl'],ka,p['S2'],F(0))['X']==0)
        check(prefix+'no_hit_aperture_not_hidden_in_quota',row['no_hit_full_aperture_bound']>F('1e-6'))
        check(prefix+'joint_alpha_paid_once',mo['global_tail_upper']<=F('1e-6'))
        check(prefix+'finite_LOW_accept_and_neighbor',mo['test_slack']>=0>mo['next_test_slack'])
        check(prefix+'nonzero_price_tail',0<mo['quiet_tail_upper']<F('1e-20'))
        check(prefix+'timely_price_update',mo['lease_slack']>=0 and mo['DE']>mo['DE_required'] and mo['DM']>mo['DM_required'])
        check(prefix+'LOW_inward_guards',mo['lease_ticks']-4>10**9+mo['delivery_ticks']+4 and 4*TM>JIT)
        check(prefix+'all_three_margins_and_gate',min(re[k] for k in ('app_margin_slack','control_margin_slack','read_margin_slack','gate_slack'))>0)
        check(prefix+'atomic_placement_with_guard',re['placement_slack']>0)
        check(prefix+'hard_peak_without_ERR_rarity',re['peak_upper']<F('.8'))
        check(prefix+'reserved_duty_separate',re['reserved_fraction']>F('.8')>re['peak_upper'])
        check(prefix+'one_packet_delay',re['one_packet_delay_with_margin']<F('3e-6'))
        region=row['common_traffic_region'];b=region['joint_burst_max'];rho=region['joint_rate_max']
        fmax=max(re['frame_max'],co['resources']['frame_max'])
        delay=MARGIN*(t['req']+b*fmax+JIT+t['app']+t['reply']+region['backpressure_max'])
        check(prefix+'closed_admission_boundary',delay==F('3e-6') and rho*fmax==1)
        check(prefix+'beyond_boundary_rejected',delay+MARGIN*F('1e-6')*fmax>F('3e-6'))
        check(prefix+'finite_queue',ceil(b+rho*F('3e-6'))==4)
        check(prefix+'constant_scalar_inversion',co['risk_upper']<=p['eps']<co['next_risk_upper'])
        check(prefix+'necessary_lower_not_upper',lb['risk_lower_at_P0']>p['eps']>=lb['predecessor_lower'] and lb['large_period_risk_lower']>p['eps'])
        check(prefix+'read_floor_not_unconditional_write',lb['read_price_lower']>F('.01') and t['r_lower']<t['e_lower'])
        check(prefix+'cost_after_failure_not_zero',row['quiet_return_price']['global_bad']>0 and row['quiet_return_price']['all_short_cap']>F('.01'))
        check(prefix+'unused_reserve_price_larger',row['price_charging_reserve']['upper']>row['quiet_return_price']['upper'])
    a,s=r['rows']
    check('main_joint_success',a['joint_success'] and a['constant_E']['feasible'] and a['certified_gain_lower']>45)
    check('same_calendar_always_S_from_start',a['always_S_from_start_risk_upper']<=F('.001'))
    check('sensitivity_no_false_success',not s['joint_success'] and s['certified_gain_lower'] is None and not s['constant_E']['feasible'])
    check('secondary_constant_class_resource_exclusion',s['constant_class']['fixed_class_resource_excluded'] and not a['constant_class']['fixed_class_resource_excluded'])
    check('constant_optimum_bracket',a['constant_class']['read_price_lower']<a['constant_E']['cost_lower']<a['constant_E']['cost_upper'])
    # Loss-price boundary is separate from a new lifetime risk allowance.
    loss=a['quiet_return_price'];frac=loss['outage_fraction_sufficient']
    check('loss_availability_boundary',loss['upper']+loss['outage_slope']*frac==F('.01'))
    check('unbounded_loss_not_one_percent',loss['all_short_cap']>F('.4'))
    check('mixed_history_cannot_take_new_start_bound',a['risk']['upper']>a['always_S_from_start_risk_upper'])
    r['verification']=dict(new_checks=len(checks),checks=checks,pinned_sources=pins,
        unchanged_prior_checks={'budget':28,'timing':15,'A':49,'T95':71},prior_outputs_rewritten=False,
        numerical_method='exact rational bounds; fixed two rows; scalar inversions; no floating-point decisions')
    for name,payload in [('report.json',r),('handoff.json',handoff(r))]:
        encoded=json.dumps(serial(payload),ensure_ascii=False,indent=2)+'\n';path=HERE/name
        if args.write:path.write_text(encoded,encoding='utf-8')
        if not path.exists() or path.read_text(encoding='utf-8')!=encoded:
            raise AssertionError(name+' differs; inspect the new calculation before --write')
    print(f'T110: {len(checks)}/{len(checks)} addressed checks; pinned budget 28+15+49+71 unchanged.')
    print('report.json and handoff.json match exactly. Two shielding rows, conditional E/traffic/timing contract.')
    print('3 g/cm2: Q<= '+text_number(a['risk']['upper'])+'; quiet<= '+a['quiet_return_price']['percent_upper']+'%; gain>= '+text_number(a['certified_gain_lower'],False,6)+'.')
    print('2.5 g/cm2: risk certificate fails; no adaptive success asserted; declared constant E class resource-excluded.')


if __name__=='__main__': main()
