"""Task 3.1–3.2. Whole-life risk and occupied port seconds on closed native-ECC maps."""
import argparse
import json
from dataclasses import dataclass
from fractions import Fraction as F
from functools import cache, cached_property
from math import ceil, floor
from pathlib import Path
from runpy import run_path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent
PRIOR_DIR = EXP / "t196-cluster-main-20261112"
REVIEW = run_path(str(PRIOR_DIR / "calculate.py"))
BASE = REVIEW["BASE"]
PARENTS = run_path(str(EXP / "t196-visible-parents-20261112/calculate.py"))
GEO, ARCHIVE = REVIEW["profiles"]()
T, C, DELTA, B0 = (REVIEW[k] for k in ("T", "C", "DELTA", "B0"))
XM, XP, J, DE = (REVIEW[k] for k in ("XI_LO", "XI_HI", "J", "DE"))
HARD, READ, WRITE = (REVIEW[k] for k in ("HARD", "READ", "WRITE"))
READ_LO = XM * BASE["READ"] - 2*J
FRAME, NS = BASE["FRAME"], BASE["NS"]
MEAN = F(6, 5)
DEN = 16384
up, down = REVIEW["up"], REVIEW["down"]
aperture, weight = REVIEW["aperture"], REVIEW["weight"]
EPSILONS = [F(1, 10**i) for i in range(1, 5)]


@dataclass(frozen=True)
class Ladder:
    words: int

    @cached_property
    def scan(self):
        return BASE["Scan"](4*self.words)

    @cached_property
    def levels(self):
        reg = BASE["registration"](self.scan)
        return [2**i * self.scan.L for i in range(reg["top_level"]+1)]

    @cached_property
    def counts(self):
        return BASE["thresholds"](self.scan, len(self.levels)-1)

    @cached_property
    def history(self):
        return [XM*(n*self.levels[-1]-self.scan.drain)-2*J for n in self.counts]

    @cached_property
    def amplitude(self):
        return [XP*p/2 for p in self.levels[1:]]

    @property
    def fast(self):
        return XP*self.scan.L + DE

    @property
    def eta(self):
        return F(5*self.words-4, 6*self.words)

    @cached_property
    def fees(self):
        gaps = [XM*p-2*J for p in self.levels]
        increments = [1/a-1/b for a,b in zip(gaps,gaps[1:])]
        start = 2 + T/gaps[-1] + (XP*self.scan.L+J)*sum(increments)
        reset = (XP*self.levels[-1]+2*J)*sum(d*(n+1) for d,n in zip(increments,self.counts))
        return self.scan.addresses*READ*start, self.scan.addresses*READ*reset

    @cache
    def risk(self, eta, env):
        assert eta > 0
        s = self.words*C*eta
        heights = [s*h for h in self.history]

        def coefficient(x):
            return self.fast + sum(a*weight(h*x) for a,h in zip(self.amplitude,heights))

        slope = max(hi*coefficient(lo) for lo,hi in REVIEW["strips"](env.peak))
        scalar = T*B0**2*coefficient(B0) + (env.exposure-B0*T)*slope
        phase = self.fast*aperture(env,self.scan.L)
        phase += sum(a*aperture(env,p) for a,p in zip(self.amplitude,self.levels[1:]))
        mass = env.peak*XP*self.levels[-1]
        kernel = mass/(1-weight(s*mass)) + env.peak*XP*self.scan.phase_max
        rises = (1+1/F("2.71828")**2)*env.rise*sum(self.amplitude)*kernel
        factor = self.words*C**2/2
        return (DELTA, factor*scalar, factor*phase, factor*rises)

    def threshold(self, eps, env):
        def value(j):
            return sum(self.risk(F(j,DEN),env))

        if value(DEN) > eps:
            return {"pass":None, "fail":"1", "q_at_fail_lower":down(value(DEN),12)}
        lo, hi = 0, DEN
        while hi-lo > 1:
            mid = (lo+hi)//2
            if value(mid) <= eps:
                hi = mid
            else:
                lo = mid
        assert lo > 0 and value(lo) > eps >= value(hi)
        return {"pass":str(F(hi,DEN)), "fail":str(F(lo,DEN)),
                "q_at_pass_upper":up(value(hi),12), "q_at_fail_lower":down(value(lo),12)}

    def cost(self, env, mean, eta):
        terms = self.risk(eta,env)
        q = sum(terms)
        assert 0 < q < 1
        hits = (self.words+1)*C*env.exposure
        anchor = self.levels[-1]
        mask = min(env.exposure,(self.fast+2*J)*(env.exposure/(XM*anchor)+2*(env.peak+env.rise)))
        parents = self.words*C*env.exposure/mean
        cells = min(hits, parents+self.words*C*mask/mean)
        start, reset = self.fees
        before_read = start+reset*(1+cells)
        before_write = WRITE*hits
        tail = q*(READ+WRITE)*HARD
        total = before_read+before_write+tail
        lower = (1-q)*self.scan.addresses*READ_LO*(T/(XP*anchor+2*J)-2)
        return {"q":up(q,12), "q_terms_upper":[up(x,15) for x in terms],
                "s_lower":down(lower,3), "s_upper":up(total,3),
                "pct_lower":down(100*lower/T,6), "pct_upper":up(100*total/T,6),
                "repair_events_upper":up(hits,6), "parents_upper":up(parents,6),
                "true_cells_upper":up(cells,6), "reset_fee_s_upper":up(reset,6),
                "pre_read_s_upper":up(before_read,6), "pre_repair_s_upper":up(before_write,6),
                "post_stop_s_upper":up(tail,6)}, q


