"""Verify the deterministic read floors, candidate coverage and reported archive prices."""
import argparse
from fractions import Fraction as F
import json
from math import floor, ceil
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent


def data(path):
    return json.loads(path.read_bytes(), parse_float=F)


cal = data(EXP/"t186-native-ge30-x16/calendar.json")
clock_hi = F(cal["xi_max"])
clock_lo = F(cal["xi_min"])
ns = F(1, 10**9)
jitter = ns*F(cal["edge_jitter_ns"])
frame = cal["frame_ns"]*ns
aperture = clock_hi*cal["operation_ns"]["write_release"]*ns+3*jitter
cr_lo = clock_lo*cal["operation_ns"]["read_release_or_drive_write"]*ns-2*jitter
cr_hi = clock_hi*cal["operation_ns"]["read_release_or_drive_write"]*ns+2*jitter
geo = data(EXP/"c1-common-geo-20261109/six.json")
T, eps, delta = F(geo["T"]), F(1,1000), F(geo["delta_exec"])
c = F(38, geo["D"])
profiles = data(EXP/"t196-cluster-main-20261112/result.json")["profiles"]
plateau = data(EXP/"c1-common-geo-20261109/coverage.json")
old_folder = EXP/"t186-volume-archive"


def rounded(value, digits, upper):
    return F((ceil if upper else floor)(value*10**digits),10**digits)


