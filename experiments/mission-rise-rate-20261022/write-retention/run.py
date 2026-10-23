"""Bounded, exact write-retention screen; accepted computations are read-only.

The app-only substitutions await the specific #196 applicability check.
The fixed witness and the application floor do not depend on that check.
No new ERR risk integration is performed when the price screen closes 5x.
"""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from math import gcd
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ACCEPTED = ROOT / 'experiments/t186-method-comparison/code-strength'
sys.path.insert(0, str(ACCEPTED))
import comparison as cmp
from cost import periodic_starts, per_bit_moment_caps
from parents import projected_groups

NS = cmp.NS


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, default=str) + '\n').encode()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    manifest = json.loads((HERE/'frozen-inputs.json').read_text('utf-8'))
    for path, digest in manifest['sha256'].items():
        if sha(ROOT/path) != digest:
            raise ValueError('Frozen dependency changed: ' + path)
    plan = json.loads((HERE/'input.json').read_text('utf-8'))
    cfg = json.loads((ROOT/plan['common_input']).read_text('utf-8'))
    return cfg, plan, manifest


def numeric(value):
    if isinstance(value, dict):
        return {k: numeric(v) for k, v in value.items()}
    if isinstance(value, list):
        return [numeric(v) for v in value]
    if isinstance(value, str):
        try:
            return F(value)
        except ValueError:
            pass
    return value


