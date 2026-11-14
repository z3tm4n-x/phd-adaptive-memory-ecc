"""Assemble chapter 4 from the accepted ledgers. No particle histories are generated."""
import argparse
import json
from collections import Counter
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path
from runpy import run_path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent
BASE = "a5df64aab07ef149f3547479c6a5f96f5a3468e1"
GRID = "t186-native-cost-map/result.json"
PAIRS = "t186-pair-service-table/result.json"
HALF = "t525-two-phases/result.json"
PHASES = "t534-map-phases/result.json"
LARGE = "t504-large-bank/result.json"
ARCH = "t534-archive-comparison"
MIX = "compact_1p2"
EPS = "1/1000"
EPS_LABEL = {"1/10":"10⁻¹", "1/100":"10⁻²", EPS:"10⁻³", "1/10000":"10⁻⁴"}
DECISION = {"fixed":"П дешевле", "ladder":"Л дешевле", "overlap":"цены перекрываются",
            "fixed_only":"подтверждён П", "excluded":"оба исключены",
            "ladder_excluded":"Л исключена", "unknown":"выбор открыт"}
LAYOUT = {"half":"разнос L/2", "all":"любые пары", "covered":"≥21 007 пар",
          "closed":"любая замкнутая", "outside":"все снаружи", "partial":"частичный охват"}


def read(path):
    return json.loads((EXP / path).read_bytes())


def directed(value, places, upper=False):
    scale = 10**places
    n = (ceil if upper else floor)(F(value)*scale)
    return f"{n//scale}.{n%scale:0{places}d}" if places else str(n)


def decision(row):
    eps = F(row["epsilon"])
    if row.get("both_q_lower") and F(row["both_q_lower"]) > eps:
        return "excluded"
    if row.get("ladder_q_lower") and F(row["ladder_q_lower"]) > eps:
        return "ladder_excluded"
    if row["fixed_q_upper"] is None or F(row["fixed_q_upper"]) > eps:
        return "unknown"
    if row["ladder_q_upper"] is None or F(row["ladder_q_upper"]) > eps:
        return "fixed_only"
    if row["ratio_basis"] == "pointwise" and F(row["ratio_lower"]) > 1:
        return "ladder"
    if F(row["fixed_lower_s"]) > F(row["ladder_upper_s"]):
        return "ladder"
    if row["ladder_lower_s"] and F(row["fixed_upper_s"]) < F(row["ladder_lower_s"]):
        return "fixed"
    return "overlap"


def finish(row):
    row["decision"] = decision(row)
    if row["ratio_basis"] != "pointwise":
        row.pop("ratio_lower", None)
    if row["ratio_basis"] == "pointwise":
        # The published ratio is the minimum of per-map comparisons.
        assert row["decision"] == "ladder" and row["ratio_lower"]
    elif row["decision"] == "ladder":
        row["ratio_lower"] = directed(F(row["fixed_lower_s"])/F(row["ladder_upper_s"]), 6)
    elif row["decision"] == "fixed":
        row["ratio_lower"] = directed(F(row["ladder_lower_s"])/F(row["fixed_upper_s"]), 6)
    return row


def accepted_row(old, index):
    fixed, stair = old["fixed"], old["ladder"]
    cand = fixed["candidate"] or {}
    kib = old["words"] // 256
    row = dict(id=f"{old['scope']}-{kib}-{old['epsilon'].split('/')[1]}-{old['law']}",
               kib=kib, layout="half", scope=old["scope"], law=old["law"], m=old["m"],
               epsilon=old["epsilon"], u_upper=old["u_upper"], eta=old["eta"],
               visibility_481=old["threshold"], u_test_lower_481=old["u_test_boundary_lower"],
               u_test_lower=old["u_test_boundary_lower"], fixed_period_s=cand.get("period_s"),
               fixed_q_upper=cand.get("physical_Q_upper"), fixed_lower_s=fixed["s_lower"],
               fixed_upper_s=cand.get("s_upper"), ladder_q_upper=stair["q"],
               ladder_lower_s=stair["s_lower"], ladder_upper_s=stair["s_upper"],
               ratio_basis="single_map", sources=[f"{GRID}#/rows/{index}"])
    if fixed["class_empty"]:
        row["both_q_lower"] = fixed["fast_witness"]["Q_lower"]
        row["infeasible_L_tariff"] = fixed["continuous_tariff"]
    return finish(row)


