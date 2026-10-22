"""Short T196 aperture certificate, not a new numerical comparison table.

Read accepted v4 sources without modifying them. Check boundary geometry,
an exhaustive tiny last-birth inclusion, and the existing rational upper.
"""
from fractions import Fraction as F
from itertools import combinations, product
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = ROOT / 'experiments/t186-method-comparison/code-strength'


def dec(x, places=18, up=False):
    x = F(x)
    q, r = divmod(x.numerator*10**places, x.denominator)
    q += int(up and r != 0)
    s = str(q).zfill(places+1)
    return s[:-places]+'.'+s[-places:]


def tiny_inclusion():
    """Every realized allowed E schedule is covered, not assumed Poisson.

    Toy integer half-ticks: E starts/finishes at even times, births at odd.
    Each E removes old births and retains late ones (worst weak-E service).
    Three positions suffice to witness first weight>2. Repeated positions
    exercise XOR cancellations. Pending E is never completed at horizon.
    """
    arrivals = (8, 20, 32)
    D = 4
    choices = [((a, a+2), (a, a+4), (a+2, a+4)) for a in arrivals]
    tested = failures = cross = terminal = initial = 0
    for horizon in (7, 9, 21, 33, 39):
        birth_times = [t for t in (1, 3, 7, 9, 11, 19, 21, 33, 35) if t <= horizon]
        for calendar in product(*choices):
            for times in combinations(birth_times, 3):
                for bits in product(range(3), repeat=3):
                    tested += 1
                    events = [(t, 0, b) for t, b in zip(times, bits)]
                    events += [(end, 1, start) for start, end in calendar if end <= horizon]
                    live = {}
                    for time, kind, value in sorted(events):
                        if kind:
                            live = {b: born for b, born in live.items() if born >= value}
                        else:
                            if value in live:
                                del live[value]
                            else:
                                live[value] = time
                            if len(live) <= 2:
                                continue
                            failures += 1
                            births = list(live.values())
                            cells = {sum(a <= born for a in arrivals if a < horizon) for born in births}
                            covered = len(cells) == 1
                            initial += int(max(births) < arrivals[0])
                            for j, a in enumerate(arrivals):
                                prev = 0 if j == 0 else arrivals[j-1]
                                if (a <= time <= min(a+D, horizon) and
                                    all(prev <= born <= min(a+D, horizon) for born in births) and
                                    min(births) < a <= max(births)):
                                    covered = True
                                    cross += 1
                                    terminal += int(a <= horizon < a+D)
                            if not covered:
                                raise AssertionError((horizon, calendar, times, bits, live))
                            break
    assert failures and cross and terminal and initial
    return dict(histories=tested, first_exceedances=failures,
                cross_witnesses=cross, pending_terminal_witnesses=terminal,
                initial_cell_witnesses=initial,
                note='finite pathwise oracle only, not a probability estimate or independent review')


