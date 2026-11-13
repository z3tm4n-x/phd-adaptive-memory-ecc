"""Directed controls independent of the skipped empty passes and the reported sums."""

import json
from fractions import Fraction as F
from itertools import product

import numpy as np

from policies import BENCH, HERE, e, krasnikov_step, threshold
from bounds import EPS, NS, stress_gap_lower
from verify import Word


def literal(hits, horizon):
    """Apply the original Word service; remember whether the current cell was dirty."""
    words = [Word(0) for _ in range(e.W)]
    i = r = consecutive = 0
    step = 1
    dirty = False
    stat = np.zeros(len(e.FIELDS), dtype=np.int64)
    starts, commands = [], []
    while r * e.L < horizon:
        start = r * e.L
        starts.append(r)
        stat[e.PASSES] += 1
        repairs = 0
        for a in range(e.D):
            launch = start + a//4 * 1400 + (0, 240, 520, 760)[a % 4]
            if launch >= horizon:
                break
            word = words[a % e.W]
            stat[e.READ_NS] += min(100, horizon - launch)
            while i < len(hits) and hits[i][0] < min(launch+60, horizon):
                t, w, b = hits[i]
                words[w].toggle(b, t)
                i += 1
            if launch+60 >= horizon or not word.errors:
                continue
            stat[e.WRITE_NS] += min(100, max(0, horizon-launch-100))
            while i < len(hits) and hits[i][0] < min(launch+160, horizon):
                t, w, b = hits[i]
                words[w].toggle(b, t)
                i += 1
            if launch+160 < horizon:
                word.errors = {k: t for k, t in word.errors.items() if t >= launch}
            repairs += launch+200 < horizon
        stat[e.REPAIRS] += repairs
        if start + e.CUT < horizon and repairs:
            stat[e.REPORTS] += 1
        if start + e.INSTALL < horizon:
            old = step
            dirty |= bool(repairs)
            if repairs:
                step = 1
                stat[e.RESETS] += 1
            if r % e.CELL == 0:
                consecutive = 0 if dirty or r == 0 else consecutive+1
                step = 1 if not consecutive else e.CELL
                dirty = False
            if step != old:
                stat[e.SWITCHES] += 1
                stat[e.DOWNS] += step < old
                commands.append(start + e.INSTALL)
        r += step
    for t, w, b in hits[i:]:
        if t < horizon:
            words[w].toggle(b, t)
    changes = [0, *commands, horizon]
    stat[e.FAST_NS] = sum(b-a for a, b in zip(changes[::2], changes[1::2]))
    firsts = [w.first_exceedance for w in words if w.first_exceedance is not None]
    stat[e.FIRST] = min(firsts, default=-1)
    stat[e.REMAIN] = sum(len(w.errors) for w in words)
    assert set(range(0, starts[-1]+1, e.CELL)).issubset(starts)
    return stat


def check_paths():
    l, p = e.L, e.L*e.CELL
    examples = [([], 3*p), ([(1, 0, 1), (2, 0, 2)], 3*l+90),
                ([(1, 0, 0), (59, 0, 0), (60, 0, 37)], 220),
                ([(p-2, 15, 1), (p+20, 0, 2)], 4*p+1),
                ([(p+10, 0, 3), (p+95, 0, 0), (p+1000, 15, 37)], 4*p+1),
                ([(p+21000, 5, 1), (2*p+80, 5, 2), (2*p+30000, 5, 3)], 5*p+1)]
    for end in (59, 60, 61, 99, 100, 101, 159, 160, 161, 199, 200, 201,
                e.CUT, e.CUT+1, e.INSTALL, e.INSTALL+1, l+95):
        examples.append(([(0, 0, 13), (70, 0, 35)], end))
    for hits, horizon in examples:
        arrays = np.array(hits, dtype="int64").reshape(-1,3).T.copy(order="C")
        expected = literal(hits, horizon)
        for jump in (False, True):
            obtained = threshold(*arrays, 0, len(hits), horizon, jump)
            np.testing.assert_array_equal(obtained, expected)
    alpha = 2 * e.W * F(1, 1000) * F(l, NS) / 315576000
    assert 0 < alpha < 1
    for counts in product((0, 1, 2, 32), repeat=4):
        k, u = 1, F(1)
        for m in counts:
            k, u = krasnikov_step(k, u, m)
            assert k == 1
    return len(examples)


def check_table():
    result = json.loads((HERE/"result.json").read_bytes())["profiles"]
    cases = json.loads((BENCH/"results.json").read_bytes())["profiles"]
    # The theory handoff gives independent, outward-rounded maxima and periods.
    limits = {"class_plateau": (2**24, .000718185, 1.094e-8, 2.31e-11),
              "sepem": (2**27, .000665877, 1.269e-9, 3.27e-12),
              "stress": (2, .000533424, .089172, .000184455)}
    for name, profile in result.items():
        fixed, fixed_q, slow_q, fast_q = limits[name]
        rows = profile["rows"]
        assert rows["fixed"]["mandatory_stride"] == fixed
        costs = profile["port_bounds_s"]
        assert rows["fixed"]["mean_port_s"] <= costs["fixed_upper"]
        assert rows["krasnikov_hold"]["mean_port_s"] >= costs["fast_floor"]
        assert min(rows[k]["mean_port_s"] for k in ("ladder","threshold")) >= costs["adaptive_floor"]
        for k, top in zip(("fixed","ladder","krasnikov_hold","threshold"),(fixed_q,slow_q,fast_q,slow_q)):
            row = rows[k]
            assert top*.996 < row["q_upper"] <= top
            assert row["n"] == 131072
            assert row["cp95_joint12"][0] <= row["cp95"][0] <= row["frequency"]
            assert row["frequency"] <= row["cp95"][1] <= row["cp95_joint12"][1]
            assert row["mean_port_pct"] <= 100
        n = rows["threshold"]["n"]
        ledger = profile["threshold_totals"]
        assert 100*ledger["completed_writes"] <= ledger["write_ns"] <= 100*(ledger["completed_writes"]+n)
        assert 0 <= 32*100*ledger["passes"] - ledger["read_ns"] <= 32*100*n
        case = next(c for c in cases[name]["cases"] if c["law"] == "compact_1p2")
        assert case["shared_input_sha256"] == profile["shared_particles_sha256"]
    assert stress_gap_lower() > F(18455, 10**7) > EPS


if __name__ == "__main__":
    print(f"{check_paths()} threshold paths matched the literal calendar in both replay modes.")
    check_table()
    print("All 12 ledgers, 3 shared inputs, fixed selection, analytical bounds and the stress lower bound passed.")
