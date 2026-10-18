"""T187: fixed-calendar first-exceedance bounds and certified small-model Q.

No MC, physical qualification, or optimization of an adaptive policy.
Positive-series enclosure follows accepted T166/T177, without editing them.
"""
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations
from math import comb, factorial


def falling(n, r):
    out = 1
    for j in range(r):
        out *= n-j
    return out


def dec(x, places=36, upper=False):
    q, r = divmod(x.numerator * 10**places, x.denominator)
    q += int(upper and r != 0)
    if not places:
        return str(q)
    sign = "-" if q < 0 else ""
    digits = str(abs(q)).zfill(places+1)
    return sign + digits[:-places] + "." + digits[-places:]


def interval(lo, hi, places=36):
    assert 0 <= lo <= hi <= 1
    return {"lower": dec(lo, places), "upper": dec(hi, places, True)}


def rounded(lo, hi, places=48):
    return F(dec(max(F(0), lo), places)), F(dec(min(F(1), hi), places, True))


def imul(a, b, places=48):
    return rounded(a[0]*b[0], a[1]*b[1], places)


@lru_cache(None)
def exp_bounds(x, terms=32):
    if x < 0 or terms < 2 or x >= terms+2:
        raise ValueError("positive-series geometric ratio must be <1")
    weight = total = F(1)
    for i in range(1, terms+1):
        weight *= x/i
        total += weight
    tail = (weight*x/(terms+1))/(1-x/F(terms+2))
    return 1/(total+tail), 1/total, tail


def phi(n, t, m1, m2=F(0)):
    """Expected union-witness count. For t=1 size2 is paid as direct."""
    if t == 1:
        if m2:
            raise ValueError("size2 belongs to the separate t=1 direct budget")
        return F(n-1, 2*n)*m1*m1
    if t != 2 or n < 3:
        raise ValueError("this compound-mark bound is for t=2, n>=3")
    return (F((n-1)*(n-2), 6*n*n)*m1**3
            + F(n-2, n)*m1*m2
            + (1-F(1, comb(n, 2)))*m2*m2/2)


def cross_phi(n, t, j, h):
    return phi(n, t, j[0]+h[0], j[1]+h[1])-phi(n, t, *j)-phi(n, t, *h)


def exposure(case, a, b, group=1):
    # Rates are per word, per parent group, not per corrected bit or ERR.
    return sum((max(F(0), min(b, y)-max(a, x))*rates[group-1]
                for x, y, rates in case["segments"]), F(0))


def validate(case):
    if not (case["W"]>=1 and 1<=case["t"]<case["n"] and case["T"]>0
            and case["P"]>0 and 0<=case["D"]<=case["P"]/case["W"]):
        raise ValueError("invalid code/calendar or overlapping reserved operations")
    cursor = F(0)
    for a,b,rates in case["segments"]:
        if a!=cursor or b<=a or b>case["T"] or len(rates)!=2 or min(rates)<0:
            raise ValueError("segments must partition [0,T] with nonnegative rates")
        cursor = b
    if cursor!=case["T"]:
        raise ValueError("profile does not cover the whole horizon")


def schedule(case, word):
    r = F(word, case["W"])*case["P"]
    while r <= case["T"]:
        yield r, r+case["D"]
        r += case["P"]


def cells(case, word, kind):
    points = {F(0), case["T"]}
    for r, f in schedule(case, word):
        value = f if kind == "U" else r
        if 0 < value < case["T"]:
            points.add(value)
    values = sorted(points)
    return list(zip(values, values[1:]))


def fixed_upper(case, kind="U"):
    validate(case)
    if kind not in ("U","E"):
        raise ValueError("unknown service")
    v = x = F(0)
    for w in range(case["W"]):
        for a, b in cells(case, w, kind):
            v += phi(case["n"], case["t"], exposure(case,a,b,1), exposure(case,a,b,2))
        if kind == "E":
            for r, f in schedule(case, w):
                j = tuple(exposure(case, max(F(0),r-case["P"]), r, g) for g in (1,2))
                h = tuple(exposure(case, r, min(f,case["T"]), g) for g in (1,2))
                x += cross_phi(case["n"], case["t"], j, h)
    return min(F(1), v+x), v, x