def main():
    versions = json.loads((HERE/'versions.json').read_text())
    checks = []
    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append(name)
    for item in versions['sources']:
        raw = (ROOT/item['path']).read_bytes()
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        check('blob '+item['path'], blob == item['git_blob'])
    raw = (PACKAGE/'common-input.json').read_bytes()
    check('unchanged input v4', hashlib.sha256(raw).hexdigest() == versions['input_sha256'])
    cfg = json.loads(raw)
    sys.path.insert(0, str(PACKAGE))
    from comparison import risk, service, timing
    from cost import per_bit_moment_caps

    W, n, t = cfg['words'], 44, 2
    a = cfg['application']
    period_ns = W*a['epoch_ns']
    first_ns = a['first_ns']+a['write_offset_ns']
    horizon_ns = cfg['mission_s']*10**9
    deadline_ns = cfg['constraints']['application_deadline_ns']
    inverse = pow(a['address_multiplier'], -1, W)
    first = [first_ns+(inverse*w % W)*a['epoch_ns'] for w in range(W)]
    check('full address permutation', len(set(first)) == W)
    check('first virtual cell bounded by P', 0 <= min(first) <= max(first) <= period_ns)
    check('first deadline before P', max(first)+deadline_ns <= period_ns)
    last = [f+((horizon_ns-1-f)//period_ns)*period_ns for f in first]
    tails = [horizon_ns-x for x in last]
    check('last virtual cell bounded by P', 0 < min(tails) <= max(tails) <= period_ns)
    check('word apertures disjoint', deadline_ns < period_ns)
    check('global useful-write apertures disjoint', deadline_ns < a['epoch_ns'])
    check('strict app requests isolated', deadline_ns < min(a['write_offset_ns'], a['epoch_ns']-a['write_offset_ns']))
    check('clean init and initial pending unchanged', cfg['initial']['K0'] == 0 and cfg['initial']['pending'] is False)
    check('full useful write and nonrepairing read', a['data_bits'] == 32 and a['read_repair'] is False)
    check('declared singleton baseline only', cfg['environment']['baseline_p_s'] == {'1': '1'})
    tm = timing(cfg, n, 44837)
    check('same grant service already implies deadline', tm['app_response_upper_ns'] <= deadline_ns)
    check('write fits the unchanged grant', service(cfg,n)['upper']['app_write'] <= tm['application_aperture_ns'])

    # Physical arrival timestamps in v4 are exact ns. Clock of the executor
    # is already covered by the true-time end-to-end deadline, hence D=3000.
    P, D = F(period_ns, 10**9), F(deadline_ns, 10**9)
    m = per_bit_moment_caps(cfg)
    A3 = F(n*(n-1)*(n-2), 6)
    within = W*A3*P*P*m['M3']
    cross = W*3*A3*(m['peak_per_bit']*D*P*m['M2']+m['peak_per_bit']**2*D*D*m['M1'])
    delta = F(cfg['lifetime_other_budget'])
    upper = delta+within+cross
    replay = risk(cfg, n, t, period_ns, deadline_ns)
    check('existing moment/E bound exact agreement', upper == replay['upper'])
    check('single lifetime quota and no initial/direct charge', replay['terms']['lifetime_exceptions'] == delta
          and replay['terms']['initial'] == replay['terms']['direct'] == 0)
    check('hard and half-epsilon sufficient', upper < F(cfg['epsilon'])/2)

    # A looser numerical enclosure of the same exact-SI arrivals. This does
    # not certify a different workload produced by a drifting device clock;
    # that would require a separate deterministic arrival-window contract.
    Pguard = F(period_ns)*F(cfg['service']['clock_upper']) + F(cfg['service']['operation_endpoint_span_ns'])
    guard = risk(cfg,n,t,Pguard,deadline_ns)
    check('clock-inflated enclosure also sufficient', upper <= guard['upper'] < F(cfg['epsilon'])/2)
    oracle = tiny_inclusion()
    check('tiny causal-aperture last-birth oracle', oracle['histories'] > 0)

    out = dict(task=196, base_main=versions['base_main'], input_sha256=versions['input_sha256'],
        checks=checks, check_count=len(checks),
        calendar=dict(words=W, multiplier=a['address_multiplier'], inverse=inverse,
            first_write_ns=first_ns, first_word_visit_max_ns=max(first),
            first_deadline_max_ns=max(first)+deadline_ns, period_ns=period_ns,
            deadline_ns=deadline_ns, last_cell_max_ns=max(tails), last_cell_min_ns=min(tails),
            actual_terminal_pending_apertures=sum(x < deadline_ns for x in tails),
            semantics='fixed physical arrivals, causal E starts contained in arrival-to-deadline windows'),
        theorem_substitution=dict(n=n,t=t,moment_caps=m,within_cell=within,E_cross=cross,lifetime_exceptions=delta,
            Q_upper=upper,Q_upper_decimal=dec(upper,18,True),
            slack_lower_decimal=dec(F(cfg['epsilon'])-upper,18),
            relative_slack_lower_decimal=dec(1-upper/F(cfg['epsilon']),12),
            clock_enclosure_P_ns=Pguard,clock_enclosure_Q_upper=guard['upper'],
            clock_enclosure_Q_decimal=dec(guard['upper'],18,True),
            exact_Q=None,physical_unconditional_Q=None),
        service=dict(existing_app_response_upper_ns=tm['app_response_upper_ns'],
            application_aperture_ns=tm['application_aperture_ns'],
            app_write_upper_ns=service(cfg,n)['upper']['app_write'],
            note='retain app grant/dispatcher; disabling scrub does not itself prove physical hardware timing'),
        tiny_oracle=oracle,
        cost_scope='only extra scrub count is identically zero; full price is handed to #186',
        accepted_table_modified=False,full_engineer_replay_or_MC=False)
    print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True,default=str))


if __name__ == '__main__':
    main()
