"""Directed arithmetic for the single and dyadic local-count rules."""
import argparse
import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "experiments/c1-common-geo-20261109"
SIX = json.loads((DATA / "six.json").read_text(encoding="utf-8"))
COVERAGE = json.loads((DATA / "coverage.json").read_text(encoding="utf-8"))
W = 65_536
T = F(SIX["T"])
WORD_RATE_FACTOR = F(39, SIX["D"])
B = F(COVERAGE["B_s_inv"])
S1, S2 = F(SIX["S1_max"]), F(SIX["S2_max"])
U = F("28.855")
DELTA = F(SIX["delta_exec"])
EPS = F(1, 1000)
E_LO = F("2.71828")
PAIR_FACTOR = F(W, 2) * WORD_RATE_FACTOR**2
HISTORY_RATIO = F("0.00168")
NS = F(1, 10**9)


@dataclass(frozen=True)
class Calendar:
    name: str
    L: F
    xi_lo: F
    xi_hi: F
    jitter: F
    aperture: F
    phase_max: F
    min_spacing: F
    drain: F
    install: F | None

    def __post_init__(self):
        assert self.drain <= self.L
        if self.install is not None:
            assert self.drain + self.install <= self.L
        assert self.xi_lo*self.min_spacing > self.aperture
        assert self.aperture >= 2*self.jitter
        assert 0 <= self.phase_max < self.L


OLD = Calendar("PR431", 196*W*NS, F(".99999"), F("1.00001"), NS/2,
               124*F("1.00001")*NS + 3*NS/2, (196*W-420)*NS,
               164*NS, 196*W*NS, None)
