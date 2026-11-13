"""Five closed native-ECC banks on one sequential GE30-45 service port (#504)."""
import argparse
import json
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path
from runpy import run_path


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "t186-native-cost-map"
ref = run_path(str(PRIOR / "calculate.py"))
geo, base = ref["GEO"], ref["BASE"]
T, c, delta = (ref[key] for key in ("T", "C", "DELTA"))
xm, xp, jitter, ns = (ref[key] for key in ("XM", "XP", "J", "NS"))
frame, read, write, hard = (ref[key] for key in ("FRAME", "READ", "WRITE", "HARD"))
up, down = ref["up"], ref["down"]
eps = F(1, 1000)
volumes = (F(1, 4), F(1, 2), F(1), F(2), F(4))


def resource_bounds():
    cal = base["CAL"]
    frame_min = xm*frame - 2*jitter
    n = len(cal["visit_offsets_ns"])
    full = read + write
    # In a physical window of one nominal frame, each phase stream may have
    # two partial visits. Consecutive starts of that phase are >= frame_min apart.
    sliding = n*(full + frame - frame_min)/frame
    return {
        "hard_accesses": hard,
        "read_or_extra_write_s_upper": str(read),
        "weak_word_aperture_s_upper": str(ref["DE"]),
        "nominal_frame_peak_pct": up(100*n*cal["operation_ns"]["write_release"]/F(cal["frame_ns"]), 6),
        "aligned_frame_peak_pct_upper": up(100*n*full/frame_min, 6),
        "sliding_1400ns_peak_pct_upper": up(100*sliding, 6),
        "select_preparation_ns_available_lower": down(
            (xm*(cal["frame_ns"]-cal["management_ns"][1])*ns-2*jitter)/ns, 4),
        "sample_path_ns_available_lower": down(
            (xm*cal["operation_ns"]["sample_dq_and_err"]*ns-2*jitter)/ns, 4),
    }


def half_mib_witness(ladder):
    block = next(b for b in ref["word_blocks"](ladder.words)
                 if b.subset == "all" and b.max_span == F(1, 4))
    aperture = ref["DE"]
    gap = xp*ladder.scan.L/2
    interior = gap-aperture
    visits = floor((block.span+aperture)/gap)+1
    free_squares = interior*(block.span-visits*aperture)-interior**2/2
    assert free_squares > 0
    hazard = block.blocks*max(0, block.first_factor*free_squares-block.intersections)
    lower = max(0, hazard/(1+hazard)-delta)
    return {"max_block_s": str(block.max_span), "blocks": block.blocks, "max_visits": visits,
            "gap_s": str(gap), "interior_s": str(interior),
            "sum_free_squares_s2_lower": down(free_squares, 15), "Q_lower": down(lower, 12)}


def fixed_ledger(ladder):
    prior = ref["fixed_floor"](ladder, eps)
    common = F(prior["fast_witness"]["Q_lower"])
    sharpened = None
    if ladder.words == 2**17:
        sharpened = half_mib_witness(ladder)
        common = max(common, F(sharpened["Q_lower"]))
    empty = prior["class_empty"] or common > eps
    candidate = ref["candidate"](ladder, eps)
    chosen = candidate or ref["fixed_price"](ladder, ladder.scan.L, geo)[1]
    p = F(chosen["period_s"])
    # Basic reads persist on every execution-correct path, even after two errors.
    reads_lower = (1-delta)*ladder.scan.addresses*(T/(xp*p+2*jitter)-2)
    spent_lower = reads_lower*ref["READ_LO"]
    q_low, _ = ref["word_floor"](ladder, xp*p)
    chosen = dict(chosen, Q_lower=down(max(common, q_low), 12), s_lower=down(spent_lower, 3),
                  pct_lower=down(100*spent_lower/T, 6))
    assert common <= F(chosen["physical_Q_upper"])
    assert not (empty and candidate)
    if empty:
        verdict = "excluded"
    else:
        verdict = "certified" if candidate else "open"
    return dict(prior_floor=prior, paired_spacing_witness=sharpened,
                common_Q_lower=down(common, 12), class_empty=empty,
                s_lower=None if empty else prior["s_lower"],
                pct_lower=None if empty else prior["pct_lower"],
                verdict=verdict, quote_is_candidate=bool(candidate), quote=chosen)


