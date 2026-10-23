"""Finite registered-scheme calculation; no MC or transport implementation.

Run: python3 .../run.py ; compare committed output: add --check.
Accepted inputs/Decimal enclosure are read-only and hash checked.
"""
from fractions import Fraction as F
from hashlib import sha1
from importlib.util import module_from_spec, spec_from_file_location
from math import comb
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PINS = {
    'experiments/t186-method-comparison/stage2/policies.py': '2f0f94c39c9200337c267085b6262493e62ae800',
    'experiments/t186-method-comparison/stage2/training.json': 'b6182c39d4fc778eec7f50752b7fe393b3ba8bd7',
    'experiments/t186-method-comparison/code-strength/common-input.json': '31fe2d05282a283f2fa8da67147a8ad1baac1276',
    'experiments/t114-two-stage-err/intervals.py': 'fe57d6075e5ed5e807fd8f52e29387ccd4eda036',
}
for path, expected in PINS.items():
    data = (ROOT/path).read_bytes()
    actual = sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert actual == expected, (path, actual)


def module(name, path):
    spec = spec_from_file_location(name, ROOT/path)
    result = module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


policy = module('frozen_policy', 'experiments/t186-method-comparison/stage2/policies.py')
iv = module('accepted_intervals', 'experiments/t114-two-stage-err/intervals.py')
I = iv.I
cfg = json.loads((ROOT/'experiments/t186-method-comparison/code-strength/common-input.json').read_text())
training = json.loads((ROOT/'experiments/t186-method-comparison/stage2/training.json').read_text())
weights = tuple(map(F, training['weights']))
NS = 10**9


def floor(x):
    x = F(x)
    return x.numerator//x.denominator


def ceil(x):
    return -floor(-F(x))


def enclosure(x):
    x = x if isinstance(x, I) else I(x)
    return {'lo': str(x.lo), 'hi': str(x.hi)}


def tail(mu, threshold):
    """Chernoff for NHPP or counting process with compensator <=mu."""
    assert 0 < mu < threshold
    return (I(threshold-mu)+I(threshold)*(I(mu)/I(threshold)).ln()).exp()


def arrivals(first, step, T_ns):
    return max(0, ceil(F(T_ns-first, step)))


