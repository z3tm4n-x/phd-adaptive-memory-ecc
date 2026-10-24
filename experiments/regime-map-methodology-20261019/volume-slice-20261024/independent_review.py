"""Reviewer arithmetic from the declared formulas; no production-code imports."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from math import comb, gcd
from pathlib import Path
import json
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[3]
PACKAGE = ROOT / 'experiments/regime-map-methodology-20261019/volume-slice-20261024'
cfg = json.loads((ROOT / 'experiments/t186-method-comparison/code-strength/common-input.json').read_text('utf-8'))
result = json.loads((PACKAGE / 'outputs/result.json').read_text('utf-8'))
e, s, a, cal = (cfg[k] for k in ('environment', 'service', 'adaptive', 'calendar'))
T, eps, delta, NS = F(cfg['mission_s']), F(cfg['epsilon']), F(cfg['lifetime_other_budget']), 10**9
xm, xp, J = (F(s[k]) for k in ('clock_lower', 'clock_upper', 'operation_endpoint_span_ns'))
den = e['reference_words'] * e['reference_bits']
b, B, FS = (F(e[k])/den for k in ('reference_background_per_s', 'reference_peak_per_s', 'reference_solar_mass'))
M1 = min(B*T, b*T+FS)
M2 = min(B*B*T, B*M1, b*b*T+(B+b)*FS)
d = ((3*s['read_beat_ns']+s['decode39_ns']+3*s['write_beat_ns']+s['turnaround_ns'])*xp+J)/NS
Rplus, Rminus = 3*s['read_beat_ns']*xp+J, 3*s['read_beat_ns']*xm-J
Wplus = (3*s['write_beat_ns']+s['turnaround_ns'])*xp+J
ceil = lambda x: -(-x.numerator//x.denominator)
S = lambda t: 2+ceil((F(t)*NS+J)/(cal['c_ticks']*xm))
dec = lambda x: Decimal(x.numerator)/Decimal(x.denominator)

def read_bound(W, k, upper):
    P = k*W*cal['g_ticks']*(xm if upper else xp)+(-J if upper else J)
    return W*(T*NS/P+(2 if upper else -2))

out = []
for row in result['rows']:
    W = row['words']; kf = row['fixed']['k']
    cross = 2*W*comb(39,2)*B*d*M1
    k_limit = (eps-delta-cross-W*comb(39,2)*J/NS*M2)/(W*W*comb(39,2)*cal['g_ticks']*xp/NS*M2)
    assert kf == k_limit.numerator//k_limit.denominator
    q_fixed = delta+W*comb(39,2)*(kf*W*cal['g_ticks']*xp+J)/NS*M2+cross
    assert q_fixed == F(row['fixed']['risk']['upper'])
    threshold = row['fixed_class']; P0 = F(threshold['P0'])
    L = FS/(B-b)-(W*cal['g_ticks']*xp+J)/NS
    lam = 39*B
    def lower_Q(period):
        windows = L/period+2
        free = L-windows*(d+2*J/NS)
        assert free > 0
        sq = free*free/(windows+1)
        with localcontext() as context:
            context.prec = 100
            Z = dec(W*F(38,39)*lam*lam*sq/2)*(-dec(lam*L)).exp()
            return 1-(-Z).exp()-dec(delta)
    assert lower_Q(P0)>dec(eps) and lower_Q(P0-F(1,10**6))<=dec(eps)
    fixed_lower = Rminus*W*(1/(P0+J/NS)-2/T)/NS
    assert fixed_lower == F(threshold['pure_bus_class_lower_if_reviewed'])
    hard = read_bound(W, 1, True)
    gate_terms = {
        'background':S(a['short_hold_s'])*39*W*b*T,
        'solar':S(a['long_hold_s'])*39*W*FS,
        'false':S(a['long_hold_s'])*F(a['ordinary_false_expected_per_s'])*T,
        'recovery':(a['recoveries_upper']+1)*S(a['long_hold_s']),
        'loss':F(a['ordinary_outage_fraction'])*T*NS/(cal['c_ticks']*xm)+2*a['ordinary_loss_episodes_upper'],
        'bad':delta*hard,
    }
    for key, value in gate_terms.items():
        assert value == F(row['price_gate']['terms'][key])
    floor = Rplus*min(hard,sum(gate_terms.values()))/(T*NS)
    assert floor == F(row['price_gate']['certificate_bus_floor'])
    assert row['price_gate']['activated'] == (fixed_lower<=floor)
    for trial in row['adaptive_rows']:
        k, q = trial['k'], F(trial['Q_upper']); price=trial['price']
        assert gcd(k,W)==1
        if trial.get('certificate','').startswith('accepted mandatory-only'):
            expected = delta+W*comb(39,2)*(k*W*cal['g_ticks']*xp+J)/NS*M2+cross
            assert q == expected
        count_terms = sum(F(v) for v in price['read_count_terms'].values())
        # Confirm the selected new hold expression rather than trusting its stored total.
        N = min(hard, count_terms)
        assert N == F(price['reads_upper'])
        repairs = min(N, 2*39*W*M1+q*hard)
        assert repairs == F(price['repairs_upper'])
        bus = (Rplus*N+Wplus*repairs)/(T*NS)
        assert bus == F(price['pure_bus_upper'])
        assert Rminus*read_bound(W,k,False)/(T*NS) == F(price['pure_bus_lower'])
    chosen = next(t for t in row['adaptive_rows'] if t['k']==row['selected_k'])
    assert fixed_lower-F(chosen['price']['pure_bus_upper']) == F(row['comparison']['control_bus_sufficient_strict_below'])
    assert row['whole_reference_memory_Q'] is None
    out.append({'KiB':row['kib'], 'fixed_k':kf, 'fixed_period_limit_s':float(P0),
                'price_certificate_floor_pp':float(100*floor),
                'floor_components_pp':{k:float(100*Rplus*v/(T*NS)) for k,v in gate_terms.items()},
                'class_lower_over_floor':float(fixed_lower/floor),
                'fixed_witness_upper_over_floor':float(F(row['comparison']['fixed_witness_bus_upper'])/floor)})

for file in sorted((PACKAGE/'outputs').glob('certificate-256KiB-k*.json')):
    c=json.loads(file.read_text('utf-8')); p=c['environment']; cc=c['calendar']; m=c['majorant']; W=p['W']; k=c['k']
    factor=F(39*W,den)
    for key, ref in [('b','reference_background_per_s'),('B','reference_peak_per_s'),('FS','reference_solar_mass'),('ell','reference_growth_threshold_per_s')]:
        assert F(p[key])==factor*F(e[ref])
    assert F(p['S2'])==(39*W)**2*M2
    ps, pl = F(cc['Ps_min']), F(cc['Pl'])
    assert F(cc['Ps'])==W*cal['g_ticks']*xp/NS
    assert pl==k*W*cal['g_ticks']*xp/NS
    beta=F(1,2*W); eta=2*beta/W
    cross1=beta*(k*d+pl/W)*F(p['S2'])
    v=2*beta*d*(T/ps+1)
    cross2=min(F(p['B'])*pl,F(p['F']))*min(F(p['B'])*v,F(p['b'])*v+eta*F(p['FS']),eta*F(p['F']))
    integral=min(pl*F(p['S2']),F(m['u'])*T+F(m['v'])*F(p['FS']))
    assert integral==F(m['integral'])
    assert min(F(1),delta+beta*integral+min(cross1,cross2))==F(c['risk']['upper'])
    previous=F(p['b'])
    for cell in m['cells']:
        lo,hi,K=(F(cell[x]) for x in ('lo','hi','K_upper'))
        assert previous==lo and lo<hi and 0<=K<=pl
        assert all(F(m['u'])+F(m['v'])*(x-F(p['b']))>=K*x*x for x in (lo,hi))
        previous=hi
    assert previous==F(p['B'])

print(json.dumps({'arithmetic':'matched without production imports','rows':out},indent=2))
