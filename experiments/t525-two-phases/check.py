"""Independent substitution from the calendar: child intervals, GEO envelope and price."""
import json
from decimal import Decimal as D, ROUND_CEILING, localcontext
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path
from runpy import run_path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent
prior = run_path(str(EXP / "t186-native-cost-map/check.py"))
r = json.loads((HERE / "result.json").read_bytes())
old = json.loads((EXP / "t504-large-bank/result.json").read_bytes())
row = next(item for item in old["rows"] if item["MiB"] == "1/4")
calendar = prior["calendar"]
words = 65_536
dec, rounded = prior["decimal"], prior["rounded"]


def phase_checks():
    offsets, frame = calendar["visit_offsets_ns"], calendar["frame_ns"]
    scan_ns = 2*words*frame//len(offsets)
    starts = [j//len(offsets)*frame+offsets[j % len(offsets)] for j in range(2*words)]
    assert all(y-x == scan_ns//2 for x, y in zip(starts[:words], starts[words:]))
    assert starts[words-1] < scan_ns//2 and starts[-1] < scan_ns
    # Physical time relative to the lower phase. Include the ends and interior
    # of each aperture and free interval; moving the origin preserves membership.
    L = F(scan_ns, 10**9)
    h, d = prior["xp"]*L/2, prior["edge"]
    points = (0, d/2, d, (h+d)/2, h, h+d/2, h+d,
              (3*h+d)/2, 2*h, 2*h+d/2, 2*h+d)
    for u in points:
        for v in points:
            if v < u:
                continue
            left = v <= h+d
            right = u >= h
            cross = u < h and v > h+d
            assert (left or right) != cross
            if cross:
                # An actual middle operation removes u by its release, also
                # when the second arrival coincides with the later visit.
                for start, release in ((h, h+d), (h+d/4, h+3*d/4), (h+d/2, h+d)):
                    assert u < start <= release < v
    return L


def substitution():
    L = phase_checks()
    xm, xp, J, edge = (prior[k] for k in ("xm", "xp", "J", "edge"))
    levels = [L]
    while 2*xp*levels[-1]+2*J <= 6:
        levels.append(2*levels[-1])
    top = levels[-1]
    counts = [ceil(((p/F(".00168")+2*J)/xm+L)/top) for p in levels[1:]]
    assert counts == row["zero_cell_counts"] == r["zero_cell_counts"]
    # Exercise the common boundary, the first authorization, and truncated
    # slow strides after each attainable reset. An already-issued step ends.
    stride = int(top/L)
    for step in (int(p/L) for p in levels):
        for reset_at in range(stride+1):
            starts = list(range(0, stride+1, step))
            next_decision = next(k for k in starts if k >= reset_at)
            actual = set(range(0, next_decision, step)) | set(range(next_decision, stride+1))
            assert 0 in actual and stride in actual
            for k in range(stride):
                if k not in actual:
                    assert k > 0 and k < next_decision and step >= 2
    cut = L-calendar["report_cut_ns_before_next_pass"]*prior["ns"]
    history = [dec(xm*(n*top-cut)-2*J) for n in counts]
    eta = (1-F(4, 5*words))/F(6, 5)
    assert str(eta) == r["visibility_parents_per_inversion"]
    c = prior["c"]
    rate, pair = dec(words*c*eta), dec(words*c**2/2)
    b, B, S1, S2, T = (dec(prior[k]) for k in ("b", "B", "S1", "S2", "T"))
    U = dec(old["GEO"]["rise_s-1"])
    half, aperture = dec(xp*L/2), dec(edge)
    weighted = [(half, history[0], L)]
    weighted.extend((dec(xp*p/2), h, p) for h, p in zip(history, levels[1:]))
    fast = half+aperture

    def weight(z):
        return (((1+z/64)**-64)*10**18).to_integral_value(rounding=ROUND_CEILING)/10**18

    def kernel(x):
        return fast+sum(a*weight(rate*x*h) for a, h, _ in weighted)

    left, bound, strips = b, D(0), 0
    while left < B:
        right = min(2*left, B)
        step = (right-left)/32
        for i in range(32):
            x = left+i*step
            bound = max(bound, (b+x+step)*kernel(x))
            strips += 1
        left = right
    profile = T*b*b*kernel(b) + (S1-b*T)*bound

    def mask(period):
        return aperture*(S2/dec(xm*period)+B*B+4*B*U)

    repeats = fast*mask(L/2)+sum(a*mask(p) for a, _, p in weighted)
    mass = B*dec(xp*top)
    last_phase = L - (calendar["frame_ns"]-calendar["visit_offsets_ns"][-1])*prior["ns"]
    edge_kernel = mass/(1-weight(rate*mass))+B*dec(xp*last_phase)
    rises = sum(a for a, _, _ in weighted)*edge_kernel*U*(1+D("2.71828")**-2)
    terms = [dec(prior["delta"]), pair*profile, pair*repeats, pair*rises]
    for reported, value in zip(r["new_terms_upper"], terms, strict=True):
        rounded(reported, F(value))
    stop = sum(terms)
    rounded(r["stop_upper_also_bounds_physical_Q"], F(stop))
    rounded(r["epsilon_minus_stop_lower"], F(D(".001")-stop), True)
    old_stop, _, fees = prior["ladder_check"]("geo", words, str(eta))
    rounded(r["reduction_of_certificate_lower"], F(old_stop-stop), True)
    assert stop < D(".001") < old_stop

    start, reset, hits, cell_mass = fees
    cells = min(hits, cell_mass/dec(F(6, 5)))
    cr, cw, hard = (dec(prior[k]) for k in ("cr", "cw", "hard"))
    read_fee, reset_fee = 2*words*cr*start, 2*words*cr*reset
    before = read_fee+reset_fee*(1+cells)
    tail = (cr+cw)*hard*stop
    cost = before+cw*hits+tail
    for key, value in (("reset_bus_s_upper", reset_fee), ("true_cells_upper", cells),
                       ("post_stop_bus_s_upper", tail), ("pre_stop_read_s_upper", before),
                       ("pre_stop_write_s_upper", cw*hits), ("price_s_upper", cost),
                       ("price_percent_upper", 100*cost/T)):
        rounded(r[key], F(value))
    top_real = dec(xp*top+2*J)
    fast_restore = (1+counts[0])*top_real
    time = min(T, dec(xp*L+J)+fast_restore*(1+cells)+T*stop)
    rounded(r["extra_fast_s_per_reset_upper"], F(fast_restore))
    rounded(r["fast_s_upper"], F(time))
    rounded(r["fast_percent_upper"], F(100*time/T))
    read_min = xm*prior["read"]-2*J
    rounded(r["price_s_lower"], F((1-stop)*2*words*dec(read_min)*(T/top_real-2)), True)
    frame = prior["F0"]
    peak = 100*len(calendar["visit_offsets_ns"])*(prior["cr"]+prior["cw"]+frame-xm*frame+2*J)/frame
    rounded(r["peak_sliding_1400ns_percent_upper"], peak)
    fixed = F(row["fixed"]["s_lower"])
    cost_up, reset_up = F(r["price_s_upper"]), F(r["reset_bus_s_upper"])
    assert r["best_fixed_s_lower"] == row["fixed"]["s_lower"]
    assert r["sufficient_fixed_candidate_s_upper"] == row["fixed"]["quote"]["s_upper"]
    rounded(r["fixed_over_ladder_lower"], fixed/cost_up, True)
    rounded(r["saved_s_lower"], fixed-cost_up, True)
    rounded(r["twofold_extra_s_lower"], fixed/2-cost_up, True)
    assert r["twofold_whole_resets_X0"] == floor((fixed/2-cost_up)/reset_up)
    print(f"{words} phase pairs, edge cases, {strips} intensity strips and the full-price ledger agree.")


if __name__ == "__main__":
    with localcontext() as ctx:
        ctx.prec = 80
        substitution()
