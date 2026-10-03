"""T80 E.3: finite interval majorants for the NEW finite-exit ERR-only."""
from __future__ import annotations

from decimal import Decimal as D, Context, ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_EVEN
from fractions import Fraction as F
from functools import lru_cache

from t80_engine import FAMILY, errors, short_gate, t58

# Decimal exp/ln are correctly rounded to nearest. One adjacent value on
# either side encloses them. Algebra below uses explicitly directed contexts.
DOWN = Context(prec=48, rounding=ROUND_FLOOR)
UP = Context(prec=48, rounding=ROUND_CEILING)
NEAR = Context(prec=48, rounding=ROUND_HALF_EVEN)


class I:
    __slots__ = ('lo', 'hi')

    def __init__(self, x, hi=None):
        if hi is not None:
            self.lo, self.hi = x, hi
        elif isinstance(x, F):
            self.lo = DOWN.divide(D(x.numerator), D(x.denominator))
            self.hi = UP.divide(D(x.numerator), D(x.denominator))
        else:
            self.lo = self.hi = D(str(x))

    def __add__(self, b):
        b = b if isinstance(b, I) else I(b)
        return I(DOWN.add(self.lo, b.lo), UP.add(self.hi, b.hi))

    def __sub__(self, b):
        b = b if isinstance(b, I) else I(b)
        return I(DOWN.subtract(self.lo, b.hi), UP.subtract(self.hi, b.lo))

    def __mul__(self, b):
        b = b if isinstance(b, I) else I(b)
        return I(min(DOWN.multiply(a, c) for a in (self.lo, self.hi) for c in (b.lo, b.hi)),
                 max(UP.multiply(a, c) for a in (self.lo, self.hi) for c in (b.lo, b.hi)))

    def __truediv__(self, b):
        b = b if isinstance(b, I) else I(b)
        if b.lo <= 0 <= b.hi:
            raise ValueError('interval division by zero')
        return I(min(DOWN.divide(a, c) for a in (self.lo, self.hi) for c in (b.lo, b.hi)),
                 max(UP.divide(a, c) for a in (self.lo, self.hi) for c in (b.lo, b.hi)))

    def clip(self, lo, hi):
        return I(max(D(str(lo)), min(D(str(hi)), self.lo)), max(D(str(lo)), min(D(str(hi)), self.hi)))

    def exp(self):
        return I(NEAR.next_minus(NEAR.exp(self.lo)), NEAR.next_plus(NEAR.exp(self.hi)))

    def ln(self):
        return I(NEAR.next_minus(NEAR.ln(self.lo)), NEAR.next_plus(NEAR.ln(self.hi)))


def integral_A(x, t, rho=F('.048'), l=F('.001')):
    """Outward enclosure of the exact E.3 primitive A(x,t)."""
    if min(x, t, rho) < 0:
        raise ValueError('negative input')
    if not rho:
        return I(x*t)
    if x <= l:
        v = min(t, x/(rho*l))
        return I(x*v-rho*l*v*v/2)
    xi, ri, li, ti = map(I, (x, rho, l, t))
    te = (xi/li).ln()/ri
    v1 = I(min(ti.lo, te.lo), min(ti.hi, te.hi))
    v2 = (ti-te).clip(0, str((I(1)/ri).hi))
    # v2 <= 1/rho; independent interval algebra gives outward bounds.
    v2 = I(min(v2.lo, (I(1)/ri).lo), min(v2.hi, (I(1)/ri).hi))
    term1 = (xi/ri)*(I(1)-(I(0)-ri*v1).exp())
    term2 = li*(v2-ri*v2*v2/I(2))
    return term1+term2


def exposure(x, r0, r1):
    if r1 < r0:
        raise ValueError('h <= tau')
    # Directed subtraction, explicitly as in E.3.
    v = integral_A(x, r1)-integral_A(x, r0)
    return I(max(D(0), v.lo), max(D(0), v.hi))


