"""Reproduce the 12 registered rows; replay new ERR policy on verified shared marks."""

import argparse
import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.stats import beta

from policies import BENCH, HERE, e, threshold_block
from bounds import EPS, NS, fixed_candidate, risk_upper, stress_gap_lower, word_limits
from inputs import CFG, Profile, generate
from run import clopper_pearson, exact_sum

FROZEN = {
    "inputs.json": "b16816a3af41ec14a2a8f60ef0c68cf59d1701cfd8f3877e52aa432d6be89754",
    "inputs.py": "12e20b89cc34b0dc628b6c35315164c2471af96bc533b009c2839bf97f1bd898",
    "engine.py": "bb73ae2c191c2fb3c6510deb923242a5e0cf689d24d07949e3480f4d40a21401",
    "results.json": "4bbbec891abd051378828c36c9fcf42d5f539f638bd3382fec4c55ab16b4f1d2",
}


def source():
    for name, expected in FROZEN.items():
        content = (BENCH / name).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError(f"Source mismatch: {name}")
    return json.loads((BENCH / "results.json").read_bytes())


def make_row(hits, totals, rounds, profile, n, lower=0):
    prob = risk_upper(profile, rounds)
    ns_read, ns_written = totals["read_ns"], totals["write_ns"]
    cost = (ns_read + ns_written) / (n * NS)
    return dict(first=hits, n=n, frequency=hits/n, cp95=clopper_pearson(hits, n, .05),
                cp95_joint12=clopper_pearson(hits, n, .05/12),
                one_sided_upper95=float(beta.isf(.05, hits+1, n-hits)) if hits < n else 1.,
                mandatory_stride=rounds, q_upper=math.ceil(prob*10**17)/1e17,
                q_lower=math.floor(lower*10**14)/1e14,
                guarantee="pass" if prob < EPS else ("excluded" if lower > EPS else "open"),
                ns_read_sum=ns_read, ns_write_sum=ns_written, mean_port_s=cost,
                mean_port_pct=cost/(profile.horizon/NS)*100,
                mean_reports=totals["positive_reports"]/n, mean_writes=totals["completed_writes"]/n)


def expected_fixed_cap(rounds, horizon_ns, mean_hits):
    period = rounds*e.L
    full, rest = divmod(horizon_ns, period)
    read = full*e.D*e.READ
    for address in range(e.D):
        phase = address//4*e.FRAME + e.PHASE[address % 4]
        read += min(e.READ, max(0, rest-phase))
    # Every positive sample has an inversion from the preceding visit's start
    # through this sample (or since launch at t=0). Only successive such windows
    # can overlap. A birth in the aperture may therefore pay for two writes.
    return F(read,NS) + F(2*e.WRITE,NS)*mean_hits


def one(profile, old, pi, pilot):
    size = CFG["batch_size"]
    n = CFG["trials_per_law_profile"]
    case = next(c for c in old["cases"] if c["law"] == "compact_1p2")
    assert case["n"] == n and CFG["laws"][2]["id"] == case["law"] and n % size == 0
    rounds = fixed_candidate(profile)
    old_rows = {r["mode"]: r for r in case["rows"]}
    fixed = old_rows[f"fixed_{rounds}L"]
    # These controls come from the existing high-statistics run, including its
    # full-horizon post-failure oracle and exact ns ledgers for each mode.
    stored = [fixed, old_rows["ladder"], old_rows["fixed_1L"]]
    digest, totals = hashlib.sha256(), {k: 0 for k in e.FIELDS[1:]}
    hits = 0
    for batch in range(1 if pilot else n//size):
        t, w, b, edges, parents, mult = generate(profile, pi, 2, batch, size)
        for arr in (parents, mult, t, w, b):
            digest.update(np.asarray([len(arr)], dtype="<i8").tobytes())
            digest.update(np.asarray(arr, dtype="<i8").tobytes())
        stats = threshold_block(t, w, b, edges, profile.horizon)
        hits += int(np.count_nonzero(stats[:, e.FIRST] >= 0))
        for k, name in enumerate(e.FIELDS[1:], 1):
            totals[name] += exact_sum(stats[:, k])
    if pilot:
        return
    assert digest.hexdigest() == case["shared_input_sha256"]
    lower = stress_gap_lower() if profile.name == "stress" else 0
    rows = {}
    for name, old_row, stride in zip(("fixed", "ladder", "krasnikov_hold"), stored, (rounds, e.CELL, 1)):
        row = make_row(old_row["first_exceedances"], old_row["totals"], stride,
                       profile, n, lower if name == "ladder" else 0)
        assert row["cp95"] == old_row["CP95"]
        assert math.isclose(row["mean_port_s"], old_row["port_s_mean"], rel_tol=4e-16)
        rows[name] = row
    rows["threshold"] = make_row(hits, totals, e.CELL, profile, n, lower)
    for row in rows.values():
        row["cost_over_fixed"] = row["mean_port_s"]/rows["fixed"]["mean_port_s"]
    # Deterministic baselines: a pass at every 256L (including the last fragment),
    # and fixed L read time. Store upward/downward rounded physical cost bounds.
    # Integral caps in bounds.word_limits include directed rounding.
    mean_hits = e.W*word_limits(profile)[0]
    fixed_cap = expected_fixed_cap(rounds, profile.horizon, mean_hits)
    adaptive_floor = expected_fixed_cap(e.CELL, profile.horizon, 0)
    fast_floor = expected_fixed_cap(1, profile.horizon, 0)
    return dict(T_s=profile.horizon//NS, shared_particles_sha256=digest.hexdigest(),
                port_bounds_s=dict(fixed_upper=math.ceil(fixed_cap*10**6)/10**6,
                                   adaptive_floor=math.floor(adaptive_floor*10**6)/10**6,
                                   fast_floor=math.floor(fast_floor*10**6)/10**6),
                inputs=profile.notes, fixed_grid_upper={str(1 << k):math.ceil(
                    risk_upper(profile,1 << k)*10**17)/1e17 for k in profile.spec["fixed_log2_L"]},
                threshold_totals=totals, rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True, help="T141 directory containing bands.npy")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--pilot", action="store_true")
    args = parser.parse_args()
    previous = source()
    out = {"base":"0c8708dbd0c65ad2bad43b8e3a750c2d67447fea",
           "registration":"1648e80b6e80cfe1be349f7083eaae7262e7f6a0",
           "source_sha256_lf":FROZEN, "profiles":{}}
    for i, spec in enumerate(CFG["profiles"]):
        start = perf_counter()
        profile = Profile(spec, args.cache)
        out["profiles"][profile.name] = one(profile, previous["profiles"][profile.name], i, args.pilot)
        print(f"{profile.name}: {perf_counter()-start:.2f} s", flush=True)
    if args.pilot:
        return
    path = HERE / "result.json"
    if args.check:
        if out != json.loads(path.read_bytes()):
            raise SystemExit("Comparison differs")
        print("All 12 rows and three common-stream hashes reproduced.")
    else:
        path.write_text(json.dumps(out, indent=2, allow_nan=False)+"\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
