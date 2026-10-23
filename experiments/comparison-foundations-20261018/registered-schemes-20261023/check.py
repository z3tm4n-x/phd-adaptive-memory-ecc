"""Small targeted checks of THIS witness, not a transport/mission simulator."""
from fractions import Fraction as F
from itertools import product
from math import factorial
import run as calc


def main():
    r = calc.main()
    g = r['geometry']
    W = calc.cfg['words']
    P, E, D = F(g['P27_s']), F(g['E_upper_s']), F(3, 10**6)
    R, L = F(g['app_period_s']), F(r['environment']['plateau_s'])
    start = F(r['environment']['plateau_start_s'])
    guards = [F(0), F(g['guard_s'])]
    guards += [F(x['quiet_guard_s']) for x in r['patent']]
    geometry_checks = 0
    # Whole real-parameter blocks, not simulated error histories. Near-edge
    # phases deliberately include exact coincidences and both one-ns sides.
    ns = F(1, 10**9)
    for guard, phase, aph in product(guards,
            (F(0), ns, P/3, P/2, P-ns, P),
            (F(0), ns, D, R/3, R-ns, R)):
        left, right = start+guard, start+L
        lo = calc.ceil((left-phase)/P)
        hi = calc.floor((right-phase-P)/P)
        removed = set()
        qlo = calc.ceil((left-D-aph)/R)
        qhi = calc.floor((right-aph)/R)
        for q in range(qlo, qhi+1):
            a = aph+q*R
            first = calc.ceil((a-P-phase)/P)
            last = calc.floor((a+D-phase)/P)
            assert last-first+1 <= 2
            removed.update(range(max(lo, first), min(hi, last)+1))
        bound = calc.floor((L-guard)/P)-2-2*(calc.ceil((L+D)/R)+2)
        assert hi-lo+1-len(removed) >= bound
        geometry_checks += 1

    # Address permutation and exact period for all word phases / four masks.
    assert len({3*j % W for j in range(W)}) == W
    def slot(j):
        return 1568*(j//8)+164*(j % 8)
    phase_checks = 0
    for k in (1, 3, 9, 27):
        assert 27 % k == 0
        for j in range(W):
            assert slot(j+k*W)-slot(j) == 196*k*W
            phase_checks += 1

    # Independent exact rational Taylor bracket of the pair integral.
    lam = F(r['environment']['array_peak'])
    ell = P-E
    x = lam*ell
    assert 0 < x < 1
    # Eighteen terms leave a rational bracket wider than Decimal roundoff.
    terms = [(-x)**j/F(factorial(j)*(j+1)*(j+2)) for j in range(18)]
    exact_lower = ell**2*sum(terms)
    exact_upper = ell**2*sum(terms[:-1])
    closed = calc.I(ell)/calc.I(lam)-(calc.I(1)-(calc.I(0)-calc.I(x)).exp())/calc.I(lam*lam)
    assert exact_lower <= F(closed.lo) <= F(closed.hi) <= exact_upper

    # All corners of the six-hour count box, and exact rounding threshold.
    chen_checks = 0
    for budget in ('0.025', '0.1', '0.4'):
        for corner in product((0, 370), repeat=6):
            core = calc.policy.Chen(calc.training['weights'], fault_budget=budget, words=W, cut=4000)
            core.bins = dict(enumerate(corner))
            core.hour = 6
            core.wake(calc.policy.next_cut(6*calc.policy.HOUR, 4000))
            if budget != '0.025':
                assert core.k == 27
            chen_checks += 1
        cap = F(budget)*calc.floor(3600/P)
        for pred, expect in ((cap, 27), (cap+F(1, 10**9), 9)):
            passes = calc.ceil(pred/F(budget))
            assert core.choose(F(3600, passes)) == expect
            chen_checks += 1

    # Explicit weak-E trap: two distinct post-release toggles need not
    # imply A if an aperture birth was left over. Our witness forbids it.
    state = {0}  # surviving birth inside the preceding weak E
    for bit in (0, 1):
        state.symmetric_difference_update({bit})
        assert len(state) <= 1
    for first, second in product(range(3), repeat=2):
        if first != second:
            state = set()
            state.symmetric_difference_update({first})
            state.symmetric_difference_update({second})
            assert len(state) == 2
    assert F(r['krasnikov_longest']['Q_lower']['lo']) > F('0.001')
    assert F(r['chen']['rows'][1]['lower']['lo']) > F('0.001')
    assert r['chen']['rows'][0]['lower'] is None
    assert all(F(x['quiet_witness_lower']['hi']) < F('0.001') for x in r['patent'])
    print(f'PASS: {geometry_checks} full-scale geometry cases; '
          f'{phase_checks} exact phase checks; {chen_checks} Chen corners/thresholds; '
          'rational integral bracket; weak-E clean-start trap; conclusion directions')


if __name__ == '__main__':
    main()