def cell_upper(xlo, xhi, aE, r0, r1):
    il = exposure(xlo, r0, r1).lo
    bound = I(xhi*xhi)*(I(0)-I(aE)*I(il)).exp()
    return F(bound.hi)


@lru_cache(maxsize=5000)
def majorant(B, b, T, FS, S2, aE, r0, r1):
    """E1 on a finite partition; refine only cells active in u or v.

    Return the best of the four preregistered u multipliers. Refinement
    never assumes monotonic psi, only monotonic I and the affine RHS.
    """
    xs = sorted(set([F(0), b, F('.001'), B]+[B*i/1024 for i in range(1, 1024)]))
    cache = {}

    def ub(lo, hi):
        key = (lo, hi)
        if key not in cache:
            cache[key] = cell_upper(lo, hi, aE, r0, r1)
        return cache[key]

    min_width = B/65536
    for iteration in range(7):
        cells = [(lo, hi, ub(lo, hi)) for lo, hi in zip(xs[:-1], xs[1:])]
        base = max(v for lo, hi, v in cells if hi <= b)
        candidates, active = [], set()
        for mult in (1, 2, 4, 16):
            u = mult*base
            zero = [(lo, hi, v) for lo, hi, v in cells if lo <= b and v > u]
            if zero:
                active.update((lo, hi) for lo, hi, _ in zero)
                continue
            slopes = [(max(F(0), (v-u)/(lo-b)), lo, hi) for lo, hi, v in cells if lo > b]
            v, alo, ahi = max(slopes)
            active.add((alo, ahi))
            active.update((lo, hi) for lo, hi, val in cells if hi <= b and val == base)
            candidates.append(dict(u=u, v=v, Q=min(S2, u*T+v*FS), multiplier=mult,
                                   cells=len(cells), active_lo=alo, active_hi=ahi))
        if not candidates:
            chosen = None
        else:
            chosen = min(candidates, key=lambda r: (r['Q'], r['multiplier']))
        mids = [(lo+hi)/2 for lo, hi in active if hi-lo > min_width]
        if not mids or iteration == 6:
            if chosen is None:
                raise ValueError('No finite E1 majorant at declared resolution')
            chosen['evaluated_cells'] = len(cache)
            chosen['minimum_E1_slack'] = min(chosen['u']+chosen['v']*max(F(0), lo-b)-val for lo, hi, val in cells)
            assert chosen['minimum_E1_slack'] >= 0
            return chosen
        xs = sorted(set(xs+mids))
    raise AssertionError('finite refinement')


def err_price(p, ka, h, risk):
    Pl, T, b = ka*p['Ps'], p['T'], p['b']
    # h is the physical guaranteed minimum; budget rounds upwards once.
    ht = t58.ceil(h/p['tm'])
    hp = ht*p['tp']
    edge = p['dE']+2*p['Gp']+p['gap']+p['f']+4*p['gp']
    DE = (t58.floor((hp+edge)/p['tp'])+1)*p['tp']
    cf = p['cp']/p['gm']
    pq = min(F(1), errors(p['q'], 'ERR-only', False)+p['Dstar']+
             p['K']*b*p['Ps']/p['W']+p['beta0']*Pl*b*b*T)
    start = DE*(1+p['K'])/T
    flags = DE*(b+p['rF']+p['rloss'])
    quiet = cf/ka+cf*min(F(1), start+flags+pq)+(2*p['cp']+p['sigmaX'])/T+p['CX']
    TQ, KQ = F(9, 10)*T, 1000
    boundary = DE*(KQ+p['K']+KQ*p['B']*(Pl+p['dE']))/TQ
    returns = cf/ka+cf*min(F(1), boundary+flags+min(F(1), risk))+(2*p['cp']+p['sigmaX'])*KQ/TQ+p['CX']
    return dict(quiet_upper=quiet, returns_upper=returns, base_tax=cf/ka,
                quiet_start_component=cf*start, quiet_ERR_component=cf*flags,
                quiet_global_component=cf*pq, DE=DE,
                full_goal_pass=quiet<=F('.01') and returns<=F('.01'))


