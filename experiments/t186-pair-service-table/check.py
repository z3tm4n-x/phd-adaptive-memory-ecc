"""Engineering check of the unknown-partner rows from PR 488, including service and costs."""

import argparse
import json
import subprocess
from fractions import Fraction as F
from pathlib import Path
from runpy import run_path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
THEORY = "279181a12a1955f14946fad83ec2728cd50ada7f"
THEORY_FILE = "experiments/native-service-robustness-20261113/check_theory.py"
M = run_path(str(EXP / "t186-native-cost-map/calculate.py"))
T, C, DELTA, XP, XM, J, DE = (M[k] for k in ("T", "C", "DELTA", "XP", "XM", "J", "DE"))
READ, WRITE, HARD, EPS = M["READ"], M["WRITE"], M["HARD"], F(1, 1000)
UP, DOWN = M["up"], M["down"]
CAL = M["BASE"]["CAL"]


def read_floor_witness(a, lo, hi, dead, witness, printed):
    # Recover the integer K independently from the rounded necessary price;
    # then test the two-parent bound for every P >= K/W, not just P = K/W.
    scale = (1 - DELTA) * a * M["READ_LO"]
    k = round(T * lo / (F(printed) / scale + 2) - 2 * J * hi)
    peak, variation, second = witness
    m = F(6, 5)
    p = F(37, 38)
    overlap = (36*p - p*p) / 25
    period_cap = F(k, lo)
    removed = dead * hi / k
    double_hit_mean = 2 * k * C * peak / m
    assert max(removed, double_hit_mean) < 1
    loss = dead*(peak**2 + 4*peak*variation) + (1+4*period_cap)*peak**2 + period_cap*peak*variation
    free_exposure = (1-removed)**2 * second - loss
    z = (1-double_hit_mean) * C*C*k*overlap*free_exposure / (2*m*m)
    excluded = z/(1+z) - DELTA
    floor = scale*(T*lo/(k + 2*J*hi) - 2)
    assert excluded > EPS and DOWN(floor, 3) == printed
    return k, floor, excluded


