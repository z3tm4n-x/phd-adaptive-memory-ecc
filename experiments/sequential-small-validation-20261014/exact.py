"""T166 finite absorbing model; all certified endpoints use Fraction arithmetic."""
from fractions import Fraction as F
from functools import lru_cache
import math

def cases(cfg):
    rows = []
    for W in cfg["W"]:
        for profile, segments in cfg["profiles"].items():
            for gap in cfg["read_to_fence_s"]:
                rows.append(dict(index=len(rows), id=f"W{W}_{profile}_D{gap.replace('/', '-')}",
                    W=W, n=cfg["n"], T=F(cfg["T_s"]), period=F(cfg["period_s"]), D=F(gap),
                    profile=profile, segments=[(F(s["start"]), F(s["end"]),
                    F(s["lambda_array_s_inv"])) for s in segments]))
    return rows

def exposure(case, start, end):
    return sum((max(F(0), min(end, b)-max(start, a))*rate
                for a,b,rate in case["segments"]), F(0))

def word_schedule(case, word):
    r = F(word, case["W"])*case["period"]
    result = []
    while r <= case["T"]:
        result.append((r, r+case["D"]))
        r += case["period"]
    return result

def fence_intervals(case, word):
    boundaries = sorted({F(0), case["T"]} |
        {f for _,f in word_schedule(case, word) if 0 < f < case["T"]})
    return list(zip(boundaries[:-1], boundaries[1:]))

def lower_cells(case, word):
    # T45 safe cells: previous possible fence -> next latch, then split rates.
    outside = []
    cursor = F(0)
    for read, fence in word_schedule(case, word):
        if cursor < read:
            outside.append((cursor, min(read, case["T"])))
        cursor = min(case["T"], max(cursor, fence))
    if cursor < case["T"]:
        outside.append((cursor, case["T"]))
    return [(max(a,c), min(b,d), rate) for a,b in outside
            for c,d,rate in case["segments"] if max(a,c) < min(b,d)]

@lru_cache(maxsize=None)
def exponential_enclosure(x, terms):
    """e^-x in [1/(S+R),1/S]; R bounds tail of positive e^x series."""
    if x < 0 or terms < 2 or x >= terms+2:
        raise ValueError("positive-series tail ratio must be below one")
    term = total = F(1)
    for k in range(1, terms+1):
        term *= x/k
        total += term
    next_term = term*x/(terms+1)
    tail = next_term/(1-x/F(terms+2))
    return 1/(total+tail), 1/total, tail

@lru_cache(maxsize=None)
def local_transition(mass, n, terms):
    """0/1/A CTMC via exact rational uniformization and an explicit tail."""
    exp_lo, exp_hi, tail = exponential_enclosure(mass, terms)
    v = (F(1), F(0), F(0))
    accum = [F(1), F(0), F(0)]
    weight = F(1)
    for k in range(1, terms+1):
        v = (v[1]/n, v[0], v[2] + v[1]*F(n-1,n))
        if sum(v) != 1:
            raise ArithmeticError("uniformization kernel loses mass")
        weight *= mass/k
        for i in range(3):
            accum[i] += weight*v[i]
    components = [(exp_lo*x, min(F(1), exp_hi*x+tail)) for x in accum]
    if not sum(x[0] for x in components) <= 1 <= sum(x[1] for x in components):
        raise ArithmeticError("component enclosures do not contain unit mass")
    live = accum[0]+accum[1]
    survival = (exp_lo*live, min(F(1), exp_hi*live+tail))
    return survival, tuple(components), tail

def fixed_decimal(x, places, upper=False):
    scale = 10**places
    q,r = divmod(x.numerator*scale, x.denominator)
    if upper and r:
        q += 1
    sign = "-" if q < 0 else ""
    digits = str(abs(q)).zfill(places+1)
    return sign + digits[:-places] + "." + digits[-places:] if places else str(q)

def enclosure(lo, hi, places=36):
    if not lo <= hi:
        raise ArithmeticError("reversed enclosure")
    a, b = fixed_decimal(lo, places), fixed_decimal(hi, places, True)
    midpoint = (F(a)+F(b))/2
    radius = (F(b)-F(a))/2
    return dict(lower=a, upper=b, midpoint=fixed_decimal(midpoint,places+1),
                absolute_error=fixed_decimal(radius,places+1))

def solve(case, terms=32, places=36):
    live_lo = live_hi = F(1)
    no_lower_event_lo = no_lower_event_hi = F(1)
    square = F(0)
    max_tail = F(0)
    audits = []
    for word in range(case["W"]):
        intervals = fence_intervals(case, word)
        masses = [exposure(case,a,b)/case["W"] for a,b in intervals]
        for mass in masses:
            survival, _, tail = local_transition(mass,case["n"],terms)
            live_lo *= survival[0]
            live_hi *= survival[1]
            square += mass*mass
            max_tail = max(max_tail,tail)
        cells = lower_cells(case,word)
        for a,b,rate in cells:
            mass = rate*(b-a)/case["W"]
            e_lo,e_hi,_ = exponential_enclosure(mass,terms)
            factor = F(case["n"]-1,2*case["n"])*mass*mass
            p_lo,p_hi = factor*e_lo, factor*e_hi
            if not 0 <= p_lo <= p_hi <= 1:
                raise ArithmeticError("invalid cell probability enclosure")
            no_lower_event_lo *= 1-p_hi
            no_lower_event_hi *= 1-p_lo
        audits.append(dict(word=word,
            read_fence=[dict(read=str(r),fence=str(f),executed=f<=case["T"])
                        for r,f in word_schedule(case,word)],
            upper_intervals=[dict(start=str(a),end=str(b),word_exposure=str(m))
                             for (a,b),m in zip(intervals,masses)],
            lower_cells=[dict(start=str(a),end=str(b),array_rate=str(rate))
                         for a,b,rate in cells]))
    q_lo,q_hi = 1-live_hi,1-live_lo
    L_lo,L_hi = 1-no_lower_event_hi,1-no_lower_event_lo
    U = min(F(1),F(case["n"]-1,2*case["n"])*square)
    token = min(F(1),square/2)
    F_total = exposure(case,F(0),case["T"])
    coarse = min(F(1),F_total**2/(2*case["W"]))
    if not L_hi <= q_lo <= q_hi <= U <= token <= coarse:
        raise ArithmeticError("certified comparison fails; retain this case and localize")
    return dict(Q_exact=enclosure(q_lo,q_hi,places), L=enclosure(L_lo,L_hi,places),
        U=enclosure(U,U,places), U_token=enclosure(token,token,places),
        U_coarse=enclosure(coarse,coarse,places), U_rational=str(U),
        F_array=str(F_total), full_state_count=2**case["W"]+1,
        uniformization_terms=terms, max_local_unscaled_tail_rational=str(max_tail),
        mass_check="all exact stochastic kernel sums=1; component intervals contain1",
        comparison="L.upper <= Q.lower <= Q.upper <= U.exact",
        phase_audit=audits)

def analytic_survival(mass, n):
    """Independent closed form for spot checks (ordinary floating point)."""
    x = float(mass)
    root = math.sqrt(n)
    return math.exp(-x)*(math.cosh(x/root)+root*math.sinh(x/root))