def lower(case, terms=32, places=48):
    """T45-type no-service cells, only independent uniform singleton streams."""
    validate(case)
    if any(r[1] for _,_,r in case["segments"]):
        raise ValueError("compound mixture lower needs its own no-other-parent factor")
    survival = (F(1), F(1))
    factor = F(falling(case["n"],case["t"]+1),
               factorial(case["t"]+1)*case["n"]**(case["t"]+1))
    for w in range(case["W"]):
        cursor = F(0)
        outside = []
        for r, f in schedule(case, w):
            if cursor < r:
                outside.append((cursor,r))
            cursor = min(case["T"], max(cursor,f))
        if cursor < case["T"]:
            outside.append((cursor,case["T"]))
        for a,b in outside:
            for u,v,rates in case["segments"]:
                ell = max(F(0),min(b,v)-max(a,u))
                if not ell:
                    continue
                m = ell*rates[0]
                el,eh,_ = exp_bounds(m,terms)
                pref = factor*m**(case["t"]+1)
                survival = imul(survival,(1-pref*eh,1-pref*el),places)
    return 1-survival[1],1-survival[0]


def hit_kernel(n, t, fraction_double=F(0)):
    """Exact lumping of uniform size1/size2 XOR marks by Hamming weight."""
    size = t+2
    rows = []
    for j in range(t+1):
        row = [F(0)]*size
        for ell, mix in ((1,1-fraction_double),(2,fraction_double)):
            if not mix:
                continue
            for overlap in range(max(0,ell-(n-j)),min(j,ell)+1):
                prob = mix*F(comb(j,overlap)*comb(n-j,ell-overlap),comb(n,ell))
                after = j+ell-2*overlap
                row[after if after<=t else t+1] += prob
        assert sum(row)==1
        rows.append(tuple(row))
    rows.append(tuple([F(0)]*(t+1)+[F(1)]))
    return tuple(rows)


@lru_cache(None)
def transition(m1, m2, n, t, terms=32):
    m = m1+m2
    kernel = hit_kernel(n,t,m2/m if m else F(0))
    el,eh,tail = exp_bounds(m,terms)
    size = t+2
    result = []
    for start in range(size-1):
        vec = [F(i==start) for i in range(size)]
        accum = vec.copy()
        weight = F(1)
        for k in range(1,terms+1):
            vec = [sum((vec[i]*kernel[i][j] for i in range(size)),F(0)) for j in range(size)]
            assert sum(vec)==1
            weight *= m/k
            accum = [a+weight*v for a,v in zip(accum,vec)]
        row = tuple((el*a,min(F(1),eh*a+tail)) for a in accum)
        assert sum(a for a,b in row)<=1<=sum(b for a,b in row)
        result.append(row)
    result.append(tuple([(F(0),F(0))]*(size-1)+[(F(1),F(1))]))
    return tuple(result)


def clean_survival(m1,m2,n,t,terms=32):
    row = transition(m1,m2,n,t,terms)[0]
    return max(1-row[-1][1],sum(a for a,b in row[:-1])), min(1-row[-1][0],sum(b for a,b in row[:-1]))


def exact_u(case,terms=32,places=48):
    validate(case)
    # Product of independent clean-reset cells. No future adaptive conditioning.
    live = (F(1),F(1))
    for w in range(case["W"]):
        for a,b in cells(case,w,"U"):
            # Main example is singleton: one generator, so rates commute.
            if any(r[1] for _,_,r in case["segments"]):
                raise ValueError("use state propagation for time-varying compound mixtures")
            live = imul(live,clean_survival(exposure(case,a,b),F(0),case["n"],case["t"],terms),places)
    return 1-live[1],1-live[0]