def check_block(theory, a, lo, hi, name, env, issued):
    ladder = theory["AnyPairs"](lo, a)
    period = F("0.0934444") if a == 32768 else F("0.0458752")
    assert period % M["FRAME"] == 0 and period >= ladder.scan.L
    # Reconstruct the effective read phases from the four actual pin starts in each frame.
    phase_last = F((a//4 - 1)*CAL["frame_ns"] + CAL["visit_offsets_ns"][-1], 10**9)
    assert phase_last == ladder.scan.phase_max and phase_last + DE / XP <= ladder.scan.L
    eta = (5*lo-4) / F(6*lo)
    q = DELTA + sum(ladder.risk(eta,env)[1:])*F(hi,lo)
    assert UP(q, 12) == issued["q"]
    for w in {lo, (lo+hi)//2, hi}:
        exact = theory["AnyPairs"](w, a)
        assert sum(exact.risk(exact.eta,env)) <= q
    gates = ((ladder.fast+2*J) * (env.exposure/(XM*ladder.levels[-1]) + 2*(env.peak+env.rise)))
    fixed_q = M["physical"](ladder.scan, hi, period, both=False, env=env)
    assert UP(fixed_q,12) == issued["fixed_candidate_q"] and fixed_q <= EPS
    fixed, _ = M["fixed_price"](theory["AnyPairs"](hi, a), period, env)
    assert UP(fixed,3) == issued["fixed_candidate_s_upper"]
    hits = (hi + 1)*C*env.exposure
    cells = min(hits, hi*C*(env.exposure+min(env.exposure,gates))/F(6,5))
    first, fee = ladder.fees
    port = first + fee*(1+cells) + WRITE*hits + (READ+WRITE)*HARD*q
    assert UP(port,3) == issued["stairs_s"]
    k, floor, excluded = read_floor_witness(a,lo,hi,ladder.fast,theory["WITNESSES"][name],issued["fixed_s_min"])
    assert DOWN(floor/port,4) == issued["fixed_over_stairs_lower"]
    return dict(lo=lo,hi=hi,q=q,port=port,floor=floor,fixed=fixed,fixed_q=fixed_q,
                ratio=floor/port,room=floor/2-port,fee=fee,cap=k,excluded=excluded)


def summarize(blocks, scan, wmax, env):
    qq = M["physical"](scan,wmax,scan.L,both=False,env=env)
    return {
        "q_upper": UP(max(r["q"] for r in blocks),12),
        "fixed_q_upper": UP(max(r["fixed_q"] for r in blocks),12),
        "continuous_q_over_epsilon_upper": UP(qq/EPS,6),
        "fixed_lower_s": DOWN(min(r["floor"] for r in blocks),3),
        "fixed_candidate_upper_s": UP(max(r["fixed"] for r in blocks),3),
        "stairs_upper_s": UP(max(r["port"] for r in blocks),3),
        "same_map_ratio_lower": DOWN(min(r["ratio"] for r in blocks),4),
        "same_map_extra_room_s_lower": DOWN(min(r["room"] for r in blocks),3),
        "reset_fee_s_upper": UP(blocks[0]["fee"],6),
    }


def result(source):
    # Pin the actual file contents, including a dirty checkout; use Git LF normalization.
    rel = Path(THEORY_FILE)
    expected = subprocess.check_output(["git","show",f"{THEORY}:{rel.as_posix()}"],cwd=source)
    if expected.replace(b"\r\n",b"\n") != (source/rel).read_bytes().replace(b"\r\n",b"\n"):
        raise ValueError("Theory source differs from PR 488")
    if subprocess.check_output(["git","rev-parse","HEAD"],cwd=source,text=True).strip() != THEORY:
        raise ValueError("Use a checkout at the specified PR 488 commit")
    theory = run_path(str(source/rel))
    # Compare both cache orders with separate evaluations of the source formula.
    pairs = theory["AnyPairs"]
    short, long = pairs(32768,32768), pairs(32768,65536)
    raw = pairs.risk.__wrapped__
    witness = {"32768_addresses":UP(sum(raw(short,short.eta,M["GEO"])),12),
               "65536_addresses":UP(sum(raw(long,long.eta,M["GEO"])),12)}
    assert short != long and short.scan.L != long.scan.L and len(set(witness.values())) == 2
    for order in ((short,long),(long,short)):
        pairs.risk.cache_clear()
        for ladder in order:
            for env in (M["GEO"], M["ARCHIVE"]):
                assert ladder.risk(ladder.eta,env) == raw(ladder,ladder.eta,env)
    assert CAL["visit_offsets_ns"] == [0,240,520,760] and CAL["frame_ns"] == 1400
    out = {"risk_cache_witness":witness}
    for a in (32768,65536):
        scan = M["BASE"]["Scan"](2*a)
        local = theory["AnyPairs"](a,a)
        assert local.scan.L == F(350*a,10**9) == scan.L
        entries = list(theory["map_rows"](a))
        spans = [(lo,hi) for lo,hi,_ in entries[:-1]]
        assert spans[0][0] == a//2 and spans[-1][1] == a and entries[-1][:2] == [a,a]
        assert all(next_lo == hi+1 for (_,hi),(next_lo,_) in zip(spans,spans[1:]))
        out[str(a)] = {"nominal_L_s":str(scan.L),"top_s":str(local.levels[-1]),"history_counts":local.counts,
                       "period_fixed_s":str(F("0.0934444") if a==32768 else F("0.0458752"))}
        for name,env in (("geo",M["GEO"]),("archive",M["ARCHIVE"])):
            blocks = [check_block(theory,a,lo,hi,name,env,row[name]) for lo,hi,row in entries]
            # The single-phase bound is affine in W for fixed scan and domain.
            slope = M["physical"](scan,1,scan.L,both=False,env=env) - DELTA
            quarter = min(a, (EPS/4-DELTA)//slope)
            assert quarter >= a//2 and M["physical"](scan,quarter,scan.L,both=False,env=env) <= EPS/4
            assert quarter == a or M["physical"](scan,quarter+1,scan.L,both=False,env=env) > EPS/4
            domain = {
                "all_maps":summarize(blocks[:-1],scan,a,env),
                "all_partners_outside":summarize([blocks[-1]],scan,a,env),
                "quarter_max_W":quarter,
                "witness_blocks":[[r["lo"],r["hi"],r["cap"],DOWN(r["excluded"],12)] for r in blocks],
            }
            if name == "geo" and a == 65536:
                assert quarter == 44529
            if a == 65536:
                # Use the GEO quarter restriction for BOTH domains on this application.
                cutoff = 44529
                covering = [r for r in blocks[:-1] if r["lo"] <= cutoff]
                assert covering[-1]["hi"] >= cutoff
                domain["W_at_most_44529"] = summarize(covering,scan,cutoff,env)
            out[str(a)][name] = domain
    # Conditional probability that a contact during an arbitrary forced write is dangerous.
    # Both policies share the same full-word uniform-touch bound c*S1.
    closed_port = {}
    closed_scan = M["BASE"]["Scan"](131072)
    for name,env in (("geo",M["GEO"]),("archive",M["ARCHIVE"])):
        forced_eta = F(32,38)*theory["OLD"].eta
        q_f = M["physical"](closed_scan,32768,F("0.0934444"),both=False,env=env)
        q_a = sum(theory["OLD"].risk(forced_eta,env))
        fee = theory["costs"](theory["OLD"],32768,env,q_a,True)
        fixed_min = F("11527603.947") if name=="geo" else F("1585505.253")
        total_room = min(EPS-q_a,(fixed_min-fee)/((READ+WRITE)*HARD),EPS-q_f)
        # Each scheduled fixed read is followed by a write on this service.
        P = F("0.0934444")
        slots = min(HARD,65536*(2+T/(XM*P-2*J)))
        forced_fixed = (READ+WRITE)*(slots+DELTA*(HARD-slots))
        closed_port[name] = {
            "q_fixed_weak_upper":UP(q_f,12),"q_ladder_weak_upper":UP(q_a,12),
            "continuous_q_over_epsilon_upper":UP(M["physical"](closed_scan,32768,closed_scan.L,both=False,env=env)/EPS,6),
            "forced_fixed_candidate_s_upper":UP(forced_fixed,3),
            "forced_fixed_s_lower":DOWN(2*fixed_min,3),"forced_ladder_s_upper":UP(fee,3),
            "same_forced_ratio_lower":DOWN(2*fixed_min/fee,4),
            "same_forced_extra_room_s_lower":DOWN(fixed_min-fee,3),
            "if_comparator_can_skip_clean_write_ratio_lower":DOWN(fixed_min/fee,4),
            "max_extra_probability_for_ladder_price_and_fixed_admissibility_down":DOWN(total_room,12),
            "max_conditional_danger_per_target_contact_both_policies_down":DOWN(total_room/(C*env.exposure),9),
        }
    out["closed_forced_write"] = closed_port
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theory-root", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = result(args.theory_root.resolve())
    target = HERE / "result.json"
    if args.check:
        assert data == json.loads(target.read_bytes())
        print("Verified both witnesses, complete W coverage, single-phase timing and cost margins.")
    else:
        target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