def row(volume):
    w = int(volume * 2**18)
    dies = 2 if volume == 4 else 1
    n = w//dies
    assert 2*n <= base["CAL"]["die_x16_addresses"]
    ladder = ref["Ladder"](w)
    scan, top = ladder.scan, ladder.levels[-1]
    top_real = xp*top + 2*jitter
    assert top_real <= 6 < xp*2*top+2*jitter
    assert xm*(scan.drain-scan.phase_max) >= ref["DE"]+2*jitter
    assert xm*(scan.L-scan.drain) >= xp*200*ns+2*jitter
    assert all(h >= p/F("0.00168") for h, p in zip(ladder.history, ladder.levels[1:]))

    fixed = fixed_ledger(ladder)
    cost, q = ladder.cost(geo, ref["MEAN"], ladder.eta)
    fast_prefix = xp*scan.L+jitter+(ladder.counts[0]+1)*top_real*(1+F(cost["true_cells_upper"]))
    fast_total = min(T, fast_prefix+q*T)
    witness = F(fixed["common_Q_lower"])
    assert witness <= q
    if witness > eps:
        ladder_verdict = "excluded"
    else:
        ladder_verdict = "certified" if q <= eps else "open"
    item = {
        "MiB": str(volume), "dies": dies, "words": w, "addresses_x16": scan.addresses,
        "words_per_die": n, "parent_rate_per_nu": str(w*c/ref["MEAN"]),
        "parent_rate_per_die_per_nu": str(n*c/ref["MEAN"]), "eta": str(ladder.eta),
        "L_local_s": str(scan.L), "levels_local_s": [str(p) for p in ladder.levels],
        "top_stride": int(top/scan.L), "top_same_address_s_upper": up(top_real, 12),
        "pair_gap_at_top_including_aperture_s_upper": up(xp*(top-scan.L/2)+2*jitter+ref["DE"], 12),
        "zero_cell_counts": ladder.counts, "fixed": fixed,
        "ladder": dict(cost, Q_lower=down(witness, 12), verdict=ladder_verdict,
                       fast_s_upper=up(fast_total, 3), fast_pct_upper=up(100*fast_total/T, 6)),
        "only_ladder_proved": fixed["class_empty"] and q <= eps,
    }
    if dies == 2:
        # One initial selection and <= four chip blocks in each potential scan.
        # Applications may select a different die between protection visits.
        item["block_selections_pathwise_upper_if_order_kept"] = 1+4*(ceil(T/(xm*scan.L-2*jitter))+2)
        item["protection_selections_pathwise_upper_any_tail"] = hard
    return item


def calculate():
    accepted = json.loads((PRIOR / "result.json").read_bytes())
    anchor = next(r for r in accepted["rows"] if r["scope"] == "geo"
                  and r["law"] == "compact_1p2" and r["words"] == 65536 and F(r["epsilon"]) == eps)
    rows = []
    for volume in volumes:
        item = row(volume)
        if volume == volumes[0]:
            for key, value in anchor["ladder"].items():
                assert item["ladder"][key] == value
            for key, value in anchor["fixed"].items():
                if key == "candidate":
                    assert all(item["fixed"]["quote"][k] == v for k, v in value.items())
                else:
                    assert item["fixed"]["prior_floor"][key] == value
        rows.append(item)
    return {"base": "a25d2236ba9fbec2c0084eb21b41472da3f33e68",
            "registration": "b6fa6ff66e955bff5a75359a4a0ba907de0118ac",
            "half_mib_edge_registration": "002e25000401a94e5bc59332a90be3639b582d25",
            "T_s": int(T), "epsilon_accumulation": str(eps), "delta_execution_assembly": str(delta),
            "GEO": {"background_s-1": str(ref["B0"]), "peak_s-1": str(geo.peak),
                    "S1": str(geo.exposure), "S2_s-1": str(geo.second),
                    "rise_s-1": str(geo.rise), "growth_s-2": base["C1"]["growth_s_inv2"]},
            "c": str(c), "mean_words_per_parent": str(ref["MEAN"]),
            "port": resource_bounds(), "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    path = HERE / "result.json"
    result = calculate()
    if parser.parse_args().check:
        assert result == json.loads(path.read_bytes())
        print("Five rows, including the accepted 0.25 MiB anchor, agree.")
    else:
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
