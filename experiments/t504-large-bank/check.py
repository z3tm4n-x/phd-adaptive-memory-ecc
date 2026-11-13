"""Independent checks from the service calendar, plateau and per-position rates."""
import json
from decimal import localcontext
from fractions import Fraction as F
from math import ceil
from pathlib import Path
from runpy import run_path


here = Path(__file__).resolve().parent
source = run_path(str(here.parent / "t186-native-cost-map/check.py"))
data = json.loads((here / "result.json").read_bytes())
calendar = source["calendar"]
rounded, dec = source["rounded"], source["decimal"]
xm, xp, jitter, ns = (source[k] for k in ("xm", "xp", "J", "ns"))
T, c, delta, edge = (source[k] for k in ("T", "c", "delta", "edge"))
cr, cw, hard, frame = (source[k] for k in ("cr", "cw", "hard", "F0"))
s1, s2, peak = (source[k] for k in ("S1", "S2", "B"))
offsets = calendar["visit_offsets_ns"]
eps = F(data["epsilon_accumulation"])


def check_addresses(r):
    n, dies, w = r["words_per_die"], r["dies"], r["words"]
    assert w == n*dies and 4*w == F(r["MiB"])*2**20
    seen = [bytearray(2*n) for _ in range(dies)]
    scan_ns = 2*w//4*calendar["frame_ns"]

    def time(j):
        return j//4*calendar["frame_ns"]+offsets[j%4]

    visits = 0
    for half in range(2):
        for die in range(dies):
            for word in range(n):
                address = half*n+word
                assert not seen[die][address]
                seen[die][address] = 1
                if half == 0:
                    assert time(visits+w)-time(visits) == scan_ns//2
                visits += 1
    assert visits == r["addresses_x16"] and all(all(occupied) for occupied in seen)
    assert time(visits-1)+200 <= scan_ns-300 and scan_ns-300+200 < scan_ns
    assert F(r["L_local_s"]) == scan_ns*ns
    assert F(r["parent_rate_per_nu"]) == w*c/F(6, 5)
    assert F(r["parent_rate_per_die_per_nu"]) == n*c/F(6, 5)
    assert F(r["eta"]) == (1-F(4, 5*w))/F(6, 5)
    return visits


def check_fixed(r):
    w, L = r["words"], F(r["L_local_s"])
    f = r["fixed"]
    prior = f["prior_floor"]
    old_witness = prior["fast_witness"]
    common = source["word_witness"](w, xp*L, old_witness["max_block_s"], old_witness["subset"])
    rounded(old_witness["Q_lower"], common, True)
    quote = f["quote"]
    period = F(quote["period_s"])
    factor = w*c**2*F(37, 76)

    def upper(p):
        return delta+factor*((xp*(p-L/2)+2*jitter+edge)*s2+2*peak*edge*s1)

    assert (period/frame).denominator == 1 and period >= L
    rounded(quote["physical_Q_upper"], upper(period))
    if f["quote_is_candidate"]:
        assert upper(period) <= eps < upper(period+frame)
        cut = F(prior["cutoff_physical_s"])
        witness = source["common_witness"](w, L, prior["witness"]["K_word_s"])
        rounded(prior["exclusion_Q_lower"], witness, True)
        rounded(f["s_lower"], (1-delta)*2*w*(xm*source["read"]-2*jitter)*(T/(cut+2*jitter)-2), True)
    else:
        assert period == L and upper(period) > eps
    reads = min(hard, 2*w*(2+T/(xm*period-2*jitter)))
    extra = delta*(hard-reads)
    phase = edge*(s2/(xm*period)+peak**2+4*peak*F(data["GEO"]["rise_s-1"]))
    stop = min(1, delta+w*c**2/2*(xp*period+edge)*(s2+phase))
    writes = min(reads+extra, (w+1)*c*s1+min(stop*hard, stop*reads+extra))
    rounded(quote["s_upper"], cr*(reads+extra)+cw*writes)
    rounded(quote["s_lower"], (1-delta)*2*w*(xm*source["read"]-2*jitter)*(T/(xp*period+2*jitter)-2), True)
    return common


def check_spacing(r):
    # Reconstruct the bound from the outer (possibly clipped) visits and the
    # factorial moments of neighbouring and non-neighbouring word counts.
    w = r["words"]
    gap = xp*F(r["L_local_s"])/2
    bound = r["fixed"]["paired_spacing_witness"]
    blocks = ceil(4*source["span"])
    span = source["span"]/blocks
    assert blocks == bound["blocks"] and F(bound["gap_s"]) == gap
    starts = 0
    while starts*gap <= span+edge:
        starts += 1
    assert starts == bound["max_visits"]
    s = gap-edge
    lower_sq = s*(span-starts*edge)-2*(s/2)**2
    rounded(bound["sum_free_squares_s2_lower"], lower_sq, True)

    # Direct partitions, including a block edge in an aperture, a complete
    # inter-visit interval and long periods between the two halves.
    for p in (2*gap, 2*gap+xp*frame, 3*gap, 9*gap, F(1)):
        for offset in (F(0), edge/2, edge, gap/2, gap-edge/2, 2*gap, span-edge/2):
            windows = sorted((start, start+edge)
                             for j in range(-4, ceil(span/p)+2)
                             for start in (offset+j*p, offset+j*p+gap)
                             if start < span and start+edge > 0)
            end = F(0)
            free_sq = F(0)
            for a, b in windows:
                free_sq += max(a-end, 0)**2
                end = min(span, b)
            assert len(windows) <= starts and free_sq+(span-end)**2 >= lower_sq

    rate = c*peak
    mu = rate*span
    shared = mu/6
    pair_count = w*(w-1)//2
    joint = (pair_count-w)*mu**4/4 + w*(mu**4/4+shared*mu**2+shared**2/2)
    per_block = w*(1-mu)*rate**2*F(37, 76)*lower_sq-joint
    q = 1-1/(1+blocks*per_block)-delta
    assert q > eps
    rounded(bound["Q_lower"], q, True)
    return q