# PR448, SERVICE.md / calendar.json, 44ac01ebbebd6571d0c8b068b34070bab4511d2f.
GE_L = 1400*(W//2)*NS
GE = Calendar("CY62167GE30-45", GE_L, F(".99999"), F("1.00001"), NS/2,
              F("501.505")*NS, GE_L-880*NS, 520*NS, GE_L-300*NS, 200*NS)


def up(x, n=9):
    scale = 10**n
    v = ceil(x*scale)
    return f"{v//scale}.{v%scale:0{n}d}"


def down(x, n=9):
    if x < 0:
        return "-" + up(-x, n)
    scale = 10**n
    v = floor(x*scale)
    return f"{v//scale}.{v%scale:0{n}d}"


def geometry(cal, period, cells):
    d, J = cal.aperture, cal.jitter
    physical = cal.xi_hi*period
    H = cal.xi_lo*(cells*period-cal.drain)-2*J
    span = cal.xi_hi*((cells+1)*period+cal.L)+d+2*J
    n_overlap = ceil((span+2*d+2*J)/(cal.xi_lo*period))+3
    n = ceil((T+2*J+d)/(cal.xi_lo*period))+3
    return H, physical+d, n, span, n_overlap


def fast_part(cal):
    _, fast, n, _, _ = geometry(cal, cal.L, 2)
    return PAIR_FACTOR*fast*(S2+B*B*cal.aperture*n)


def discrete_rise(cal, period, n_overlap, s):
    mass = B*cal.xi_hi*period
    assert s*mass < 2
    # (1-exp(-s*mass)) >= s*mass * (1-s*mass/2).
    remainder = mass/(2-s*mass)
    lag = B*(cal.xi_hi*cal.phase_max+n_overlap*cal.aperture)
    return 1/s + remainder + lag


def single(cal, stride, gamma=F(1,2)):
    period = stride*cal.L
    cells = ceil(300/period)
    H, span_s, n, age, n_overlap = geometry(cal, period, cells)
    s = gamma*WORD_RATE_FACTOR*(W-1)
    fast = fast_part(cal)
    quiet = PAIR_FACTOR*span_s*(S1+B*cal.aperture*n)/(E_LO*s*H)
    old_rise = PAIR_FACTOR*span_s*B*U*(age+n_overlap*cal.aperture)
    sharp = discrete_rise(cal, period, n_overlap, s)
    literal = 1/s + B*span_s
    largest_s = W*WORD_RATE_FACTOR
    worst_slack = (1/largest_s + B*span_s
                   - discrete_rise(cal,period,n_overlap,largest_s))
    risk = DELTA+fast+quiet+PAIR_FACTOR*span_s*U*sharp
    claim = DELTA+fast+quiet+PAIR_FACTOR*span_s*U*literal
    return {"period_multiple":stride, "cells":cells, "nominal_history_s":up(cells*period),
            "visible_H_lower_s":down(H), "fast":up(fast,12), "quiet":up(quiet,12),
            "old_total":up(DELTA+fast+quiet+old_rise),
            "literal_verified":sharp <= literal, "literal_slack_lower":down(literal-sharp),
            "literal_slack_all_physical_s_lower":down(worst_slack),
            "total_by_literal_d0":up(claim) if sharp <= literal else None,
            "total_by_discrete_d0":up(risk), "total_by_discrete_d1e4":up(risk+F("0.0001")),
            "total_by_literal_d1e4":up(claim+F("0.0001")) if sharp<=literal else None,
            "joint_stop_upper":up(risk)}


def exp_upper(z):
    """Upper bound on exp(-z), including for large z; round up before reuse."""
    assert z >= 0
    # The binomial power is a lower bound on exp(z).
    bound = (1 + z/64)**(-64)
    return F(ceil(bound*10**18), 10**18)


def phase_mask(cal, period):
    """Integral of nu^2 on periodic copies of a word's write aperture."""
    return cal.aperture*(S2/(cal.xi_lo*period) + B*B + 4*B*U)


def thresholds(cal):
    frame = 512*cal.L
    return [ceil(((2**m*cal.L/HISTORY_RATIO + 2*cal.jitter)/cal.xi_lo + cal.L)/frame)
            for m in range(1,10)]


def scalar_bound(b, amplitudes, histories, fast, s):
    # Subdivide the fixed scalar interval [b,B] using outward endpoints.
    def coefficient(x):
        return fast + sum(a*exp_upper(s*h*x) for a,h in zip(amplitudes,histories))

    left = b
    slope = F(0)
    pieces = 0
    while left < B:
        right = min(B,2*left)
        step = (right-left)/32
        for i in range(32):
            lo = left+i*step
            hi = lo+step
            slope = max(slope,(hi+b)*coefficient(lo))
        left = right
        pieces += 32
    result = T*b*b*coefficient(b)+(S1-b*T)*slope
    return result, slope, pieces


def dyadic_pairs(cal, gamma=F(1,2), binary64=False):
    b = F(COVERAGE["b_s_inv"])
    s = gamma*WORD_RATE_FACTOR*(W-1)
    top = 6 if binary64 else 9
    frame = 2**top*cal.L
    levels = [2**m*cal.L for m in range(1,top+1)]
    # The binary controller skips all six splits on the same admission.
    counts = [ceil(300/frame)]*top if binary64 else thresholds(cal)
    histories = [cal.xi_lo*(n*frame-cal.drain)-2*cal.jitter for n in counts]
    if not binary64:
        assert all(h >= (cal.xi_hi*p+2*cal.jitter)/HISTORY_RATIO for h,p in zip(histories,levels))
    a = [cal.xi_hi*p/2 for p in levels]
    fast = cal.xi_hi*cal.L+cal.aperture
    ideal, slope, pieces = scalar_bound(b,a,histories,fast,s)
    phase = fast*phase_mask(cal,cal.L)
    phase += sum(u*phase_mask(cal,p) for u,p in zip(a,levels))
    mass = B*cal.xi_hi*frame
    # e > 2.71828, so its inverse square bounds exp(-2) from above.
    kernel = mass/(1-exp_upper(s*mass)) + B*cal.xi_hi*cal.phase_max
    variation = (1 + 1/E_LO**2)*sum(a)*U*kernel
    q = DELTA+PAIR_FACTOR*(ideal+phase+variation)
    return {"level_thresholds":counts,"history_s_lower":[down(h,6) for h in histories],
            "scalar_intervals":pieces, "scalar_slope_upper":up(slope,12),
            "profile_term":up(PAIR_FACTOR*ideal,12), "overlaps":up(PAIR_FACTOR*phase,12),
            "variation":up(PAIR_FACTOR*variation,12), "kernel_upper":up(kernel,9),
            "joint_stop_upper_d0":up(q), "joint_stop_upper_d1e4":up(q+F("0.0001"))}


def price(cal, q, ledger, *, stride=None):
    """Conditional lifetime upper at I=0 and cost increment per further reset."""
    main_cap, read, repair, target = ledger
    touches = W*WORD_RATE_FACTOR*S1
    q = min(F(1),F(q))
    if stride is None:
        levels = [2**i for i in range(10)]
        counts = thresholds(cal)
    else:
        levels = [1,stride]
        counts = [ceil(300/(stride*cal.L))]
    frame = levels[-1]*cal.L
    frame_hi = cal.xi_hi*frame+2*cal.jitter
    widths = [cal.xi_lo*p*cal.L-2*cal.jitter for p in levels]
    fast = [min(T,cal.xi_hi*cal.L+cal.jitter + (n+1)*frame_hi*(1+2*touches))
            for n in counts]
    changes = [1/x-1/y for x,y in zip(widths,widths[1:])]
    starts = 2 + T/widths[-1] + sum(a*t for a,t in zip(changes,fast))
    reads = W*starts + q*main_cap
    writes = 2*touches+q*main_cap
    subtotal = read*reads+repair*writes
    increment = read*W*sum(a*(n+1)*frame_hi for a,n in zip(changes,counts))
    hard_switch = 2*ceil(T/(cal.xi_lo*frame-2*cal.jitter))+4
    nlevels = len(levels)-1
    switches = nlevels+(nlevels+1)*(2*touches)+q*hard_switch
    out = {"before_stop_fast_s":up(fast[0],3), "all_fast_s":up(min(T,fast[0]+q*T),3),
           "switches_upper":ceil(switches),"read_repair_bus_s":up(subtotal,3),
           "read_repair_percent":up(100*subtotal/T,6),
           "seconds_per_invalid_cell":up(increment,6)}
    if target is not None:
        out["margin_to_half_constant_lower_s"] = down(target-subtotal,3)
    return out


def old_ledger():
    row = next(r for r in SIX["rows"] if r["W"] == W and F(r["epsilon"])==EPS)
    return (F(row["necessary"]["maximum_reads_upper"]),48*NS*OLD.xi_hi+OLD.jitter,
            56*NS*OLD.xi_hi+OLD.jitter, F(row["necessary"]["bus_lower_s"])/2)


def fixed_ge():
    # High-start singleton member. On the nominal legal execution 2J is
    # a conservative allowance per visit and per interval between starts.
    plateau = F(SIX["plateau_s"])
    nb = ceil((plateau-1)/120)
    block = (plateau-1)/nb
    word = WORD_RATE_FACTOR*B

    def witness(period):
        visits = block/period+2
        free = max(0,block-visits*GE.aperture)
        z = nb*W*F(38,78)*(1-word*block)*word**2*free**2/(1+visits)
        return z/(1+z)-DELTA

    lo, hi = F("0.001"), F(1)
    assert witness(lo) < EPS < witness(hi)
    for _ in range(40):
        middle = (lo+hi)/2
        if witness(middle) > EPS:
            hi = middle
        else:
            lo = middle
    assert witness(hi)>EPS
    visits = (1-DELTA)*W*(T/(hi+2*GE.jitter)-2)
    bus_lower = visits*(240*NS*GE.xi_lo-2*GE.jitter)
    nominal = GE.xi_hi*GE.L+GE.aperture
    sufficient = DELTA+PAIR_FACTOR*nominal*(S2+phase_mask(GE,GE.L))
    assert sufficient+F("0.0001")<EPS
    return bus_lower, {"period_excluded_from_s":up(hi,12),
                       "witness_above_epsilon":down(witness(hi)-EPS,20),
                       "constant_L_stop_upper_d0":up(sufficient),
                       "necessary_known_bus_s":down(bus_lower,3),
                       "necessary_known_bus_percent":down(100*bus_lower/T,6)}


def ge_ledger(lower):
    # At most two main word slots in each 1400 ns frame even after the stop.
    cap = 2*(ceil((T+2*GE.jitter)/(1400*NS*GE.xi_lo))+2)
    return cap, 240*NS*GE.xi_hi+2*GE.jitter, 260*NS*GE.xi_hi+2*GE.jitter, lower/2


def verify_engineer_calendar(path):
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    header = f"blob {len(raw)}\0".encode()
    assert hashlib.sha1(header + raw).hexdigest() == "53a15096183cd03ed0684bc15e2817b35128951c"
    data = json.loads(raw)
    positions = [i//2*data["frame_ns"]+data["word_slots_ns"][i%2] for i in range(W)]
    assert len({i*data["word_stride"] % W for i in range(W)}) == W
    assert F(data["L_ns"])*NS == GE.L
    assert max(positions)*NS == GE.phase_max
    assert min(b-a for a,b in zip(positions, positions[1:]+[data["L_ns"]]))*NS == GE.min_spacing
    assert F(data["xi_minus"]) == GE.xi_lo and F(data["xi_plus"]) == GE.xi_hi
    assert F(data["J_ns"])*NS == GE.jitter
    assert data["D_o_ns"]*NS == GE.drain and data["I_o_ns"]*NS == GE.install
    assert data["E_max_ns"]*NS*GE.xi_hi + 3*GE.jitter == GE.aperture
    assert F(data["aperture_upper_ns"])*NS == GE.aperture
    assert data["read_port_ns"] == 240 and data["repair_extra_ns"] == 260


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--single-only", action="store_true")
    parser.add_argument("--check", action="store_true", help="Compare to the directed reference JSON")
    parser.add_argument("--engineer-calendar", type=Path, help="Verify the pinned PR448 calendar.json")
    args = parser.parse_args()
    if args.engineer_calendar is not None:
        verify_engineer_calendar(args.engineer_calendar)
    lower, constant = fixed_ge()
    output = {}
    for cal,ledger in ((OLD,old_ledger()),(GE,ge_ledger(lower))):
        rows = [single(cal,32),single(cal,64)]
        result = {"single":rows}
        if not args.single_only:
            stairs = dyadic_pairs(cal)
            result["same_binary64_by_dyadic_pairs"] = dyadic_pairs(cal,binary64=True)
            result["ladder"] = stairs
            result["conditional_price_at_I0"] = {
                "single64":price(cal,rows[1]["joint_stop_upper"],ledger,stride=64),
                "ladder":price(cal,stairs["joint_stop_upper_d0"],ledger)}
        output[cal.name] = result
    output[GE.name]["fixed"] = constant
    if args.check:
        expected = json.loads(Path(__file__).with_name("result.json").read_text(encoding="utf-8"))
        for name, sections in output.items():
            for key,value in sections.items():
                assert value == expected[name][key], (name,key)
        print("Directed results match the reference.")
        return
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
