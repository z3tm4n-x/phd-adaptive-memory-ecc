"""Directed port, jump and visibility checks independent of the statistical sample."""
from fractions import Fraction as F
from itertools import combinations
import json
from math import ceil
from runpy import run_path
import sys

import numpy as np
from scipy.stats import binomtest

import engine as e
from inputs import EXP, Profile, generate, load

sys.path.insert(0, str(EXP / "t457-native-err-local"))
reference = run_path(str(EXP / "t457-native-err-local/oracle.py"))
old_history = reference["history"]
from memory_oracle import Word


def literal(hits, horizon, stride):
    """Explicit visits with the original Word and clean-cell history from #460."""
    bank = [Word(0) for _ in range(16)]
    out = {key: 0 for key in e.FIELDS}
    index = 0

    def advance(edge):
        nonlocal index
        while index < len(hits) and hits[index][0] < min(horizon, edge):
            when, w, bit = hits[index]
            bank[w].toggle(bit, when)
            index += 1

    r = clean = 0
    dirty = False
    mode = stride or 1
    reset_cells = set()
    last_install = 0
    while r * e.L < horizon:
        start = r * e.L
        out["passes"] += 1
        repairs = 0
        for address in range(32):
            launch = start + 1400 * (address // 4) + (0, 240, 520, 760)[address % 4]
            if launch >= horizon:
                break
            word = bank[address % 16]
            advance(launch + 60)
            out["read_ns"] += min(horizon - launch, 100)
            if launch + 60 >= horizon or not word.errors:
                continue
            out["write_ns"] += min(100, max(0, horizon - launch - 100))
            advance(launch + 160)
            if launch + 160 < horizon:
                word.errors = {b: t for b, t in word.errors.items() if t >= launch}
            if launch + 200 < horizon:
                repairs += 1
        out["completed_writes"] += repairs
        if repairs and start + e.CUT < horizon:
            out["positive_reports"] += 1
        if not stride and start + e.INSTALL < horizon:
            if r and repairs:
                out["resets"] += 1
                reset_cells.add((r + 255) // 256)
            clean, dirty, new = old_history(clean, dirty, mode, r, bool(repairs))
            if mode == 1:
                out["fast_ns"] += start + e.INSTALL - last_install
            last_install = start + e.INSTALL
            out["switches"] += int(mode != new)
            out["downshifts"] += int(mode > new)
            mode = new
        r += mode
    advance(horizon)
    if mode == 1:
        out["fast_ns"] += horizon - last_install
    out["reset_cells"] = len(reset_cells)
    out["terminal_wrong_bits"] = sum(len(word.errors) for word in bank)
    firsts = [word.first_exceedance for word in bank if word.first_exceedance is not None]
    out["first_ns"] = min(firsts) if firsts else -1
    return np.asarray(list(out.values()), dtype="int64")


def evaluate(hits, T, stride, accelerate=True):
    arrays = np.asarray(hits, dtype="int64").reshape(-1, 3).T
    return e.trajectory(*arrays, 0, len(hits), T, stride, accelerate)


def directed():
    L = e.L
    cases = [
        ([], 4 * L + 35), ([(1, 0, 37)], 151),
        ([(59, 0, 2), (60, 0, 3)], 201),
        ([(0, 0, 32), (90, 0, 32)], 161),
        ([(5, 0, 32), (6, 0, 37)], 2 * L),
        ([(5000, 15, 32), (5000, 0, 37)], 2 * L),
        ([(L - 500, 15, 0), (2 * L - 650, 15, 0)], 3 * L),
        ([(L + 100, 5, 32), (L + 101, 5, 35)], 3 * L),
        ([(1280 * L - 1, 1, 6), (1280 * L + 525, 2, 1)], 1283 * L),
        ([(1282 * L - 2, 5, 6), (1282 * L - 1, 6, 7),
          (1283 * L - 2, 9, 0)], 1285 * L),
    ]
    # The last release, cut, install and T are independent frontiers.
    for t in (59, 60, 61, 99, 100, 101, 159, 160, 161, 199, 200, 201,
              L - 440, e.CUT, e.CUT + 1, e.INSTALL, e.INSTALL + 1):
        cases.append(([(0, 0, 37), (L - 700, 15, 3)], t))
    for hits, T in cases:
        for stride in (1, 4, 256, 0):
            expected = literal(hits, T, stride)
            for jump in (False, True):
                result = evaluate(hits, T, stride, jump)
                assert np.array_equal(result, expected), (hits, T, stride, e.FIELDS, result, expected)
    # A first exceedance in a fixed controller's last idle gap and an XOR
    # cancellation must remain distinguishable even with no read at either hit.
    late = [(L + 5, 8, 1), (L + 6, 8, 2)]
    assert evaluate(late, 2 * L, 256)[e.FIRST] == L + 6
    assert evaluate([(0, 1, 37), (4, 1, 37)], L, 1)[e.FIRST] == -1
    # Hit immediately before the first opportunity after the 256L promotion.
    r = 596 * 256
    due = (r + 256) * L
    trace = [(due - 1, 0, 31), (due - 1, 15, 37)]
    slow = evaluate(trace, due + 3 * L, 0, False)
    fast = evaluate(trace, due + 3 * L, 0)
    assert np.array_equal(slow, fast) and fast[e.DOWNS] == 1 and fast[e.SWITCHES] == 9
    assert fast[e.REPAIRS] == 2 and fast[e.RESETS] == 1
    return len(cases) * 4


def geometry():
    W = 16
    singles = [((i,), F(1, W)) for i in range(W)]
    pairs = [(pair, F(1, 120)) for pair in combinations(range(W), 2)]
    ring = lambda i, n: tuple((i + j) % W for j in range(n))
    adjacent = [(ring(i, 2), F(1, W)) for i in range(W)]
    sizes = {"single": singles, "two_uniform": pairs,
             "compact_1p2": [(m, p * F(4, 5)) for m, p in singles] + [(m, p / 5) for m, p in adjacent],
             "compact_5": [(ring(i, 5), F(1, W)) for i in range(W)]}
    output = {}
    for law in e.CFG["laws"]:
        rows = sizes[law["id"]]
        m = F(*law["mean"])
        assert sum(p for _, p in rows) == 1 and sum(len(s) * p for s, p in rows) == m
        for i in range(W):
            marginal = sum(p for s, p in rows if i in s)
            assert marginal == m / W and (W * 38 / m) * marginal / 38 == 1
        output[law["id"]] = {str(k): str(sum(p for s, p in rows if min(s) < k)) for k in (1, 4, 8)}
    assert sum(p for s, p in adjacent if min(s) < 4) == F(5, 16)
    assert sum(p for s, p in pairs if min(s) < 4) == F(9, 20)
    return output


def check_draws():
    """Inspect parent identity and word placement in the registered generator."""
    spec = e.CFG["profiles"][2]
    profile = Profile(spec)
    for li, law in enumerate(e.CFG["laws"]):
        t, w, b, edges, counts, multi = generate(profile, 2, li, 0, 2048)
        assert edges[0] == 0 and edges[-1] == len(t)
        assert np.all((0 <= b) & (b < 38)) and np.all((0 <= w) & (w < 16))
        assert np.all(((2_000_000_000 <= t) & (t < 2_020_000_000)) |
                      ((4_000_000_000 <= t) & (t < 4_020_000_000)))
        allowed = {"single": {1}, "two_uniform": {2}, "compact_1p2": {1, 2}, "compact_5": {5}}
        assert set(multi) == allowed[law["id"]]
        i = 0
        for width in multi:
            words = w[i:i + width]
            assert len(set(words)) == width and t[i] == t[i + width - 1]
            if law["id"].startswith("compact"):
                assert np.all(words == (words[0] + np.arange(width)) % 16)
            i += width
        assert np.array_equal(edges, np.r_[0, multi.cumsum()][np.r_[0, counts.cumsum()]])
        assert all(np.all(np.diff(t[a:z]) >= 0) for a, z in zip(edges[:-1], edges[1:]))


def check_ledger():
    """Independent fixed ledger, CP inversion and paired-count identities."""
    result = json.loads((e.HERE / "results.json").read_bytes())
    family = result["family_rows"]
    count = 0
    for spec in e.CFG["profiles"]:
        T = spec["T_s"] * 10**9
        offsets = [i // 4 * 1400 + (0, 240, 520, 760)[i % 4] for i in range(32)]
        for case in result["profiles"][spec["id"]]["cases"]:
            n = case["n"]
            ladder = case["rows"][0]
            assert n == e.CFG["trials_per_law_profile"]
            assert [row["period_ns"] for row in case["rows"][1:]] == [2**j * e.L for j in spec["fixed_log2_L"]]
            for row in case["rows"]:
                count += 1
                s = row["totals"]
                read, write = s["read_ns"], s["write_ns"]
                # Only the final transaction can contribute an incomplete write.
                assert 0 <= write - 100 * s["completed_writes"] <= n * 100
                assert 0 <= read + write <= n * T
                assert 0 <= s["fast_ns"] <= n * T
                assert 0 <= s["downshifts"] <= s["reset_cells"] <= s["resets"] <= s["positive_reports"]
                assert s["positive_reports"] <= s["completed_writes"]
                assert abs(row["port_s_mean"] * 1e9 - (read + write) / n) <= max(1., (read + write) / n * 1e-15)
                P = row["period_ns"]
                if P:
                    full, tail = divmod(T, P)
                    tail_ns = sum(min(100, max(0, tail - t)) for t in offsets)
                    assert read == n * (full * 3200 + tail_ns)
                    assert s["passes"] == n * (full + bool(tail))
                    assert s["switches"] == s["resets"] == 0
                k = row["first_exceedances"]
                assert k - ladder["first_exceedances"] == row["failed_only_here_vs_ladder"] - row["failed_only_ladder_vs_here"]
                test = binomtest(k, n)
                for name, alpha in (("CP95", 0.05), ("CP95_family", 0.05 / family)):
                    ci = test.proportion_ci(1 - alpha, method="exact")
                    assert np.allclose(row[name], ci, rtol=0, atol=2e-12)
    assert count == family == 136
    return count


def main():
    cal = load("t186-native-ge30-x16/calendar.json")
    assert tuple(cal["visit_offsets_ns"]) == e.PHASE and cal["frame_ns"] == e.FRAME
    assert [cal["operation_ns"][k] for k in ("sample_dq_and_err", "we_high", "read_release_or_drive_write", "write_release")] == [e.SAMPLE, e.EDGE, e.READ, e.READ + e.WRITE]
    assert e.CUT == e.L - cal["report_cut_ns_before_next_pass"]
    assert e.INSTALL == e.CUT + cal["command_install_ns"]
    required = tuple(ceil(((2**j * e.L / F("0.00168") + 1) / F("0.99999") + e.L) / (256 * e.L))
                     for j in range(1, 9))
    assert required == e.REQ == reference["REQ"] and e.L == 11200
    print("bit marginals and footprint intersection:", geometry())
    check_draws()
    print("literal cases by policy:", directed(), "; all eight promotions and return checked")
    if "--results" in sys.argv:
        print("row ledgers, exact binomial intervals and paired differences:", check_ledger())


if __name__ == "__main__":
    main()