def check_two_touch_marks():
    positions = calendar["inner_data_bits"] + calendar["inner_check_bits"]
    flips = [1 << i for i in range(positions)]
    for initial in [0, *flips]:
        successes = 0
        for first in flips:
            after_first = initial ^ first
            for second in flips:
                after_second = after_first ^ second
                crossed = max(after_first.bit_count(), after_second.bit_count()) >= 2
                witness = (first != second) if initial == 0 else (first != initial)
                assert crossed == witness
                successes += crossed
        assert F(successes, positions**2) == F(37, 38)


def check_ladder(r, common):
    w, L = r["words"], F(r["L_local_s"])
    levels = list(map(F, r["levels_local_s"]))
    top = levels[-1]
    assert levels == [L*2**i for i in range(r["top_stride"].bit_length())]
    assert xp*top+2*jitter <= 6 < 2*xp*top+2*jitter
    counts = [ceil(((p/F("0.00168")+2*jitter)/xm+L)/top) for p in levels[1:]]
    assert r["zero_cell_counts"] == counts
    with localcontext() as ctx:
        ctx.prec = 72
        q, low, (start, reset, hits, weighted_mass) = source["ladder_check"]("geo", w, r["eta"])
        cells = min(hits, weighted_mass/dec(F(6, 5)))
        cost = dec(2*w*cr)*(start+reset*(1+cells))+dec(cw)*hits+dec(hard*(cr+cw))*q
        ladder = r["ladder"]
        rounded(ladder["s_lower"], F(low), True)
        rounded(ladder["s_upper"], F(cost))
        rounded(ladder["q"], F(q))
        rounded(ladder["Q_lower"], common, True)
        true_cells = ceil(F(cells)*10**6)/F(10**6)
        fast = min(T, xp*L+jitter+(counts[0]+1)*(xp*top+2*jitter)*(1+true_cells)+F(q)*T)
        rounded(ladder["fast_s_upper"], fast)
        rounded(ladder["fast_pct_upper"], 100*fast/T)
        assert (common > eps) == r["fixed"]["class_empty"] == (ladder["verdict"] == "excluded")
        assert r["only_ladder_proved"] == (common > eps and F(q) <= eps)


def check_table():
    # Compare display values at their printed precision (outward rounding).
    printed = source["printed"]
    lines = (here / "README.md").read_text(encoding="utf-8").splitlines()
    table = [line.strip("|").split("|") for line in lines if line.startswith("| ")]
    assert len(table) == 1+len(data["rows"])
    for r, cols in zip(data["rows"], table[1:]):
        cols = [col.strip() for col in cols]
        f, ladder = r["fixed"]["quote"], r["ladder"]
        assert len(cols) == 9 and cols[0] == printed(r["MiB"], 2)
        assert cols[1] == printed(r["words"], 0)+" / "+printed(r["addresses_x16"], 0)
        assert cols[2] == printed(r["L_local_s"], 7)+" / "+str(r["top_stride"])+"L"
        period = printed(f["period_s"], 7) if r["fixed"]["quote_is_candidate"] else "L†"
        assert cols[3] == period+" · ["+printed(f["Q_lower"], 12)+", "+printed(f["physical_Q_upper"], 12)+"]"
        assert cols[5] == "["+printed(ladder["Q_lower"], 12)+", "+printed(ladder["q"], 12)+"]"
        for col, cost in ((cols[4], f), (cols[6], ladder)):
            assert col == source["price_cell"](cost["s_lower"], cost["s_upper"],
                                                cost["pct_lower"], cost["pct_upper"])
        assert cols[7] == printed(data["port"]["sliding_1400ns_peak_pct_upper"], 3)+"% / "+printed(ladder["fast_s_upper"], 0)
        assert cols[8] == ("Оба исключены" if r["fixed"]["class_empty"] else "Постоянный подтверждён, лестница открыта")


def main():
    assert [F(r["MiB"]) for r in data["rows"]] == [F(1, 4), F(1, 2), 1, 2, 4]
    check_two_touch_marks()
    visits = 0
    for r in data["rows"]:
        visits += check_addresses(r)
        common = check_fixed(r)
        if r["fixed"]["paired_spacing_witness"]:
            common = max(common, check_spacing(r))
        check_ladder(r, common)
    assert len(data["rows"]) == 5 and sum(r["only_ladder_proved"] for r in data["rows"]) == 0
    port = data["port"]
    assert port["hard_accesses"] == hard
    fl = xm*frame-2*jitter
    rounded(port["aligned_frame_peak_pct_upper"], 4*100*(cr+cw)/fl)
    rounded(port["sliding_1400ns_peak_pct_upper"], 4*100*((cr+cw)/frame+1-fl/frame))
    check_table()
    print(f"{visits} x16 addresses, five calendars, both entrance cases for 37/38, probability bounds, cost, plateau edges and printed table verified.")


if __name__ == "__main__":
    main()