def grid_and_slice(base, half):
    primary, transverse = [], []
    scan = base["maps"][str(half["word_count"])]
    assert base["T_s"] == 315576000 and F(base["delta_exec"]) == F(6, 10**6)
    assert scan["L_s"] == half["local_scan_s"] and scan["zero_cells"] == half["zero_cell_counts"]
    for i, old in enumerate(base["rows"]):
        row = accepted_row(old, i)
        if old["scope"] == "geo" and old["law"] == MIX:
            row["decision_481"] = row["decision"]
            if row["kib"] == 256:
                assert F(row["eta"]) == F(half["visibility_parents_per_inversion"])
                assert row["ladder_q_upper"] == half["old_stop_upper"]
                row.update(ladder_q_upper=half["stop_upper_also_bounds_physical_Q"],
                           ladder_q_lower=half["physical_Q_lower_from_plateau"],
                           ladder_lower_s=half["price_s_lower"], ladder_upper_s=half["price_s_upper"])
                # Reconstruct a *lower* bound on the numerator from its issued ceiling.
                q_cont_lo = F(old["continuous_Q_upper"]) - F(1, 10**12)
                row["u_test_lower"] = directed(q_cont_lo/F(row["ladder_q_upper"]), 9)
                row["sources"].append(HALF)
            primary.append(finish(row))
        if row["kib"] == 128 and row["epsilon"] == EPS:
            transverse.append(row.copy())
    assert [(r["kib"], r["epsilon"]) for r in primary] == [
        (kib, eps) for kib in (64, 128, 256) for eps in EPS_LABEL]
    assert len(transverse) == 10
    return primary, transverse


def map_rows():
    pairs = read(PAIRS)
    rows = []
    for kib, layout, key in ((64, "all", "all_maps"), (128, "all", "all_maps"),
                             (128, "covered", "W_at_most_44529")):
        a = str(512*kib)
        for scope in ("geo", "archive"):
            src = pairs[a][scope][key]
            rows.append(finish(dict(id=f"{scope}-{kib}-{layout}", kib=kib, layout=layout,
                scope=scope, law=MIX, m="6/5", epsilon=EPS, u_upper=src["continuous_q_over_epsilon_upper"],
                fixed_period_s=pairs[a]["period_fixed_s"], fixed_q_upper=src["fixed_q_upper"],
                fixed_lower_s=src["fixed_lower_s"], fixed_upper_s=src["fixed_candidate_upper_s"],
                ladder_q_upper=src["q_upper"], ladder_lower_s=None, ladder_upper_s=src["stairs_upper_s"],
                ratio_basis="pointwise", ratio_lower=src["same_map_ratio_lower"],
                quarter_geo_upper=pairs[a]["geo"][key]["continuous_q_over_epsilon_upper"],
                extra_2x_s=src["same_map_extra_room_s_lower"], sources=[f"{PAIRS}#/{a}/{scope}/{key}"])))
    assert int(a) - pairs[a]["geo"]["quarter_max_W"] == 21007
    return rows