def main():
    W, n, T = cfg['words'], 39, F(cfg['mission_s'])
    env = cfg['environment']
    Z = env['reference_words']*env['reference_bits']
    b, B, FS, rho = (F(env[k]) for k in ('reference_background_per_s',
                         'reference_peak_per_s', 'reference_solar_mass', 'reference_growth_per_s'))
    rb, rB = b/Z, B/Z
    lam = W*n*rB
    P1, P = F(W*196, NS), F(27*W*196, NS)
    e = F(cfg['application']['epoch_ns'], NS)
    Rapp, D = W*e, F(3000, NS)
    xp, xm, J = (F(cfg['service'][k]) for k in ('clock_upper','clock_lower','operation_endpoint_span_ns'))
    E, AW = (F(v)*xp+J for v in (124, 144))
    Es, AWs = E/NS, AW/NS
    delta, freeze = F(10000, NS), F(320, NS)
    tau = P+Es+AWs+delta+2*J/NS
    L, ramp, start = F(115000), F(200), F(21600)
    rise_rate = (I(B)/I(b)).ln()/I(ramp)
    solar_upper = (B-b)*(L+2*ramp)
    assert rise_rate.hi < I(rho).lo and solar_upper < FS
    peak_start = start+ramp

    # Deterministic cells of the k27 calendar. Drop two boundary cells,
    # and at most two cells for each useful-write external aperture.
    guard = F(7, 3)*P+2*Es+4*delta+freeze
    length = P-Es
    dropped = 2*(ceil((L+D)/Rapp)+2)
    K_chen = floor(L/P)-2-dropped
    K_kras = floor((L-guard)/P)-2-dropped
    assert min(K_chen, K_kras) > 0 and guard > P and D < P

    # Two distinct active bits in the open cell and NO birth in the
    # preceding E aperture: the cell is clean even under weak E.
    # The complete P-blocks used by the witness are disjoint.
    mu_raw_chen = W*K_chen*comb(n, 2)*rB*rB*length*length
    single_factor = (I(0)-I(n*rB*P)).exp()
    mu_chen = I(mu_raw_chen)*single_factor
    q_constant_cells = I(1)-(I(0)-mu_chen).exp()

    # Pay the surrounding array-wide silence in the Krasnikov witness.
    # Integral_0^l (l-d)*exp(-lambda*d) dd.
    pair_integral = I(length)/I(lam)-(I(1)-(I(0)-I(lam*length)).exp())/I(lam*lam)
    mu_raw_kras = W*K_kras*comb(n, 2)*rB*rB*length*length
    mean_kras = I(W*K_kras*n*(n-1)*rB*rB)*(I(0)-I(lam*guard)).exp()*pair_integral
    q_kras = mean_kras-I(mu_raw_kras*mu_raw_kras/2)
    patent_rows=[]
    for window in (30,60,120):
        pg = P+window+2*Es+4*delta+freeze
        pk = floor((L-pg)/P)-2-dropped
        raw = W*pk*comb(n,2)*rB*rB*length*length
        mean = I(W*pk*n*(n-1)*rB*rB)*(I(0)-I(lam*pg)).exp()*pair_integral
        lower = mean-I(raw*raw/2)
        patent_rows.append(dict(window_s=window,quiet_guard_s=str(pg),cells_per_word=pk,
            sufficient_FAST_count=window//30+1,bonferroni_raw=enclosure(lower),
            quiet_witness_lower=enclosure(I(max(iv.D(0),lower.lo),max(iv.D(0),lower.hi))),
            conclusion='OPEN: this paid quiet witness does not cross epsilon'))

    # At most 350 main parents +20 aperture repeats per completed hour.
    # Before first A each repeat is charged to one predictably active word.
    bins = ceil(T/F(3600))+1
    mu_hour = lam*(3600+tau)
    mu_repeat = mu_hour/W
    count_bad = (tail(mu_hour, 351)+tail(mu_repeat, 21))*I(bins)
    q_chen = q_constant_cells-count_bad
    prediction_cap = weights[0]+370*sum(max(F(0), x) for x in weights[1:])
    chen_rows = []
    for budget in ('0.025','0.1','0.4'):
        predicted_passes = ceil(prediction_cap/F(budget))
        pstar = F(3600, predicted_passes)
        chosen = policy.Chen(training['weights'], fault_budget=budget, words=W, cut=4000).choose(pstar)
        sufficient_cap = F(budget)*floor(3600/P)
        chen_rows.append(dict(budget=budget, prediction_upper=enclosure(prediction_cap),
                              allowed_prediction_for_k27=str(sufficient_cap),
                              chosen_at_box_max=chosen, passes_upper=predicted_passes,
                              box_guarantees_k27=(chosen==27),
                              lower=enclosure(q_chen) if chosen==27 else None))

    # Existing generic T196 pair/aperture upper on common mandatory support.
    M1 = (b*T+FS)/Z
    M2 = (b*b*T+(B+b)*FS)/(Z*Z)
    lifetime = F(cfg['lifetime_other_budget'])
    def upper(k):
        pk = (k*W*196*xp+J)/NS
        return lifetime+W*comb(n,2)*(pk*M2+2*rB*Es*M1)
    upper27, upper1 = upper(27), upper(1)

    # One-word visits are P-periodic; maximum gaps between decision masks
    # stay bounded even while k changes, since every k divides27.
    alpha_max = 2*W*F('0.01')*P/F(315576000)
    assert alpha_max < 2
    checks = 0
    for ms in ('0.001','0.01'):
        for k in (1,3,9,27):
            for m in (*range(40), 10**6):
                for target in (F(1),F(3,2)):
                    core = policy.Krasnikov(Ms=ms, zero='longest', words=W)
                    core.k=core.modes[0]=k
                    core.count, core.target = m, target
                    old_period=core.period
                    core.advance(old_period)
                    if m:
                        assert core.k <= k
                        if k==27 and m>=2 and m!=target: assert core.k <= 9
                    else:
                        assert core.k==27
                    if core.k!=27:
                        core.advance(core.anchor+core.period)
                        assert core.k==27
                    checks += 1
    # Frozen hour prediction at the exact worst corner of the nonnegative box.
    box = [370 if x>0 else 0 for x in weights[1:]]
    for row in chen_rows:
        core=policy.Chen(training['weights'], fault_budget=row['budget'], words=W, cut=4000)
        core.bins=dict(enumerate(box));core.hour=6
        core.wake(policy.next_cut(6*policy.HOUR,4000))
        assert core.k==row['chosen_at_box_max']

    app=cfg['application'];H=int(T*NS)
    nr=arrivals(app['first_ns']+app['read_offset_ns'],app['epoch_ns'],H)
    nw=arrivals(app['first_ns']+app['write_offset_ns'],app['epoch_ns'],H)
    Nlow=max(F(0),W*(F(H)/(27*W*196*xp+J)-2))
    Nhigh=W*(F(H)/(W*196*xm-J)+2)
    core_low=(Nlow*(68*xm-J)+nr*(68*xm-J)+nw*(144*xm-J)+W*(76*xm-J))/H
    core_high=(Nhigh*E+nr*(68*xp+J)+nw*AW+W*(76*xp+J))/H

    return {
        'status':'COMPUTED_NOT_INDEPENDENT_REVIEW', 'base_commit':'3e7a04e74bad4ab51a4e25e21a031ac63054f94d',
        'frozen_blobs':PINS,
        'environment':dict(background_ref=str(b),peak_ref=str(B),solar_cap=str(FS),
            rise_s=str(ramp),rise_rate=enclosure(rise_rate),growth_cap=str(rho),
            plateau_start_s=str(peak_start),plateau_s=str(L),
            solar_mass_upper=str(solar_upper),solar_slack=str(FS-solar_upper),array_peak=str(lam)),
        'geometry':dict(P1_s=str(P1),P27_s=str(P),E_upper_s=str(Es),app_period_s=str(Rapp),
            guard_s=str(guard),cell_s=str(length),dropped_per_word=dropped,
            chen_cells_per_word=K_chen,krasnikov_cells_per_word=K_kras,birth_to_processed_s=str(tau)),
        'generic_upper':dict(k27=enclosure(upper27),k1=enclosure(upper1),epsilon=str(cfg['epsilon']),
                             k27_excess=enclosure(upper27-F(cfg['epsilon']))),
        'krasnikov_longest':dict(Ms=['0.001','0.01'],mean_witnesses=enclosure(mean_kras),
            second_factorial_correction=enclosure(mu_raw_kras*mu_raw_kras/2),Q_lower=enclosure(q_kras),
            lower_minus_epsilon=enclosure(q_kras-I(F(cfg['epsilon']))),state_checks=checks),
        'chen':dict(hour_bins=bins,parents_hour_mean_upper=enclosure(mu_hour),
            repeat_hour_mean_upper=enclosure(mu_repeat),count_bad_upper=enclosure(count_bad),
            fixed_cells_Q_lower=enclosure(q_constant_cells),rows=chen_rows),
        'patent':patent_rows,
        'cost':dict(application_reads=nr,application_writes=nw,
            all_rows_memory_core_lower=enclosure(core_low),all_rows_memory_core_upper=enclosure(core_high),
            cuts_upper=ceil(T*NS/4000)+1,chen_updates_upper=ceil(T/F(3600))+1,
            krasnikov_updates_upper=ceil(T/P1)+2,patent_update_formula='<=2*N_ERR+1 in the no-loss witness; add recovery/timer work for full quota class',
            CPU_energy_controller_unknown=True,post_A_work_included=True,full_price_is_not_core=True),
        'physical_guarantee_claimed':False,'transport_implemented':False,'Monte_Carlo':False,
    }


if __name__=='__main__':
    result=main()
    if '--check' in sys.argv:
        expected=json.loads((HERE/'result.json').read_text())
        assert result==expected, 'committed output mismatch'
        print('PASS: exact output and frozen-policy semantic checks')
    else:
        print(json.dumps(result,ensure_ascii=False,indent=2))
