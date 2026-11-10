"""One c01 point, three unchanged calendars and three bank-lifetime direct budgets."""
import argparse
from decimal import Decimal
from fractions import Fraction as F
from hashlib import sha256
import json
from math import ceil, floor
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GRID = ROOT / "experiments/regime-map-methodology-20261019/predictability-volume-20261028"
sys.path.insert(0, str(GRID / "map-14"))
from run import GridPoint, load as load_cells

D1 = ROOT / "theory/t413-parent-marks-d1-20261109.md"
D2 = ROOT / "experiments/t413-cy62167-placement-d2/handoff.json"
M = ROOT / "theory/t196-c01-direct-certificate-20261029/result.json"
CUT = ROOT / "experiments/t331-window-reset-20261030/result.json"
N0 = ROOT / "theory/t196-n0-map-diagnosis-20261028-result.json"
NS = 10**9


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return sha256(path.read_bytes().replace(b"\r\n",b"\n")).hexdigest()


def c01():
    cell = next(c for c in load_cells()["cells"] if c["id"] == "c01")
    p = GridPoint(cell)
    handoff = read(D2)
    data = handoff["D3_input"]
    assert (p.W,p.T,p.alpha,p.eps) == (data["W"],data["T_s"],0,F(data["epsilon"]))
    assert (p.W,p.T,p.eps,p.D) == (1048576,315576000,F(1,1000),data["reference_bit_count"])
    assert p.D == 38*524288 and p.Fr == 0 and p.K == F(p.W*39*38,2*p.D**2)
    assert p.b*p.T+p.Fs == F(data["S1_reference"]) and p.Fparents == F(data["F_b39_inversions"])
    assert handoff["test_derived_lifetime_upper"] is None
    budgets = [F(a["D1_upper_parents_per_bank_T"]) for a in data["anchors"]]
    assert budgets == [0,F(1,10**5),F(1,10**4)]
    assert all(a["status"] == "CONDITIONAL" and not a["is_test_derived"] for a in data["anchors"])
    assert (p.delta0,p.deltacal,p.delta) == (F(6,10**6),F(1,10**6),F(7,10**6))
    return p,budgets


def geometry(p, name, fast, slow, guarded):
    """Pair contribution on the guaranteed deterministic supports of this rule."""
    ph,pl = p.P(fast),p.P(slow)
    ah,al = ph+p.dE,pl+p.dE
    hold = p.hold(fast,guarded)
    assert slow % fast == 0 and p.W % 8 == 0
    pad = p.hp+p.delay+p.freeze+2*p.et
    edge_width = edge_integral = F(0)
    if guarded:
        assert hold["lower_s"] >= ah
    else:
        assert hold["ticks"] == 0
        edge_width = ah+2*pad
        rise = F(p.c["environment"]["template"]["rise_s"])
        assert 0 < edge_width < rise == p.width/2
        slope = p.a/rise
        edge_integral = 2*p.N*(p.b**2*edge_width + p.b*slope*edge_width**2
                               + slope**2*edge_width**3/3)
    round_s = F(196*p.W,NS)
    assert p.left > al and p.T-(p.left+(p.N-1)*p.cycle+p.width) > al
    ordinary = p.K*(ah*p.IH+al*p.IL)
    mixed = p.K*p.XE
    boundary = p.K*(al-ah)*edge_integral
    return dict(name=name, pair=[fast,slow], guarded=guarded,hold=hold,
                periods_nominal_s=[fast*round_s,slow*round_s],periods_upper_s=[ph,pl],
                C0_s=pad,edge_width_s=edge_width,edge_squared_integral=edge_integral,
                ordinary_pairs=ordinary,aperture_pairs=mixed,boundary_pairs=boundary,
                accumulation_upper=ordinary+mixed+boundary)


def verify_sources(p, methods):
    """Three independently saved baseline certificates, including both physical edges."""
    m,cut,n0 = read(M),read(CUT),read(N0)
    v = {k:F(x["exact"]) for k,x in cut["values"].items()}
    n = n0["rows"]["c01"]
    base = [F(m["Q_upper"]),v["physical_Q_upper"],F(n["Q_upper"])]
    assert [g["pair"] for g in methods] == [m["periods"],[cut["kH"],cut["kL"]],n["pair"]]
    assert all(x == p.delta for x in (F(m["delta"]),v["Delta"],F(n0["delta"])))
    for g,q in zip(methods,base):
        assert g["accumulation_upper"]+p.delta == q
    assert methods[0]["ordinary_pairs"] == F(m["ordinary_pair_expectation_upper"])
    assert methods[0]["aperture_pairs"] == F(m["aperture_cross_expectation_upper"])
    assert methods[0]["accumulation_upper"] == F(m["EV0_upper"])
    assert methods[1]["boundary_pairs"] == v["D_boundary_upper_correction"]
    assert methods[1]["edge_width_s"] == v["sigma_s"]
    assert v["physical_Q_upper"] == v["L_cut_fictitious_upper"]+v["D_boundary_upper_correction"]
    assert methods[2]["boundary_pairs"] == F(n["boundary_penalty"])
    assert methods[2]["aperture_pairs"] == F(n["E_mixed"])
    assert methods[2]["edge_width_s"] == F(n["strip_s"])
    assert methods[2]["periods_upper_s"] == [F(n["period_high_upper_s"]),F(n["period_low_upper_s"])]
    # Reproduce published bus and serial prices at the original map Q of each
    # stored execution. The new table uses the physical Q of each D3 row.
    saved = read(GRID/"map-14/result.json")["cells"]["c01"]
    for g in (methods[0],methods[2]):
        old = saved["methods"][g["name"]]
        price = p.price(*g["pair"],F(old["Q_upper"]),g["guarded"])
        ref = saved["price_bounds"][old["price"]]["price"]
        for coord in ("bus","serial"):
            assert price["coordinates"][coord]["protection_upper_s"] == F(ref["coordinates"][coord]["protection_upper_s"])