def archive_and_geometry(primary, transverse, phase, map_comparisons):
    rows = []
    for kib in (64, 128, 256):
        if kib == 128:
            row = next(r.copy() for r in transverse if r["law"] == MIX and r["scope"] == "reconstructions")
            row["scope"] = "archive"
            row["id"] = "archive-128-half"
            # A necessary lower bound for EVERY map also holds on this member.
            # Its published pointwise ratio belongs to a different comparison.
            universal = next(r for r in map_comparisons if r["kib"] == kib and r["scope"] == "archive"
                             and r["layout"] == "all")
            row["fixed_lower_s"] = max(row["fixed_lower_s"], universal["fixed_lower_s"], key=F)
            row["sources"] = [*row["sources"], *universal["sources"]]
        else:
            path = f"{ARCH}/sepem-{kib}.json"
            contract = read(path)["contract"]
            main = next(r for r in primary if r["kib"] == kib and r["epsilon"] == EPS)
            g, a = (contract["classes"][c] for c in ("geo", "archive"))
            assert (contract["words"], contract["addresses"]) == (256*kib, 512*kib)
            assert (main["fixed_lower_s"], main["ladder_upper_s"]) == (g["fixed_read_floor_s"], g["ladder"]["s_upper"])
            row = dict(id=f"archive-{kib}-half", kib=kib, layout="half", scope="archive",
                       law=MIX, m="6/5", epsilon=EPS, u_upper=None,
                       fixed_period_s=str(F(a["period_ns"], 10**9)), fixed_q_upper=a["fixed_Q_upper"],
                       fixed_lower_s=a["fixed_read_floor_s"], fixed_upper_s=a["fixed_s_upper"],
                       ladder_q_upper=a["ladder"]["Q_upper"], ladder_lower_s=None,
                       ladder_upper_s=a["ladder"]["s_upper"], ratio_basis="single_map",
                       sources=[f"{path}#/contract/classes/archive"])
            if kib == 256:
                witness = phase["archive_fixed"]
                assert row["fixed_lower_s"] == witness["old_compulsory_reads_s_lower"]
                row["fixed_lower_s"] = witness["compulsory_reads_s_lower"]
                row["sources"].append(PHASES+"#/archive_fixed")
        rows.append(finish(row))

    fixed, growth = phase["closed_fixed_class"], phase["one_phase_growth"]
    model = run_path(str(EXP / "t186-native-cost-map/calculate.py"))
    rule = model["Ladder"](phase["words_closed"])
    period = F(fixed["one_phase_candidate_s"])
    assert rule.scan.addresses == phase["addresses"]
    assert model["up"](model["physical"](rule.scan, rule.words, period, both=False), 12) == fixed["candidate_Q_upper"]
    # Only the fixed-calendar read/write tariff is independent of the pairing.
    # Discard fixed_price's two-phase Q. The one-phase Q above qualifies this P.
    fee, _ = model["fixed_price"](rule, period, model["GEO"])
    row = dict(id="geo-256-closed", kib=256, layout="closed", scope="geo", law=MIX, m="6/5",
               epsilon=EPS, u_upper=directed(F(fixed["continuous_Q_upper"])/F(EPS), 9, True),
               fixed_period_s=fixed["one_phase_candidate_s"], fixed_q_upper=fixed["candidate_Q_upper"],
               fixed_lower_s=fixed["per_map_constant_reads_s_lower"], fixed_upper_s=model["up"](fee, 3),
               ladder_q_upper=growth["closed_one_phase_stop_upper"], ladder_lower_s=None,
               ladder_upper_s=growth["closed_bus_s_upper_I0_X0"], ratio_basis="pointwise",
               ratio_lower=fixed["per_map_ratio_lower"], sources=[PHASES+"#/closed_fixed_class",
                   PHASES+"#/one_phase_growth", "t186-native-cost-map/calculate.py#fixed_price"])
    rows.append(finish(row))
    # Every adopted reconstruction lies inside GEO (#459). Restriction preserves
    # both upper bounds and the sufficient candidate, but NOT the GEO fixed floor.
    coverage = "t186-ost-geo-3g/result.json"
    assert read(coverage)["archive"]["conditional_class_covers"]
    arc = dict(row, id="archive-256-closed", scope="archive", u_upper=None,
               fixed_lower_s=phase["archive_fixed"]["compulsory_reads_s_lower"],
               ratio_basis="uniform_on_each_map", sources=row["sources"]+[
                   PHASES+"#/archive_fixed", coverage+"#/archive/conditional_class_covers"])
    rows.append(finish(arc))
    for layout in ("outside", "partial"):
        outside = layout == "outside"
        rows.append(finish(dict(id="geo-256-"+layout, kib=256, layout=layout, scope="geo", law=MIX,
            m="6/5", epsilon=EPS, u_upper=None, fixed_period_s=None, fixed_q_upper=None,
            fixed_lower_s=None, fixed_upper_s=None, ladder_lower_s=None, ladder_upper_s=None,
            ladder_q_lower=phase["all_external_physical_lower"] if outside else None,
            ladder_q_upper=phase["all_external_one_phase_upper"] if outside else phase["all_maps_one_phase_upper"],
            ratio_basis=None, sources=[PHASES+"#/all_external_physical_lower" if outside else
                                       PHASES+"#/all_maps_one_phase_upper"])))
    return rows