def physical(scan, words, period, both=True, env=GEO):
    # On this map both x16 phases of one word differ by exactly L/2.
    assert period >= scan.L
    gap = period-scan.L/2 if both else period
    width = XP*gap+2*J+DE
    return DELTA+words*C**2*F(37,76)*(width*env.second+2*env.peak*DE*env.exposure)


def fixed_price(ladder, period, env):
    a, w = ladder.scan.addresses, ladder.words
    stop = min(1, DELTA+w*C**2/2*(XP*period+DE)*(env.second+aperture(env,period)))
    ordinary = min(HARD, a*(2+T/(XM*period-2*J)))
    excess = DELTA*(HARD-ordinary)
    reads = ordinary+excess
    hits = (w+1)*C*env.exposure
    # An auxiliary proof stop can increase writes in any remaining read slot.
    # Only an execution exception can add slots to the fixed calendar.
    writes = min(reads, hits+stop*HARD, hits+stop*ordinary+excess)
    fee = READ*reads+WRITE*writes
    return fee, {"period_s":str(period), "physical_Q_upper":up(physical(ladder.scan,w,period,env=env),12),
                 "stop_upper":up(stop,12), "ordinary_slots_upper":ceil(ordinary),
                 "read_s_upper":up(READ*reads,6), "repair_s_upper":up(WRITE*writes,6),
                 "s_upper":up(fee,3), "pct_upper":up(100*fee/T,6)}


def candidate(ladder, eps):
    scan, w = ladder.scan, ladder.words
    at_l = physical(scan,w,scan.L)
    if at_l > eps:
        return None
    per_frame = F(w)*C**2*F(37,76)*XP*FRAME*GEO.second
    longest = scan.L+FRAME*floor((eps-at_l)/per_frame)
    assert physical(scan,w,longest) <= eps < physical(scan,w,longest+FRAME)
    periods = {scan.L, longest}
    old = REVIEW["FIXED_PERIOD"]
    if scan.L <= old <= longest:
        periods.add(old)
    return min((fixed_price(ladder,p,GEO) for p in sorted(periods)), key=lambda item:item[0])[1]


@dataclass(frozen=True)
class WordBlock:
    """The plateau free-gap lower bound, with intersections for the actual marks."""
    blocks: int
    span: F
    words: int
    first_factor: F
    intersections: F
    subset: str
    max_span: F

    def hazard(self, period):
        visits = 2*(self.span/period+F(2,self.blocks))+F(self.blocks-1,self.blocks*self.words)
        free = max(0,self.span-visits*DE)
        return self.blocks*max(0,self.first_factor*free**2/(1+visits)-self.intersections)