def err_scan(p):
    gate = short_gate(p, 'ERR-only')
    if not gate['short_pass']:
        return [dict(status='short_risk', **gate)], None
    aE, beta0 = F(p['W']-1, p['W']), p['beta0']
    e = errors(p['q'], 'ERR-only')+p['Dstar']+gate['initial_upper']
    best, rows = None, []
    # Cache common b/g cases across the three distinct T72 budget records.
    max_age = ((I(p['B'])/I('.001')).ln()+I(1))/I('.048')
    rejected_from = None
    for ka in range(1, 4096, 2):
        Pl = ka*p['Ps']
        tau = Pl+p['dE']
        r0 = tau+Pl+p['Gp']+p['f']
        mandatory = beta0*Pl*p['S2']
        # A lower bound on EVERY admissible E1 majorant, not a lower bound
        # on physical failure: uT+vFS >= psi(x)*min(T,FS/(x-b)).
        # Use h=infinity (finite inverse-cone support) for the most optimistic
        # Q. If even that expression fails, no h in the declared list helps.
        qlower = F(0)
        if rejected_from is None:
            for x in (p['b'], F('.001'), p['B']/8, p['B']/4, p['B']/2, p['B']):
                expo = exposure(x, r0, max(r0, F(max_age.hi))).hi
                psi_lo = F((I(x*x)*(I(0)-I(aE)*I(expo)).exp()).lo)
                mass = p['T'] if x<=p['b'] else min(p['T'], p['FS']/(x-p['b']))
                qlower = max(qlower, min(p['S2'], psi_lo*mass))
            optimistic = e+min(mandatory, gate['short_pairs_upper']+beta0*Pl*qlower)
            if optimistic > p['eps']:
                rejected_from = (ka, optimistic, qlower)
        if rejected_from is not None:
            rows.append(dict(ka=ka, status='all_h_E1_expression_lower_reject',
                             risk_formula_lower=rejected_from[1],
                             Q_lower=rejected_from[2], reject_from_ka=rejected_from[0],
                             h_scope='all ten declared h; r0 and Pl increase with ka'))
            continue
        for h in map(F, FAMILY['ERR_only']['h_s']):
            row = dict(ka=ka, h=h, tau=tau, beta0_short=gate['short_pairs_upper'],
                       aE=aE, r0=r0, mandatory_pairs=mandatory)
            if h <= tau:
                rows.append(dict(**row, status='h_le_tau'))
                continue
            r1 = h+Pl+p['Gp']+p['f']
            if r0 >= F(max_age.hi):
                # Entire inverse cone is zero even for x=B. Exact saturation.
                Q, maj = p['S2'], dict(u=None, v=None, cells=0)
            else:
                # A saturates beyond the largest inverse-cone support.
                # Reuse that exact same physical integral for longer h.
                r1 = min(r1, max(r0, F(max_age.hi)))
                maj = majorant(p['B'], p['b'], p['T'], p['FS'], p['S2'], aE, r0, r1)
                Q = maj['Q']
            pairs = min(mandatory, gate['short_pairs_upper']+beta0*Pl*Q)
            risk = e+pairs
            row.update(Q=Q, risk_upper=risk, risk_slack=p['eps']-risk,
                       cross_pairs=beta0*Pl*Q, u=maj['u'], v=maj['v'], cells=maj['cells'],
                       status='certified_conditional' if risk<=p['eps'] else 'ERR_pair_risk')
            if risk <= p['eps']:
                row.update(err_price(p, ka, h, risk))
                if best is None or (row['quiet_upper'], h, ka) < (best['quiet_upper'], best['h'], best['ka']):
                    best = row
            rows.append(row)
    return rows, best