def calculate():
    p,budgets = c01()
    methods = [geometry(p,"M",26,208,True),geometry(p,"L_cut",26,208,False),
               geometry(p,"N0",15,120,False)]
    verify_sources(p,methods)
    rows = []
    for d in budgets:
        for g in methods:
            accum = g["accumulation_upper"]
            direct = d                         # P(N_B >= 1) <= E N_B <= d
            total = min(F(1),accum+p.delta+direct)
            price = p.price(*g["pair"],total,g["guarded"])
            repairs = min(price["reads_upper"],2*p.Fparents+total*p.Nmax)
            assert repairs == price["repairs_upper"]
            assert price["full_started_tail_paid"] and price["work_after_first_failure_paid"]
            cost = {coord:price["coordinates"][coord]["protection_upper_s"] for coord in ("bus","serial")}
            rows.append(dict(D1_upper=d,rule=g["name"],accumulation_upper=accum,
                             exceptions=p.delta,direct_upper=direct,Q_upper=total,
                             margin=p.eps-total,certified=(total <= p.eps),
                             reads_upper=price["reads_upper"],repairs_upper=repairs,known_protection_s=cost))
    paths = (D1,D2,M,CUT,N0,GRID/"inputs.json",GRID/"resource-result.json",GRID/"first_point.py",
             GRID/"map-14/inputs.json",GRID/"map-14/result.json",GRID/"map-14/run.py")
    return dict(base_main="840144d6858cb7d483a5499e0c34a606cf2cba67",cell="c01",words=p.W,
                mission_s=p.T,alpha=p.alpha,epsilon=p.eps,reference_positions=p.D,
                S1_ref=p.b*p.T+p.Fs,expected_bit_inversions=p.Fparents,
                squared_integral_in_windows=p.IH,squared_integral_outside=p.IL,
                pair_coefficient=p.K,dE_s=p.dE,delta_exec=p.delta0,delta_calendar=p.deltacal,
                maximum_word_reads=p.Nmax,read_bus_upper_s=p.unit["bus_read"]["upper"],
                read_serial_upper_s=p.unit["serial_read"]["upper"],repair_upper_s=p.unit["repair"]["upper"],
                calendars=methods,rows=rows,source_sha256_LF={x.relative_to(ROOT).as_posix():digest(x) for x in paths})


def decimal(value, places, upper):
    ticks = (ceil if upper else floor)(value*10**places)
    return format(Decimal(ticks).scaleb(-places),f".{places}f").replace(".",",")


def table(data):
    lines = ["| d за срок | Режим | Частый / редкий период, с | Накопление | Исключения | Прямые | Q⁺ | Запас | Шина / последовательно, с | Допуск |",
             "|---:|---|---|---:|---:|---:|---:|---:|---:|---|"]
    modes = {g["name"]:g for g in data["calendars"]}
    for r in data["rows"]:
        g = modes[r["rule"]]
        periods = " / ".join(decimal(x,9,True).rstrip("0").rstrip(",") for x in g["periods_nominal_s"])
        # Probability columns are in 1e-6, outward rounding is done after all sums.
        upper_micro = [decimal(r[k]*10**6,6,True) for k in ("accumulation_upper","Q_upper")]
        budget = {F(0):"0",F(1,10**5):"10⁻⁵",F(1,10**4):"10⁻⁴"}[r["D1_upper"]]
        cost = " / ".join(format(ceil(r["known_protection_s"][k]),",").replace(","," ") for k in ("bus","serial"))
        columns = [budget,f'{g["name"]}({g["pair"][0]},{g["pair"][1]})',periods,upper_micro[0],
                   str(r["exceptions"]*10**6),str(r["direct_upper"]*10**6),upper_micro[1],
                   decimal(r["margin"]*10**6,6,False),cost,"подтверждён" if r["certified"] else "верх выше ε"]
        lines.append("| "+" | ".join(columns)+" |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write",action="store_true",help="write this experiment's result.json")
    action.add_argument("--table",action="store_true",help="print the nine rows")
    action.add_argument("--check",action="store_true",help="verify the saved results and published table (default)")
    args = parser.parse_args()
    data = calculate()
    path = HERE/"result.json"
    serialized = json.dumps(data,indent=2,ensure_ascii=False,default=str)+"\n"
    if args.write:
        path.write_text(serialized,encoding="utf-8",newline="\n")
    elif args.table:
        print(table(data))
    else:
        if path.read_text(encoding="utf-8") != serialized:
            raise ValueError("Exact D3 results differ")
        if table(data) not in (HERE/"README.md").read_text(encoding="utf-8"):
            raise ValueError("D3 report table differs")
        print("PASS: three accepted baseline certificates, nine exact rows, risk, price and table.")


if __name__ == "__main__":
    main()