@cache
def word_blocks(w):
    duration = F(BASE["C1"]["lower_witness_plateau_used_s"])
    v = C*GEO.peak
    result = []
    for power in range(-6,13):
        target = F(2)**power
        count = ceil(duration/target)
        span = duration/count
        mu = v*span
        assert mu < 1 and w%2 == 0
        for words, edges, name in [(w,w,"all"), (w//2,0,"even")]:
            first = words*F(37,76)*(1-mu)*v**2
            common = mu/6
            intersections = F(words*(words-1),8)*mu**4 + edges*(common*mu**2+common**2/2)
            result.append(WordBlock(count,span,words,first,intersections,name,target))
    return result


def word_floor(ladder, period):
    best = max(((b.hazard(period),b) for b in word_blocks(ladder.words)),key=lambda item:item[0])
    z, block = best
    return max(0,z/(1+z)-DELTA), block


def common_floor(ladder, cap):
    peak, rise, second = PARENTS["plateau"]()
    period = F(cap,ladder.words)
    missing = ladder.fast/period
    mass = 2*cap*C*peak/MEAN
    loss = ladder.fast*(peak**2+4*peak*rise)+(1+4*period)*peak**2+period*peak*rise
    rem = (1-missing)**2*second-loss
    if missing >= 1 or mass >= 1 or rem <= 0:
        return F(0)
    a = PARENTS["overlap_success"]("compact_1p2",ladder.words)
    z = (1-mass)*C**2*cap*a*rem/(2*MEAN**2)
    return max(0,z/(1+z)-DELTA)


def fixed_floor(ladder, eps):
    # Each word-block test is monotone in P. The two-parent test certifies the
    # entire tail starting at its chosen K even when its value is nonmonotone in K.
    fast_period = XP*ladder.scan.L
    fast_q, fast_block = word_floor(ladder,fast_period)
    fast_witness = {"Q_lower":down(fast_q,12),"subset":fast_block.subset,
                    "max_block_s":str(fast_block.max_span)}
    if fast_q > eps:
        return {"class_empty":True, "fast_witness":fast_witness,
                "s_lower":None,"pct_lower":None}
    lo, hi = F(0), fast_period
    while word_floor(ladder,hi)[0] <= eps:
        hi *= 2
        assert hi < T, "No plateau crossing in the registered block family"
    for _ in range(36):
        mid = (lo+hi)/2
        if word_floor(ladder,mid)[0] > eps:
            hi = mid
        else:
            lo = mid
    q, block = word_floor(ladder,hi)
    meta = {"method":"word_blocks","subset":block.subset,"max_block_s":str(block.max_span)}
    cap = ceil(2*ladder.words*ladder.fast)
    prev = 0
    while F(cap,ladder.words) < hi*2 and 2*cap*C*GEO.peak < MEAN:
        if common_floor(ladder,cap) > eps:
            while cap-prev > 1:
                mid = (prev+cap)//2
                if common_floor(ladder,mid) > eps:
                    cap = mid
                else:
                    prev = mid
            if F(cap,ladder.words) < hi:
                hi, q = F(cap,ladder.words), common_floor(ladder,cap)
                meta = {"method":"two_parents","K_word_s":cap}
            break
        prev, cap = cap, cap*2
    assert q > eps
    price = (1-DELTA)*ladder.scan.addresses*READ_LO*(T/(hi+2*J)-2)
    return {"class_empty":False, "fast_witness":fast_witness,
            "cutoff_physical_s":str(hi), "exclusion_Q_lower":down(q,18),
            "witness":meta,"s_lower":down(price,3),"pct_lower":down(100*price/T,6)}


def decide(row):
    fixed, stair = row["fixed"],row["ladder"]
    low, cand = fixed["s_lower"],fixed["candidate"]
    if fixed["class_empty"]:
        return "excluded", {}
    budgets = {}
    if low is not None:
        for divisor, key in [(1,"advantage"),(2,"twofold")]:
            gap = F(low)/divisor-F(stair["s_upper"])
            resets = gap/F(stair["reset_fee_s_upper"])
            # Equality suffices for 2x; ordinary preference is strict.
            count = ceil(resets)-1 if divisor == 1 else floor(resets)
            budgets[key] = {"s_lower":down(gap,3),
                            "whole_resets_X0":count if count>=0 and row["ladder_pass"] else None}
    if cand:
        budgets["fixed_advantage_s_lower"] = down(F(stair["s_lower"])-F(cand["s_upper"]),3)
    if cand and row["ladder_pass"]:
        if F(low) > F(stair["s_upper"]):
            return "ERR", budgets
        if F(cand["s_upper"]) < F(stair["s_lower"]):
            return "fixed", budgets
    return "open", budgets


def grid_row(ladder, eps):
    cost, q = ladder.cost(GEO,MEAN,ladder.eta)
    lower = fixed_floor(ladder,eps)
    fixed = dict(lower,candidate=candidate(ladder,eps))
    if fixed["class_empty"]:
        assert fixed["candidate"] is None and q > eps
    if fixed["candidate"] is None:
        fixed["continuous_tariff"] = fixed_price(ladder,ladder.scan.L,GEO)[1]
        fast_reads = (1-DELTA)*ladder.scan.addresses*READ_LO*(T/(XP*ladder.scan.L+2*J)-2)
        fixed["continuous_tariff"].update(s_lower=down(fast_reads,3),
                                         pct_lower=down(100*fast_reads/T,6))
    continuous = physical(ladder.scan,ladder.words,ladder.scan.L,both=False)
    row = {"scope":"geo","words":ladder.words,"epsilon":str(eps),"law":"compact_1p2",
           "m":str(MEAN),"u_upper":up(continuous/eps,9),"continuous_Q_upper":up(continuous,12),
           "u_test_boundary_lower":down(continuous/q,9),
           "paired_continuous_Q_upper":up(physical(ladder.scan,ladder.words,ladder.scan.L),12),
           "eta":str(ladder.eta),"threshold":ladder.threshold(eps,GEO),"ladder":cost,
           "ladder_pass":q<=eps,"fixed":fixed}
    row["choice"],row["budget"] = decide(row)
    return row


def inherited(rows, reference):
    """Keep the reviewed transverse slice, including its original fixed candidate."""
    anchor = next(r for r in rows if r["words"]==32768 and F(r["epsilon"])==F("0.001"))
    ladder = Ladder(32768)
    for scope,env in [("geo",GEO),("reconstructions",ARCHIVE)]:
        for law,mean in [("compact_1p2",MEAN),("two_uniform",2),("compact_4",4),
                         ("compact_5",5),("compact_8",8)]:
            old = reference["laws"][law][scope]
            eta = F(old["eta"])
            cost, q = ladder.cost(env,mean,eta)
            assert (cost["s_lower"],cost["s_upper"],cost["q"]) == (
                old["ladder_s_lower"],old["ladder_s_upper_I0_X0"],old["stop_Q_upper"])
            fixed = {"class_empty":False,"s_lower":old["fixed_s_lower"],
                     "pct_lower":old["fixed_percent_lower"],"K_word_s":old["fixed_K_word_s"],
                     "exclusion_Q_lower":old["fixed_exclusion_Q_lower"],
                     "candidate":{"period_s":str(REVIEW["FIXED_PERIOD"]),
                                  "s_upper":old["fixed_candidate_s_upper"],
                                  "pct_upper":old["fixed_candidate_percent_upper"],
                                  "physical_Q_upper":old["fixed_candidate_Q_upper"]}}
            if law=="compact_1p2" and scope=="geo":
                anchor["prior_fixed_473"] = fixed
                assert F(anchor["fixed"]["s_lower"]) >= F(fixed["s_lower"])
                assert F(anchor["fixed"]["candidate"]["s_upper"]) <= F(fixed["candidate"]["s_upper"])
                continue
            threshold = ladder.threshold(F("0.001"),env)
            assert threshold["pass"] == reference["thresholds"][scope]["eta_sufficient"]
            continuous = physical(ladder.scan,32768,ladder.scan.L,both=False,env=env)
            row = {"scope":scope,"words":32768,"epsilon":"1/1000","law":law,"m":str(mean),
                   "u_upper":up(1000*continuous,9),"continuous_Q_upper":up(continuous,12),
                   "u_test_boundary_lower":down(continuous/q,9),
                   "eta":str(eta),"threshold":threshold,"ladder":cost,"ladder_pass":q<=F("0.001"),
                   "fixed":fixed}
            row["choice"],row["budget"] = decide(row)
            rows.append(row)


def result():
    maps, rows = {}, []
    for w in (16384,32768,65536):
        ladder = Ladder(w)
        scan, top = ladder.scan,ladder.levels[-1]
        assert XP*(top+scan.L)+2*J+DE < 6 < XP*2*top
        assert XM*(scan.drain-scan.phase_max) >= DE+2*J
        assert XM*(scan.L-scan.drain) >= XP*200*NS+2*J
        maps[str(w)] = {"MiB":str(F(4*w,2**20)),"x16_addresses":scan.addresses,
                  "L_s":str(scan.L),"anchor_s":str(top),"top_stride":int(top/scan.L),
                  "same_phase_s_upper":up(XP*top+2*J,12),
                  "including_all_phases_s_upper":up(XP*(top+scan.L)+2*J+DE,12),
                  "zero_cells":ladder.counts,"reset_fee_s_upper":up(ladder.fees[1],6)}
        rows.extend(grid_row(ladder,eps) for eps in EPSILONS)
    accepted = json.loads((PRIOR_DIR/"result.json").read_bytes())
    inherited(rows,accepted)
    assert len(rows) == 21 and T == 315576000 and C == F(1,524288)
    return {"base":"c5f46da5c3fb9b3fda2a979d6ffc69ce85e22fc1","T_s":int(T),
            "delta_exec":str(DELTA),"maps":maps,"rows":rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    args = parser.parse_args()
    path = HERE/"result.json"
    data = result()
    if args.check:
        assert data == json.loads(path.read_bytes())
        print("12 GEO points and the 10-row reference slice agree (one shared point).")
    else:
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