def exact_e(case,terms=32,places=48):
    validate(case)
    # Atomic full-image E at release iff ERR latched at begin. No hidden reset.
    t = case["t"]
    stride, absorb = t+1, 2*(t+1)
    size = absorb+1
    live = (F(1),F(1))
    for w in range(case["W"]):
        points = {F(0):[],case["T"]:[]}
        for a,b,_ in case["segments"]:
            points.setdefault(a,[]); points.setdefault(b,[])
        for r,f in schedule(case,w):
            points.setdefault(r,[]).append("read")
            if f<=case["T"]:
                points.setdefault(f,[]).append("release")
        vec = [(F(1),F(1))]+[(F(0),F(0))]*absorb
        previous = F(0)
        for when,actions in sorted(points.items()):
            kernel = transition(exposure(case,previous,when,1),exposure(case,previous,when,2),case["n"],t,terms)
            out = [(F(0),F(0)) for _ in range(size)]
            for i,(a,b) in enumerate(vec):
                if i==absorb:
                    out[i] = (out[i][0]+a,out[i][1]+b)
                    continue
                pending,weight = divmod(i,stride)
                for j,(lo,hi) in enumerate(kernel[weight]):
                    dest = absorb if j==t+1 else pending*stride+j
                    out[dest] = (out[dest][0]+a*lo,out[dest][1]+b*hi)
            vec = [rounded(a,b,places) for a,b in out]
            for action in actions:
                out = [(F(0),F(0)) for _ in range(size)]
                for i,(a,b) in enumerate(vec):
                    if i==absorb:
                        dest = absorb
                    else:
                        pending,weight = divmod(i,stride)
                        dest = (int(weight>0)*stride+weight if action=="read"
                                else (0 if pending else weight))
                    out[dest] = (out[dest][0]+a,out[dest][1]+b)
                vec = [rounded(a,b,places) for a,b in out]
            assert all(0<=a<=b<=1 for a,b in vec)
            assert sum(a for a,b in vec)<=1<=sum(b for a,b in vec)
            previous = when
        qlo = max(vec[absorb][0],1-sum(b for a,b in vec[:absorb]))
        qhi = min(vec[absorb][1],1-sum(a for a,b in vec[:absorb]))
        live = imul(live,(1-qhi,1-qlo),places)
    return 1-live[1],1-live[0]


def price_u(case, service=None):
    c = case["D"] if service is None else service
    if not 0<=c<=case["P"]/case["W"]:
        raise ValueError("bus operations do not fit the declared calendar")
    return sum((max(F(0),min(c,case["T"]-r))
                for w in range(case["W"]) for r,_ in schedule(case,w)),F(0))/case["T"]


def gf_mul(a,b):
    result = 0
    while b:
        if b&1:
            result ^= a
        b >>= 1
        a <<= 1
        if a&64:
            a ^= 0x43
    return result


def gf_pow(a,p):
    result = 1
    for _ in range(p):
        result = gf_mul(result,a)
    return result


def columns(t):
    if t==1:
        return tuple(64|x for x in range(39))
    if t==2:
        return tuple(gf_pow(2,j)|(gf_pow(2,3*j)<<6) for j in range(44))
    raise ValueError(t)


def rank(cols):
    pivots = {}
    for x in cols:
        while x:
            lead = x.bit_length()-1
            if lead not in pivots:
                pivots[lead] = x
                break
            x ^= pivots[lead]
    return len(pivots)


def code_check(t):
    cols = columns(t)
    seen = {0:()}
    for size in range(1,t+1):
        for inds in combinations(range(len(cols)),size):
            syndrome = 0
            for i in inds:
                syndrome ^= cols[i]
            if syndrome in seen:
                raise ArithmeticError(("ambiguous correctable syndrome",seen[syndrome],inds))
            seen[syndrome] = inds
    if t==2:
        assert {gf_pow(2,j) for j in range(63)}==set(range(1,64))
        assert gf_pow(2,63)==1
        assert rank(cols[:12])==12
    return {"n":len(cols),"rank":rank(cols),"k":len(cols)-rank(cols),
            "t":t,"distinct_correctable_syndromes":len(seen),"columns":list(cols)}