def check_floor(kib, name, quote):
    # Invert the printed downward read floor to recover a unique integer K.
    w, a = kib*256, kib*512
    read_s = F(quote["fixed_read_floor_s"])
    estimate = w*(T/(2+read_s/((1-delta)*a*cr_lo))-2*jitter)
    K = round(estimate)
    cutoff = F(K,w)
    assert rounded((1-delta)*a*cr_lo*(T/(cutoff+2*jitter)-2),3,False) == read_s
    if name == "archive":
        peak, rise, second = F("0.525"), F(24), F(15624)
    else:
        peak, b = F(plateau["B_s_inv"]), F(plateau["b_s_inv"])
        duration = F(geo["plateau_s"])
        rise, second = peak-b, floor(duration*peak**2+(T-duration)*b**2)
    scan = frame*(a//4)
    dead = clock_hi*scan+aperture
    mean = F(6,5)
    p = F(37,38)
    overlap = F(16,25)*p+F(8,25)*2*p+F(1,25)*(2*p+1-F(1,38**2))
    missing = dead/cutoff
    mass = 2*K*c*peak/mean
    loss = dead*(peak**2+4*peak*rise)+(1+4*cutoff)*peak**2+cutoff*peak*rise
    bottom = (1-mass)*c*c*K*overlap*((1-missing)**2*second-loss)/(2*mean**2)
    assert 0 < missing < 1 and 0 < mass < 1 and bottom/(1+bottom)-delta > eps
    assert rounded(100*read_s/T,6,False) <= F(quote["fixed_read_floor_pct"])
    return K


def check_candidate(cfg, name):
    quote = cfg["classes"][name]
    d = profiles["geo" if name == "geo" else "reconstructions"]
    B, S1, S2 = (F(d[k]) for k in ("B","S1","S2"))
    w, a = cfg["words"], cfg["addresses"]
    L = frame*(a//4)
    p = quote["period_ns"]*ns
    assert (p/frame).denominator == 1
    def q(period):
        return delta + w*c*c*F(37,76)*((clock_hi*(period-L/2)+2*jitter+aperture)*S2+2*B*aperture*S1)
    assert q(p) <= eps < q(p+frame)
    assert rounded(q(p),12,True) == F(quote["fixed_Q_upper"])
    hard = 4*(ceil((T+2*jitter+aperture)/(clock_lo*frame))+2)
    ordinary = min(hard, a*(2+T/(clock_lo*p-2*jitter)))
    extra = delta*(hard-ordinary)
    stop = min(1, delta+w*c*c/2*(clock_hi*p+aperture)*(
        S2+aperture*(S2/(clock_lo*p)+B**2+4*B*F(d["U"]))))
    writes = min(ordinary+extra,(w+1)*c*S1+min(stop*hard,stop*ordinary+extra))
    assert rounded(cr_hi*(ordinary+extra+writes),3,True) == F(quote["fixed_s_upper"])
    assert F(quote["ladder"]["Q_upper"]) < eps


def format_number(value, places):
    return format(float(value), f",.{places}f").replace(",", " ").replace(".", ",")


labels = ["SEPEM 1996–2006","GOES East, 5 мин","GOES West, 5 мин",
          "G16 East, 1 мин","G16 West, 1 мин","G18 East, 1 мин","G18 West, 1 мин",
          "G19 East, 1 мин","G19 West, 1 мин"]


def cost_cell(policy, places):
    low, high = policy["busy_s"]["mean"]
    display = [format_number(x, places) for x in (low,high)]
    amount = display[0] if display[0] == display[1] else "–".join(display)
    pct = [format_number(x,6) for x in policy["mean_pct"]]
    return amount+" ("+(pct[0] if pct[0] == pct[1] else "–".join(pct))+"%)"


def table(kib):
    sets = [data(HERE/f"{p}-{kib}.json") for p in ("sepem","goes")]
    cfg = sets[0]["contract"]
    assert cfg == sets[1]["contract"]
    bounds = {k:check_floor(kib,k,v) for k,v in cfg["classes"].items()}
    for name in cfg["classes"]:
        check_candidate(cfg,name)
    rows = sets[0]["rows"]+sets[1]["rows"]
    old = data(old_folder/"sepem.json")["rows"]+data(old_folder/"goes.json")["rows"]
    assert len(rows) == len(old) == len(labels) == 9
    lines = [
        "| История | Средняя цена лестницы, с (%), SE в с | Верх цены лестницы, с (%) | Постоянный ГСО, среднее с (%) | Постоянный архивный, среднее с (%) | ГСО, к среднему / к верху | Архив, к среднему / к верху |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for title,row,prior in zip(labels,rows,old):
        h = row["history"]
        runs = row["policies"]
        stair = runs["ladder"]
        assert row["replications"] == 128 and row["name"] == prior["name"] and h == prior["history"]
        assert h["measured_s"]+h["unobserved_s"] == T
        if kib == 64:
            assert stair["busy_s"] == prior["runs"]["ladder"]["busy_s"]
            assert row["marks_sha256"] == prior["marks_sha256"]
            assert row["sample_sha256"]["archive"] == prior["sample_sha256"]["fixed_all_archives"]
        ratios = []
        for key in ("geo","archive"):
            policy = runs[key]
            q = cfg["classes"][key]
            f = F(q["fixed_read_floor_s"])
            nominal = cfg["scan_ns"]
            periods,rem = divmod(int(T)*10**9,q["period_ns"])
            frames,part = divmod(min(rem,nominal),cal["frame_ns"])
            read_ns = periods*cfg["addresses"]*100+400*frames
            read_ns += sum(min(100,max(0,part-o)) for o in cal["visit_offsets_ns"])
            assert policy["exact_read_ns"] == read_ns
            lo, hi = policy["busy_s"]["mean"]
            assert read_ns*ns <= lo <= hi
            lower = f/F(stair["analytic"]["s_upper"])
            assert rounded(lower,6,False) == F(policy["floor_over_history_upper_lower"])
            point = min(policy["floor_over_sample_ladder"])
            assert abs(point-f/max(stair["busy_s"]["mean"])) < F(1,10**9)
            ratios.append(format_number(point,3)+" / ≥"+format_number(rounded(lower,3,False),3))
        se = format_number(max(stair["busy_s"]["se"]),2)
        s = stair["analytic"]
        lines.append("| "+" | ".join([title,cost_cell(stair,2)+", "+se,
            format_number(s["s_upper"],3)+" ("+format_number(s["pct_upper"],6)+"%)",
            cost_cell(runs["geo"],2),cost_cell(runs["archive"],2),*ratios])+" |")
    return lines, bounds


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table",type=int,choices=(64,256))
    args = parser.parse_args()
    for kib, filename in ((64,"64KiB.md"),(256,"README.md")):
        lines, cutoffs = table(kib)
        if args.table == kib:
            print("\n".join(lines))
        elif args.table is None:
            printed = [s for s in (HERE/filename).read_text(encoding="utf-8").splitlines() if s.startswith("|")]
            assert lines == printed
            print(kib, "KiB: nine rows and class cutoffs (word seconds) verified:", cutoffs)
