"""T177 finite E model: interval rational propagation, local pending, pair bounds."""
from fractions import Fraction as F
from functools import lru_cache
from arithmetic import exponential_enclosure, fixed_decimal, enclosure

def cases(cfg):
    out = []
    for W in cfg["W"]:
        for profile, segments in cfg["profiles"].items():
            for gap in cfg["read_to_fence_s"]:
                out.append(dict(index=len(out), id=f"W{W}_{profile}_D{gap.replace('/', '-')}",
                    W=W, n=cfg["n"], T=F(cfg["T_s"]), period=F(cfg["period_s"]), D=F(gap),
                    profile=profile, segments=[(F(s["start"]), F(s["end"]),
                    F(s["lambda_array_s_inv"])) for s in segments]))
    return out

def exposure(case, start, end):
    return sum((max(F(0), min(end,b)-max(start,a))*rate
                for a,b,rate in case["segments"]), F(0))

def schedule(case, word):
    begin = F(word,case["W"])*case["period"]
    result = []
    while begin <= case["T"]:
        result.append((begin,begin+case["D"]))
        begin += case["period"]
    return result

def lower_cells(case, word):
    outside, cursor = [], F(0)
    for begin,end in schedule(case,word):
        if cursor < begin:
            outside.append((cursor,begin))
        cursor = min(case["T"],max(cursor,end))
    if cursor < case["T"]:
        outside.append((cursor,case["T"]))
    return [(max(a,c),min(b,d),r) for a,b in outside
            for c,d,r in case["segments"] if max(a,c)<min(b,d)]

@lru_cache(maxsize=None)
def transition(mass,n,terms):
    """5-state row kernel: (clean,dirty)x(pending0,pending1), then absorbing A."""
    lo_exp,hi_exp,tail = exponential_enclosure(mass,terms)
    rows = []
    for initial in (0,1):
        v = [F(initial==0),F(initial==1),F(0)]
        accum = v.copy()
        weight = F(1)
        for k in range(1,terms+1):
            v = [v[1]/n,v[0],v[2]+v[1]*F(n-1,n)]
            if sum(v)!=1:
                raise ArithmeticError("arrival kernel loses mass")
            weight *= mass/k
            accum = [a+weight*b for a,b in zip(accum,v)]
        rows.append([(lo_exp*a,min(F(1),hi_exp*a+tail)) for a in accum])
    matrix = []
    for pending in (0,1):
        for dirty in (0,1):
            row = [(F(0),F(0))]*5
            row[2*pending],row[2*pending+1],row[4] = rows[dirty]
            matrix.append(tuple(row))
    matrix.append(tuple([(F(0),F(0))]*4+[(F(1),F(1))]))
    for row in matrix:
        if not sum(a for a,b in row)<=1<=sum(b for a,b in row):
            raise ArithmeticError("kernel mass enclosure fails")
    return tuple(matrix),tail

def round_interval(lo,hi,places):
    return F(fixed_decimal(max(F(0),lo),places)),F(fixed_decimal(min(F(1),hi),places,True))

def mass_check(vector):
    if not all(0<=a<=b<=1 for a,b in vector):
        raise ArithmeticError("invalid probability component")
    lo,hi = sum(a for a,b in vector),sum(b for a,b in vector)
    if not lo<=1<=hi:
        raise ArithmeticError("state mass enclosure excludes one")
    return hi-lo

def propagate(vector,mass,n,terms,places):
    kernel,tail = transition(mass,n,terms)
    result = [round_interval(sum(vector[i][0]*kernel[i][j][0] for i in range(5)),
                             sum(vector[i][1]*kernel[i][j][1] for i in range(5)),places)
              for j in range(5)]
    mass_check(result)
    return result,tail

READ = (0,3,0,3,4)
RELEASE = (0,1,0,0,4)

def action(vector,mapping,places):
    result = [round_interval(sum(vector[i][0] for i in range(5) if mapping[i]==j),
                             sum(vector[i][1] for i in range(5) if mapping[i]==j),places)
              for j in range(5)]
    mass_check(result)
    return result

