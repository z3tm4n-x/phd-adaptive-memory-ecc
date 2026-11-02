"""Independent rational check of PR371; no imports of author calculators."""
import json
from fractions import Fraction as F
from hashlib import sha256
from math import factorial
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[3]
read = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8'))
new = read('theory/observation-carry-refinement-20261101/result.json')
a = new['application']
old = read('theory/observation-volume-20261101/result.json')['banks'][1]['rows'][1]
env = read('experiments/regime-map-methodology-20261019/predictability-volume-20261028/inputs.json')['environment']
res = next(x for x in read('experiments/regime-map-methodology-20261019/predictability-volume-20261028/resource-result.json')['rows'] if x['words'] == 1048576)

def ceil(x):
    return -(-x.numerator // x.denominator)

def exp_minus_bounds(x, odd=201):
    assert x >= 0 and odd % 2 == 1
    term = total = F(1)
    for k in range(1, odd + 1):
        term *= -x / k
        total += term
    return total, total + term * (-x) / (odd + 1)

def log_unit_bounds(x, count=130):
    assert 1 <= x <= 2
    z = (x - 1) / (x + 1)
    total = sum((2 * z**(2*j + 1) / (2*j + 1) for j in range(count)), F(0))
    return total, total + 2*z**(2*count+1)/((2*count+1)*(1-z*z))

def log_bounds(x):
    k = 0
    while x > 2:
        x /= 2
        k += 1
    lo, hi = log_unit_bounds(x)
    l2, h2 = log_unit_bounds(F(2))
    return lo + k*l2, hi + k*h2

W, T, K, m, threshold = 1048576, F(315576000), 3001, 6, 32
eps, d0, dc, alpha = F('.01'), F('.000006'), F('.00005'), F('.0005')
xp, xm, jitter = F('1.00001'), F('.99999'), F('0.0000000005')
scale = F(39*W, env['reference_positions'])
b, B = scale*F(env['b']), scale*F(env['B'])
ap = scale*F(env['Fs']) / (58440*600)
R, g, Fr = B-b-ap, scale*F(env['rho'])*F(env['ell'])-ap/300, scale*F(env['Fs'])/2
mass, ip = b*T+2*Fr, b*b*T+2*b*Fr+2*ap*Fr/3
block = F(1568*(W//8+7), 10**9)
hlo, hhi = K*block*xm, K*block*xp
Pobs = F(ceil((block*xp+jitter)*10**6), 10**6)
Llo, Lhi = m*hlo-2*jitter, m*hhi+2*jitter
N, Nfull = ceil(T/hlo), int((T-block*xp-jitter)/hhi)
dE = F(124,10**9)*xp+3*jitter
kb, ks, u = 6, 11, F('.203580698573')
ab, ar = max(2*Pobs,kb*block*xp+jitter), max(2*Pobs,ks*block*xp+jitter)
U = u+g*hhi
assert ar*U <= ab*R and U < R
passes = lambda k: 1+ceil(F(K-2,k))
nb, nr = passes(kb), passes(ks)
assert (nb,nr) == (501,274) and (K-2)%kb != 1 and (K-2)%ks != 1
def exposure(v):
    cone=max(F(0),v-2*g*jitter)
    tail=max(F(0),cone-g*Llo)
    return b*Llo+(cone*cone-tail*tail)/(2*g)-(b+v)*m*nb*Pobs
loglo, loghi=log_bounds(F(N)/alpha)
assert F(a['log_threshold_upper']) >= loghi
score=F('.8646')*exposure(u)-2*threshold
assert F('.8646') < 1-exp_minus_bounds(F(2))[1]
assert score > loghi+F(1,10**6)
assert F('.8646')*exposure(u-F(1,10**12))-2*threshold <= loglo+F(1,10**6)
pair=(ar*ip+(2*ar*(b+ap)+max(ab*R,ar*U))*Fr)/(2*W)
aperture=B*dE*mass/W
q0=alpha+pair+aperture
q=d0+dc+q0
assert q==F(a['Q_upper']) and q < eps
assert aperture==F(a['aperture_pair_upper']) and q0==F(a['q0_for_break_observation_and_cost'])
assert q <= F('.009315980541') and eps-q >= F('.000684019459')

# Independent rational enclosures of the two transcendental coefficients.
mu=b*(Lhi+Pobs)+300*ap
assert 600 < Lhi+Pobs < 5400 and mu==F(a['history_parent_mu_p_upper'])
tail_hi=1-exp_minus_bounds(mu)[0]*sum((mu**j/factorial(j) for j in range(17)),F(0))
lip_hi=exp_minus_bounds(F(16))[1]*F(16**16,factorial(16))
tail,lip=F(a['parent_tail_upper']),F(a['parent_tail_lipschitz'])
assert tail>=tail_hi and lip>=lip_hi
D0=N*tail+lip*(m+1)*Fr+F('.0001')*T/hlo+(m+1)*(1001+F('.000001')*T)+N*q0
assert D0==F(a['D0_upper'])
rare=max(F(0),Nfull-m-D0-N*(d0+dc))/N
assert rare==F(a['rare_fraction_lower_before_extra_z']) and rare>=F('.933096753468')
Mb=W*(1+N*nb)
M0=W*(1+N*nr+min(F(N),m+D0)*(nb-nr))
H0=min(F(Mb),2*mass+q0*Mb)
assert (Mb,M0,H0)==(a['main_reads_maximum'],F(a['main_reads_upper']),F(a['main_repairs_upper']))
hard=W*(ceil(T/(F(196*W,10**9)*xm-jitter))+2)
assert new['old_rival_bounds_used_verbatim']==old['rivals']
assert F(old['rivals']['constant_member']['Q_upper'])<eps
budgets={}
for coord,rt,wt,it,prefix in [('bus',48,56,56,'pure_bus'),('serial',68,56,76,'serial')]:
    read_cost=F(rt,10**9)*xp+jitter
    write_cost=F(wt,10**9)*xp+(jitter if coord=='bus' else 0)
    Cb=Mb*(read_cost+write_cost)/T
    Ch=hard*(read_cost+write_cost)/T
    V=(M0*read_cost+H0*write_cost)/T+d0*Ch+dc*Cb
    common=F(res['application'][prefix+'_mission_upper'])+W*(F(it,10**9)*xp+jitter)/T
    saved=a['costs'][coord]
    assert V==F(saved['V_at_deltaC_design']) and V+common==F(saved['with_common_upper'])
    assert W*N*(nb-nr)*read_cost/T==F(saved['A_z'])
    assert read_cost+write_cost==F(saved['A_G_rate']) and Ch-Cb==F(saved['C_escape'])
    budgets[coord]={}
    for kind in ('schedule','constant'):
        budget=F(old['rivals']['costs'][coord][kind]['with_common_lower'])-V-common
        assert budget==F(saved['strict_full_cost_budget'][kind]) and budget>0
        budgets[coord][kind]=float(budget*10**6)
for path, digest in new['sources_sha256_LF'].items():
    assert sha256((ROOT/path).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,path
print(json.dumps({'Q_upper_approx':float(q),'margin_approx':float(eps-q),'E3_log_margin_approx':float(score-loghi),
                  'rare_fraction_lower_approx':float(rare),'budgets_us_s_approx':budgets,
                  'sources_checked':len(new['sources_sha256_LF']),
                  'method':'exact rational algebra; independent Taylor/atanh bounds; no calculator imports'},indent=2))
print('PASS independent arithmetic and inherited provenance')