def write_count(W, epoch, first, R, H):
    """Offers in [0,H); no traversal of mission epochs or random starts."""
    if R < W*epoch or R % epoch or not 0 <= first < epoch or H < 0:
        raise ValueError('invalid deterministic bank schedule')
    cycles, tail = divmod(H, R)
    return cycles*W + min(W, max(0, (tail-1-first)//epoch + 1))


def calendar(cfg, N):
    a = cfg['application']; W = cfg['words']; epoch = a['epoch_ns']
    H = cfg['mission_s']*NS; first = a['first_ns']+a['write_offset_ns']
    R = N*epoch; D = cfg['constraints']['application_deadline_ns']
    if gcd(a['address_multiplier'], W) != 1 or N < W:
        raise ValueError('word permutation or retention constraint')
    total = 0; max_tail = 0; pending = 0
    # The permutation is bijective, so checking all j checks every word once.
    for j in range(W):
        start = first+j*epoch
        count = max(0, (H-1-start)//R+1)
        last = start+(count-1)*R if count else None
        total += count
        max_tail = max(max_tail, H-last if count else H)
        pending += bool(count and last+D > H)
    direct = write_count(W, epoch, first, R, H)
    max_initial = min(H, first+(W-1)*epoch)
    if direct != total or max(max_initial, max_tail) > R:
        raise ValueError('initial/tail or total-count mismatch')
    nr = periodic_starts(a['first_ns']+a['read_offset_ns'], epoch, H)
    return dict(retention_epochs=N, retention_ns=R, writes=direct, reads=nr,
        max_initial_cell_ns=max_initial, max_terminal_cell_ns=max_tail,
        writes_with_aperture_crossing_T=pending, words_checked=W,
        aperture_ns=D, sparse_writes_are_subset_of_original_slots=True,
        write_burst_duration_ns=W*epoch, synthetic_E_at_T=False,
        actual_starts_conditioned_as_Poisson=False)


def app_cost(cfg, n, nr, nw, bound):
    s = cmp.service(cfg, n)[bound]; H = cfg['mission_s']*NS
    if bound == 'lower':
        nr, nw = max(0, nr-1), max(0, nw-1)
    return (nr*s['app_read']+nw*s['app_write']+cfg['words']*s['initial'])/H


def fixed_candidates(cfg):
    out = {}
    for n, t in ((39, 1), (44, 2)):
        k = cmp.select_fixed(cfg, n, t)
        r = cmp.risk(cfg, n, t, cmp.period(cfg, k)['upper_ns'], cmp.service(cfg, n)['upper']['E'])
        out[str(n)] = dict(k=k, risk=r, period=cmp.period(cfg, k), timing=cmp.timing(cfg, n, k))
    return out


def price(cfg, n, t, nr, nw, fixed=None):
    """Full started work, including tail, paid initialization and post-A.

    Fixed repair/candidate formulas are the accepted formulas with ONLY the
    offered-write count changed. OFF has no dedicated scrub or observations.
    """
    T = F(cfg['mission_s']); W = cfg['words']; H = T*NS
    s = cmp.service(cfg, n); U = fixed['risk']['upper'] if fixed else F(0)
    reads = cmp.read_bounds(cfg, fixed['k']) if fixed else dict(upper=F(0), lower=F(0))
    N = reads['upper']
    parents = W*sum(projected_groups(n, {1: F(1)})[1:])*per_bit_moment_caps(cfg)['M1']
    repairs = min(N, 2*parents+U*N)
    upper = app_cost(cfg, n, nr, nw, 'upper')+(s['upper']['R']*N+(s['upper']['E']-s['upper']['R'])*repairs)/H
    lower = app_cost(cfg, n, nr, nw, 'lower')+s['lower']['R']*reads['lower']/H
    hard = app_cost(cfg, n, nr, nw, 'upper')+s['upper']['E']*N/H
    rates = dict(scrub_reads=N/T, scrub_corrections=repairs/T,
        application_reads=F(nr)/T, application_writes=F(nw)/T,
        decodes=(N+nr+nw)/T, encodes=F(nw+W)/T,
        read_beats=3*(N+nr+nw)/T, write_beats=3*(repairs+nw+W)/T,
        turnarounds=(repairs+nw+W)/T, app_dispatch=F(nr+nw)/T,
        initialization=F(W)/T, cuts=F(0), captures=F(0), records=F(0),
        decisions=N/T, timer_events=N/T)
    cpu = {k+'_ns': rates[k]/NS for k in ('app_dispatch', 'initialization', 'cuts', 'captures', 'records', 'decisions', 'timer_events')}
    energy = dict(rates, transport_requests=F(nr+nw)/T, transport_replies=F(nr+nw)/T,
                  transport_records=F(0), transport_cuts=F(0))
    return dict(core_upper=upper, core_lower=lower, all_history_core_upper=hard,
        scrub_reads_upper=N, repair_count_upper=repairs, full_cost_rates=rates,
        CPU_fraction_coefficients=cpu,
        CPU_formula='sum(rate_a*disjoint_action_ns_a)/1e9 + CPU_background_fraction',
        codec_busy_fraction=(s['decode']*rates['decodes']+s['encode']*rates['encodes'])/NS,
        energy_coefficients_per_second=energy,
        energy_formula='T*sum(rate_a*incremental_nonoverlapping_J_a)+T*idle_W',
        payload_Bps=4*F(nr+nw)/T,
        traffic_formula='4*(nr+nw)+(nr+nw)*(request_header+reply_header); headers in bytes are unknown',
        core_bus_formula='core_upper+B_controller_average; peak must separately fit service residual',
        raw_memory_bytes=6*W, additional_adaptive_transport_state_bytes=0,
        initialization=dict(encodes=W, write_beats=3*W, turnarounds=W,
                            bus_upper_ns=W*s['upper']['initial']),
        unmeasured=dict(controller_bus=None, controller_CPU_ns=None, energy_J=None,
                       policy_state_bytes=None, payload_buffer_bytes=None, codec_register_bytes=None),
        scalar_price=None, hardware_winner=None, bad_history_paid=True,
        pending_paid=True, post_A_paid=True, physical_Q=None)


def off_risk(cfg, n, N):
    r = cmp.risk(cfg, n, 1 if n == 39 else 2,
                 N*cfg['application']['epoch_ns'], cfg['constraints']['application_deadline_ns'])
    r['basis'] = 'T196 deterministic arrival apertures; new write schedule submitted to #196'
    r['specific_new_schedule_applicability'] = 'PENDING_THEORIST_REVIEW'
    return r


def thresholds(cfg):
    out = []
    for n in (39, 44):
        for divisor in (2, 1):
            target = F(cfg['epsilon'])/divisor
            valid = lambda N: off_risk(cfg, n, N)['upper'] <= target
            lo, hi = 0, 1
            while valid(hi):
                lo, hi = hi, hi*2
            while hi-lo > 1:
                mid = (lo+hi)//2
                if valid(mid):
                    lo = mid
                else:
                    hi = mid
            out.append(dict(n=n, target=target, last_sufficient_epochs=lo,
                next_epochs=hi, last_retention_s=F(lo*cfg['application']['epoch_ns'], NS),
                next_retention_s=F(hi*cfg['application']['epoch_ns'], NS),
                last_upper=off_risk(cfg, n, lo)['upper'] if lo else None,
                next_upper=off_risk(cfg, n, hi)['upper'],
                threshold_in_declared_family=lo >= cfg['words'],
                interpretation='boundary of this sufficient upper, not an admissibility boundary'))
    return out


def row(cfg, fixed, target):
    epoch = cfg['application']['epoch_ns']; W = cfg['words']
    requested = F(W*epoch, NS) if target == 'baseline' else F(cfg['mission_s'] if target == 'mission' else target)
    N = int(requested*NS)//epoch
    cal = calendar(cfg, N); nr, nw = cal['reads'], cal['writes']
    floor = app_cost(cfg, 39, nr, nw, 'lower')
    competitors = {}
    for n, t in ((39, 1), (44, 2)):
        off = off_risk(cfg, n, N)
        competitors[f'OFF{n}'] = dict(risk=off, price=price(cfg, n, t, nr, nw),
            sufficient=off['upper'] <= F(cfg['epsilon']),
            status='CONDITIONAL_SUBSTITUTION' if off['upper'] <= F(cfg['epsilon']) else 'NO_SUFFICIENT_CERTIFICATE_NOT_EXCLUDED')
        competitors[f'fixed{n}'] = dict(risk=fixed[str(n)]['risk'],
            price=price(cfg, n, t, nr, nw, fixed[str(n)]), sufficient=True,
            status='UNCHANGED_FIXED_WITNESS_EXTRA_CORRECT_E_IGNORED')
    admissible = {k: v for k, v in competitors.items() if v['sufficient']}
    best = min(admissible, key=lambda k: admissible[k]['price']['core_upper'])
    witness = admissible[best]['price']['core_upper']
    robust = competitors['fixed44']['price']['core_upper']
    return dict(target_s=target, requested_s=requested, retention_s=F(N*epoch, NS),
        rounding_down_s=requested-F(N*epoch, NS), calendar=cal,
        write_rate_per_s=F(nw, cfg['mission_s']), application39_floor=floor,
        competitors=competitors, lowest_sufficient_core_witness=best,
        witness_core_upper=witness, core_gain_ceiling=witness/floor,
        fixed44_only_gain_ceiling=robust/floor,
        extra_witness_bus_needed_for_possible_gain={str(g): max(F(0), g*floor-witness) for g in (5, 10)},
        parameter_bound='G_core_plus_controller <= (C_witness_upper+B_witness)/(C_app39_lower+B_adaptive_lower)',
        parameter_bound_requires_witness_full_feasibility=True,
        physical_Q=None, accepted_profile=False, fixed_class_lower=None)


def family_ceiling(cfg, fixed, nr, nw_max):
    # Fixed scrub cost is independent of the additional useful writes.
    # On [0,1] and [1,nw_max] numerator and denominator are affine in nw;
    # a positive-denominator ratio has constant derivative sign per segment.
    candidates = []
    for nw in (0, 1, nw_max):
        p = price(cfg, 44, 2, nr, nw, fixed['44'])
        floor = app_cost(cfg, 39, nr, nw, 'lower')
        candidates.append(dict(write_count=nw, ratio=p['core_upper']/floor))
    ceiling = max(p['ratio'] for p in candidates)
    # A diagnostic outside the frozen profile: necessary READ count for
    # gain g, even with zero useful writes, using this fixed witness.
    s39 = cmp.service(cfg, 39)['lower']; s44 = cmp.service(cfg, 44)['upper']
    const_ns = price(cfg, 44, 2, 0, 0, fixed['44'])['core_upper']*cfg['mission_s']*NS
    requirements = {}
    for g in (5, 10):
        limit = (const_ns+g*s39['app_read']-g*cfg['words']*s39['initial'])/(g*s39['app_read']-s44['app_read'])
        requirements[str(g)] = dict(maximum_read_rate_necessary_per_s=limit/cfg['mission_s'],
            maximum_integer_read_count=int(limit), no_writes_relaxation=True,
            sufficient=False, frozen_read_schedule_changed=False)
    return dict(core_gain_ceiling=ceiling, endpoints_and_kink=candidates,
        write_count_domain=[0, nw_max], witness='fixed44',
        proof='positive affine ratio on [0,1] and [1,nw_max]; endpoints and kink suffice',
        independent_of_new_OFF_basis=True, independent_of_ERR_holds_and_rho=True,
        necessary_read_diagnostics=requirements)


def union_duration(intervals):
    result = []
    for a, b in sorted(intervals):
        if b < a:
            raise ValueError('negative interval')
        if result and a <= result[-1][1]:
            result[-1][1] = max(result[-1][1], b)
        else:
            result.append([a, b])
    return sum((b-a for a, b in result), F(0)), result


def holds(cfg, plan):
    fixtures = []
    short = F(cfg['adaptive']['short_hold_s']); long = F(cfg['adaptive']['long_hold_s'])
    for name, events in plan['hold_examples'].items():
        intervals = [(F(at), F(at)+(short if kind == 'FIRST' else long)) for at, kind in events]
        duration, merged = union_duration(intervals)
        fixtures.append(dict(name=name, events=events, all_long_sum_s=len(events)*long,
            typed_sum_s=sum(b-a for a, b in intervals), union_s=duration, union_intervals=merged,
            scope='already causally classified events, nominal intervals only; not a mission expectation'))
    old = json.loads((HERE.parent/'outputs/pilot.json').read_text('utf-8'))
    r = next(r for r in old['rows'] if r['k'] == 27 and F(r['rho_per_s']) == F('.048'))
    U = F(r['information']['risk']['upper']); cal = numeric(r['information']['calendar'])
    cost = cmp.cost_result(cfg, 39, 1, 27, U, True, cal)
    if cost['core_SRAM_fraction_upper'] != F(r['cost']['core_SRAM_fraction_upper']):
        raise ValueError('accepted price does not replay from stored risk/calendar')
    ad = cost['adaptive']; s = cmp.service(cfg, 39); T = F(cfg['mission_s'])
    slots = F(2+cmp.ceil((ad['hold_length_s']*NS+s['J'])/(cfg['calendar']['c_ticks']*s['xminus'])))
    ordinary_hold_reads = ad['ordinary_publications_upper']*slots
    remaining = ad['ordinary_added_reads_upper']-ordinary_hold_reads
    if remaining < 0:
        raise ValueError('ordinary-hold separation removed recovery/outage work')
    N = min(ad['reads_hard_upper'], cmp.read_bounds(cfg, 27)['upper']+remaining+ad['bad_history_reads_upper'])
    repairs = min(N, 2*cost['expected_parent_count_upper']+U*ad['reads_hard_upper'])
    apps = cmp.count_apps(cfg)
    best_possible = app_cost(cfg, 39, apps['read'], apps['write'], 'upper') + (s['upper']['R']*N+(s['upper']['E']-s['upper']['R'])*repairs)/(T*NS)
    return dict(fixtures=fixtures, accepted_k27_ordinary_hold_probe=dict(
        rho_per_s=F('.048'), risk_reused_without_reintegration=U,
        accepted_core_upper=cost['core_SRAM_fraction_upper'],
        optimistic_zero_ordinary_hold_expression=best_possible,
        maximum_reduction_of_this_expression=cost['core_SRAM_fraction_upper']-best_possible,
        maximum_relative_reduction=1-best_possible/cost['core_SRAM_fraction_upper'],
        ordinary_hold_read_addend_removed=ordinary_hold_reads,
        remaining_recovery_outage_startup_addend=remaining,
        bad_history_addend_kept=ad['bad_history_reads_upper'],
        support_reads_upper_kept=cmp.read_bounds(cfg, 27)['upper'],
        reads_after_optimistic_removal=N, repairs_after_optimistic_removal=repairs,
        extra_veto_rate=None, source_record_capture_cut_decision_costs_not_removed=True,
        new_price_certificate=False,
        scope='ceiling on possible improvement from this term alone, not a lower bound on actual cost'))


def validate(cfg, plan, fixed, rows, bounds, family, hold):
    checks = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)
    # Independent explicit offer enumeration on small calendars, with offer
    # equality at T, one-ns neighbors, bank-boundary and final-aperture cases.
    tested = 0
    for W in (1, 4, 8):
        e, first = 10, 6
        for N in (W, W+1, 5*W):
            R = N*e
            offers = [m*R+first+j*e for m in range(5) for j in range(W)]
            ends = {0, 1, R, 2*R, 4*R}
            for t in offers:
                if t <= 4*R:
                    ends.update((max(0, t-1), t, t+1))
            for H in ends:
                check('enumerated arrivals '+str((W, N, H)), write_count(W, e, first, R, H) == sum(t < H for t in offers))
                tested += 1
    baseline = rows[0]; nr = baseline['calendar']['reads']; nw = baseline['calendar']['writes']
    apps = cmp.count_apps(cfg)
    check('baseline equals old arrivals', nr == apps['read'] and nw == apps['write'])
    oldoff = json.loads((ACCEPTED.parent/'app-only/outputs/result.json').read_text('utf-8'))
    check('baseline OFF44 exact accepted upper', baseline['competitors']['OFF44']['risk']['upper'] == F(oldoff['Q_upper']))
    for n, t in ((39, 1), (44, 2)):
        expected = cmp.cost_result(cfg, n, t, fixed[str(n)]['k'], fixed[str(n)]['risk']['upper'])
        actual = baseline['competitors'][f'fixed{n}']['price']
        check('baseline fixed cost/rates identity '+str(n), actual['core_upper'] == expected['core_SRAM_fraction_upper'] and actual['core_lower'] == expected['core_SRAM_fraction_lower'] and actual['full_cost_rates'] == expected['full_cost_rates'] and actual['energy_coefficients_per_second'] == expected['energy_coefficients_per_second'])
        check('unchanged fixed witness timing '+str(n), fixed[str(n)]['timing']['app_deadline_slack_ns'] >= 0 and fixed[str(n)]['timing']['control_slack_ns'] >= 0)
    check('complete preregistered grid', [r['target_s'] for r in rows] == plan['retention_targets_s'])
    for r in rows:
        tag = str(r['target_s']); cal = r['calendar']
        check('read cadence unchanged '+tag, cal['reads'] == nr)
        check('no added write slots '+tag, 0 < cal['writes'] <= nw and cal['retention_ns'] % cfg['application']['epoch_ns'] == 0)
        check('rounding bound '+tag, 0 <= r['rounding_down_s'] < F(cfg['application']['epoch_ns'], NS))
        check('ceiling direction '+tag, r['core_gain_ceiling'] <= r['fixed44_only_gain_ceiling'] <= family['core_gain_ceiling'])
        check('UNKNOWN preserved '+tag, r['physical_Q'] is None and r['fixed_class_lower'] is None and not r['accepted_profile'])
        for key, c in r['competitors'].items():
            check('full cost and nonnegative residual '+tag+key, c['price']['core_lower'] <= c['price']['core_upper'] <= c['price']['all_history_core_upper'])
            if not c['sufficient']:
                check('failed upper not exclusion '+tag+key, c['status'] == 'NO_SUFFICIENT_CERTIFICATE_NOT_EXCLUDED')
    for b in bounds:
        check('exact adjacent OFF bracket '+str((b['n'], b['target'])), b['last_upper'] <= b['target'] < b['next_upper'] and b['next_epochs'] == b['last_sufficient_epochs']+1)
    expected_union = {'single': 90, 'separated': 180, 'pair': 190, 'cluster': 189}
    for f in hold['fixtures']:
        check('typed union '+f['name'], f['union_s'] == expected_union[f['name']] and f['union_s'] <= f['typed_sum_s'] <= f['all_long_sum_s'])
    check('union duplicates/endpoints', union_duration([(F(0), F(2)), (F(0), F(2)), (F(2), F(3))])[0] == 3)
    check('hold probe retains other terms', hold['accepted_k27_ordinary_hold_probe']['remaining_recovery_outage_startup_addend'] > 0)
    check('full family price closes 5x without OFF', family['core_gain_ceiling'] < 5)
    return dict(status='PASS_NUMERICAL_CHECKS_ONLY', checks=checks,
        independent_small_calendar_cases=tested, physical_acceptance=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--write', action='store_true')
    p.add_argument('--probe', action='store_true')
    args = p.parse_args(); cfg, plan, manifest = load(); unchanged = deepcopy(cfg)
    start = time.perf_counter(); fixed = fixed_candidates(cfg)
    if args.probe:
        r = row(cfg, fixed, plan['retention_targets_s'][0])
        print(json.dumps(dict(elapsed_s=time.perf_counter()-start, rows=1,
            fixed44_gain_ceiling=float(r['fixed44_only_gain_ceiling']), wrote_outputs=False)))
        return
    rows = [row(cfg, fixed, t) for t in plan['retention_targets_s']]
    bounds = thresholds(cfg)
    family = family_ceiling(cfg, fixed, rows[0]['calendar']['reads'], rows[0]['calendar']['writes'])
    if family['core_gain_ceiling'] >= 5:
        raise RuntimeError('Price filter open: preregistered ERR calculations now required; do not claim a complete package')
    hold = holds(cfg, plan)
    checks = validate(cfg, plan, fixed, rows, bounds, family, hold)
    accepted = json.loads((ACCEPTED/'outputs/results.json').read_text('utf-8'))
    result = dict(status='CONDITIONAL_WRITE_RETENTION_SCREEN_READY_FOR_REVIEW',
        rows=rows, off_sufficient_thresholds=bounds, family_ceiling=family, holds=hold,
        fixed_candidates=fixed, codec_resource_models=accepted['resources'],
        new_ERR_risk_calls=[], new_ERR_risk_calls_count=0,
        skipped_ERR_reason='fixed44/app39 core ceiling <5 over entire write-count domain',
        new_archival_profiles_processed=0, physical_Q=None, profile_acceptance=None,
        scope='core-bus screen plus parameterized full-resource accounts; no scalar physical winner')
    payloads = {'result.json': encoded(result), 'checks.json': encoded(checks)}
    payloads['replay.json'] = encoded(dict(input_sha256=manifest['sha256'],
        code_sha256={'run.py': sha(HERE/'run.py')},
        output_sha256={name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()},
        plan_commit='ea5e0825c52def5874ce3c55b290f86da178df33', python='>=3.10; standard library only'))
    out = HERE/'outputs'
    if args.write:
        out.mkdir(exist_ok=True)
        for name, data in payloads.items():
            (out/name).write_bytes(data)
    else:
        mismatch = [name for name, data in payloads.items() if not (out/name).exists() or (out/name).read_bytes() != data]
        if mismatch:
            raise SystemExit('Replay differs; no files written: '+', '.join(mismatch))
    load()
    if cfg != unchanged:
        raise AssertionError('scientific input was mutated')
    print(json.dumps(dict(rows=len(rows), threshold_brackets=len(bounds), checks=len(checks['checks']),
        full_family_ceiling=float(family['core_gain_ceiling']), new_ERR_risk_calls=0,
        elapsed_s=time.perf_counter()-start, wrote_outputs=args.write)))


if __name__ == '__main__':
    main()