def word_probability(case,word,terms,places):
    points = {F(0):[],case["T"]:[]}
    for a,b,_ in case["segments"]:
        points.setdefault(a,[]); points.setdefault(b,[])
    for begin,end in schedule(case,word):
        points.setdefault(begin,[]).append("read")
        if end<=case["T"]:
            points.setdefault(end,[]).append("release")
    probability = [(F(1),F(1))]+[(F(0),F(0))]*4
    previous,max_tail,max_mass_width = F(0),F(0),F(0)
    audits = []
    for t,actions in sorted(points.items()):
        probability,tail = propagate(probability,exposure(case,previous,t)/case["W"],
                                     case["n"],terms,places)
        max_tail = max(max_tail,tail)
        max_mass_width = max(max_mass_width,mass_check(probability))
        for name in actions:
            probability = action(probability,READ if name=="read" else RELEASE,places)
            max_mass_width = max(max_mass_width,mass_check(probability))
        audits.append(dict(t=str(t),actions=actions,
            state=[enclosure(a,b,36) for a,b in probability]))
        previous = t
    lo = max(probability[4][0],1-sum(b for a,b in probability[:4]))
    hi = min(probability[4][1],1-sum(a for a,b in probability[:4]))
    return (lo,hi),dict(word=word,Q_word=enclosure(lo,hi),max_mass_width=str(max_mass_width),
        max_unscaled_tail=str(max_tail),state_order=["clean_p0","dirty_p0","clean_p1","dirty_p1","A"],
        history=audits)

def bounds(case,terms):
    c=F(case["n"]-1,case["n"])
    V=X=F(0)
    survive_lower_lo=survive_lower_hi=F(1)
    audits=[]
    for w in range(case["W"]):
        visits=schedule(case,w)
        edges=sorted({F(0),case["T"]}|{e for e,_ in visits})
        intervals=list(zip(edges[:-1],edges[1:]))
        masses=[exposure(case,a,b)/case["W"] for a,b in intervals]
        V+=c/2*sum((m*m for m in masses),F(0))
        crossing=[]
        for e,f in visits:
            j=(max(F(0),e-case["period"]),e)
            h=(e,min(f,case["T"]))
            mj,mh=exposure(case,*j)/case["W"],exposure(case,*h)/case["W"]
            X+=c*mj*mh
            crossing.append(dict(begin=str(e),release=str(f),executed=f<=case["T"],
                J=[str(t) for t in j],H=[str(t) for t in h],M_J=str(mj),M_H=str(mh),
                pair_term=str(c*mj*mh)))
        cells=lower_cells(case,w)
        for a,b,r in cells:
            m=r*(b-a)/case["W"]
            el,eh,_=exponential_enclosure(m,terms)
            factor=c*m*m/2
            survive_lower_lo*=1-factor*eh
            survive_lower_hi*=1-factor*el
        audits.append(dict(word=w,virtual_cells=[dict(start=str(a),end=str(b),M=str(m))
            for (a,b),m in zip(intervals,masses)],crossing_pairs=crossing,
            lower_cells=[dict(start=str(a),end=str(b),array_rate=str(r)) for a,b,r in cells]))
    return (1-survive_lower_hi,1-survive_lower_lo),V,X,audits

def solve(case,terms=32,places=48,out_places=36):
    if not (0<=case["D"]<case["period"]/case["W"]):
        raise ValueError("declared nonoverlapping operation calendar required")
    live_lo=live_hi=F(1)
    words=[]
    for w in range(case["W"]):
        (a,b),audit=word_probability(case,w,terms,places)
        live_lo*=1-b; live_hi*=1-a
        words.append(audit)
    q_lo,q_hi=1-live_hi,1-live_lo
    (l_lo,l_hi),V,X,audits=bounds(case,terms)
    U=min(F(1),V+X)
    qb,lb=enclosure(q_lo,q_hi,out_places),enclosure(l_lo,l_hi,out_places)
    if not F(lb["upper"])<=F(qb["lower"])<=F(qb["upper"])<=U:
        raise ArithmeticError("bound violation; retain inputs and localize")
    return dict(Q_exact=qb,L=lb,U_E=enclosure(U,U,out_places),U_E_rational=str(U),
        V_rational=str(V),X_E_rational=str(X),V=enclosure(V,V),X_E=enclosure(X,X),
        comparison="L.upper <= Q.lower <= Q.upper <= U_E exact rational",
        factorization="word histories independent; no product of clean inter-release intervals",
        local_states=5,global_enumeration_states=2**(case["W"]+1)+1,
        maximum_uniformization_index=terms,internal_decimal_places=places,
        word_audit=words,bound_audit=audits)