def checked_small_banks(primary):
    """Test the published two-phase and growth inequalities on the two smaller calendars."""
    model = run_path(str(EXP / "t525-two-phases/calculate.py"))
    ref = model["ref"]
    issued = read(PHASES)["one_phase_growth"]
    assert ref["up"](growth_at(ref["Ladder"](65536), ref), 12) == issued["closed_one_phase_stop_upper"]
    costs = run_path(str(EXP / "native-service-robustness-20261113/check_theory.py"))["costs"]
    out = {}
    for kib in (64, 128):
        w = kib*256
        rule = ref["Ladder"](w)
        # A shift by W visits preserves the in-frame slot. The last younger phase
        # is L/2 - 640 ns. The first clean history ends before the first skipped pass.
        assert w % 4 == 0 and rule.scan.L == (w//2)*ref["FRAME"]
        assert (w//4-1)*ref["FRAME"]+760*ref["NS"] == rule.scan.L/2-640*ref["NS"]
        assert min(rule.counts) >= 1 and min(rule.history) > 0
        q_pair = sum(model["two_phase_risk"](rule, ref["GEO"]))
        q_rise = growth_at(rule, ref)
        result = {}
        for name, q in (("half_phase", q_pair), ("one_phase_growth", q_rise)):
            price = costs(rule, w, ref["GEO"], q, False)
            low = (1-q)*2*w*ref["READ_LO"]*(ref["T"]/(ref["XP"]*rule.levels[-1]+2*ref["J"])-2)
            result[name] = dict(q_upper=ref["up"](q, 12), lower_s=ref["down"](low, 3),
                                upper_s=ref["up"](price, 3))
        best_bound = min(result.values(), key=lambda x: F(x["q_upper"]))
        for row in (x for x in primary if x["kib"] == kib):
            # This transfer checks category stability. Keep the original accepted
            # numbers as the chapter's reference for these two volumes.
            best = dict(row, ladder_q_upper=min(row["ladder_q_upper"], best_bound["q_upper"], key=F),
                        ladder_lower_s=max(row["ladder_lower_s"], best_bound["lower_s"], key=F),
                        ladder_upper_s=min(row["ladder_upper_s"], best_bound["upper_s"], key=F))
            assert decision(best) == row["decision"]
        out[str(kib)] = result
    return out


def growth_at(rule, ref):
    """Apply (1)–(2) of #540 with this calendar's W, visibility, phases and thresholds."""
    geo = ref["GEO"]
    B = geo.peak
    rate = rule.words*ref["C"]*rule.eta
    step = ref["XP"]*rule.levels[-1]
    phase = ref["XP"]*rule.scan.phase_max
    width = ref["XM"]*rule.levels[-1]
    slope = F(ref["BASE"]["C1"]["growth_s_inv2"])
    local_floor = B/2-slope*(2*step+phase+ref["DE"])
    accumulated = B/2*(B/(4*slope)-step)
    z = rate*local_floor*width
    discount = min(z/(1+z), 1-rate*B*width)
    assert min(rule.history) > width and local_floor > 0 and accumulated > 0 and 0 < discount < 1

    def fee(peak):
        mass = peak*step
        return mass/(1-ref["weight"](rate*mass))

    high = (1-discount)*(fee(B)+B*phase)
    mid_fee = fee(3*B/4)
    low = mid_fee+(fee(B)-mid_fee)*ref["weight"](rate*accumulated)+B*phase
    rise = rule.words*ref["C"]**2/2*geo.rise*sum(rule.amplitude)*max(high, low)
    return sum(rule.risk(rule.eta, geo)[:3])+rise


def collection():
    primary, transverse = grid_and_slice(read(GRID), read(HALF))
    supplement = map_rows()
    supplement.extend(archive_and_geometry(primary, transverse, read(PHASES), supplement))
    assert len({r["id"] for r in primary+supplement}) == len(primary)+len(supplement)
    for r in primary+supplement:
        for key in ("fixed", "ladder"):
            lo, hi = r[key+"_lower_s"], r[key+"_upper_s"]
            assert not (lo and hi) or 0 < F(lo) <= F(hi) <= 315576000
    changes = [r["id"] for r in primary if r["decision_481"] != r["decision"]]
    assert changes == ["geo-256-1000-compact_1p2"]
    assert Counter(r["decision"] for r in primary) == dict(fixed=2, ladder=5, overlap=2, fixed_only=2, excluded=1)
    volumes = {}
    for row in read(LARGE)["rows"][1:]:
        assert row["fixed"]["class_empty"] and row["fixed"]["common_Q_lower"] == row["ladder"]["Q_lower"]
        volumes[row["MiB"]] = row["fixed"]["common_Q_lower"]
    return dict(base=BASE, horizon_s=315576000, primary=primary, map_and_archive=supplement,
                transverse=transverse, changed=changes, paired_checks_other_banks=checked_small_banks(primary),
                larger_half_maps_Q_lower=volumes)


def number(value, places=0, upper=False):
    s = directed(value, places, upper)
    left, _, right = s.partition(".")
    return f"{int(left):,}".replace(",", " ") + (","+right if right else "")


def table(data):
    lines = ["| КиБ · карта | Класс · ε | u⁺ | Период П, мс | Q П / Л | П, с | Л, с | Выбор · ≥ раз |",
             "|---|---|---:|---:|---|---:|---:|---|"]
    for i, row in enumerate(data["primary"] + data["map_and_archive"]):
        if i == len(data["primary"]):
            lines.append("| **Допуск 10⁻³. Область действия и класс соперника** | | | | | | | |")
        def interval(lo, hi):
            if lo and hi:
                return number(lo)+"–"+number(hi, upper=True)
            if hi:
                return "≤"+number(hi, upper=True)
            return "≥"+number(lo) if lo else "—"
        p = row["fixed_period_s"]
        p = number(F(p)*1000, 4).rstrip("0").rstrip(",") if p else "—"
        qf = "≤"+row["fixed_q_upper"].replace(".", ",") if row["fixed_q_upper"] else "—"
        qa = "≤"+row["ladder_q_upper"].replace(".", ",")
        if row.get("both_q_lower"):
            qf = "≥"+row["both_q_lower"].replace(".", ",")
            qa = qf
        if row.get("ladder_q_lower") and row["layout"] == "outside":
            qa = "≥"+row["ladder_q_lower"].replace(".", ",")
        u = number(row["u_upper"], 6, True) if row["u_upper"] else "—"
        if row.get("quarter_geo_upper") is not None or (
                row["scope"] == "geo" and row["epsilon"] == EPS and row["u_upper"]):
            cap = row.get("quarter_geo_upper", row["u_upper"])
            u += "<br>¼ " + ("есть" if F(cap) <= F(1,4) else "не подтв.")
        fl = interval(row["fixed_lower_s"], row["fixed_upper_s"])
        al = interval(row["ladder_lower_s"], row["ladder_upper_s"])
        status = DECISION[row["decision"]]
        if row.get("ratio_lower"):
            status += " · "+number(row["ratio_lower"], 4)+"×"
        layout = LAYOUT[row["layout"]]
        if row["layout"] == "all" or row["layout"] == "covered":
            layout += " · смесь"
        lines.append("| "+" | ".join([f"{row['kib']} · {layout}",
            ("ГСО" if row["scope"]=="geo" else "Рек.")+" · "+EPS_LABEL[row["epsilon"]],
            u, p, qf+" / "+qa, fl, al, status])+" |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify data, Markdown table and figure")
    args = parser.parse_args()
    data = collection()
    doc = HERE / "README.md"
    start, end = "<!-- table -->", "<!-- /table -->"
    raw = doc.read_text(encoding="utf-8")
    before, middle = raw.split(start)
    _, after = middle.split(end)
    from figure import draw
    outputs = {doc: (before+start+"\n\n"+table(data)+"\n\n"+end+after).encode(),
               HERE/"map.json": (json.dumps(data, ensure_ascii=False, indent=2)+"\n").encode(),
               HERE/"map.svg": draw(data)}
    for path, content in outputs.items():
        if args.check:
            if path.read_bytes().replace(b"\r\n", b"\n") != content:
                raise SystemExit(f"Rebuild {path.name}")
        else:
            path.write_bytes(content)
    print("12 GEO rows, 10 visibility comparisons, both fixed classes and all map variants verified.")


if __name__ == "__main__":
    main()
