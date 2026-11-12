"""Registered small-bank checks. Service is replayed at the #467 nominal port edges."""
import argparse
import json
import math
import random
from collections import defaultdict
from fractions import Fraction as F
from itertools import combinations

from calculate import BITS, HERE, LAWS, both_word_ratio, overlap_success


CONFIG = json.loads((HERE.parent / "t186-cluster-laws/inputs.json").read_bytes())
W, A = CONFIG["words"], CONFIG["addresses"]
FRAME, PHASES = CONFIG["frame_ns"], CONFIG["phases_ns"]
L = A // len(PHASES) * FRAME
CUT = L - CONFIG["cut_before_end_ns"]
SAMPLE, EDGE = CONFIG["sample_ns"], CONFIG["write_edge_ns"]
READ = CONFIG["read_ns"]
WRITE = READ + CONFIG["repair_extra_ns"]
N = 65536
RADIUS = math.sqrt(math.log(2 * 12 / 0.05) / (2 * N))


def start(address):
    frame, lane = divmod(address, len(PHASES))
    return frame * FRAME + PHASES[lane]


def support(law):
    if law == "two_uniform":
        return {pair: F(1, math.comb(W, 2)) for pair in combinations(range(W), 2)}
    sizes = {"single": [(1, F(1))], "compact_1p2": [(1, F(4, 5)), (2, F(1, 5))],
             "compact_5": [(5, F(1))], "adjacent_2": [(2, F(1))]}[law]
    return {tuple((w + i) % W for i in range(k)): prob / W
            for w in range(W) for k, prob in sizes}


def draw(law, rng):
    if law == "two_uniform":
        return tuple(sorted(rng.sample(range(W), 2)))
    w = rng.randrange(W)
    if law == "single":
        return (w,)
    if law == "compact_1p2":
        return (w, (w + 1) % W) if rng.randrange(5) == 0 else (w,)
    if law == "compact_5":
        return tuple((w + i) % W for i in range(5))
    raise ValueError(law)


def replay(hits, launches=(0,), horizon=None, retain=True):
    """One/two complete or truncated scans; retain both birth time and origin."""
    events = [(t, "hit", (parent, positions)) for t, parent, positions in hits]
    for launch in launches:
        for address in range(A):
            arrival = launch + start(address)
            for delay, op in ((SAMPLE, "sample"), (READ, "clean"), (EDGE, "edge"), (WRITE, "repair")):
                events.append((arrival + delay, op, (launch, address)))
    # All injections are strictly between the designated edges.
    memory = [dict() for _ in range(W)]
    samples, last, complete, reports = {}, {}, defaultdict(set), defaultdict(list)
    exceeded = False
    for t, op, data in sorted(events):
        if horizon is not None and t > horizon:
            break
        if op == "hit":
            parent, positions = data
            for word, bit in positions:
                cell = memory[word]
                if bit in cell:
                    del cell[bit]
                else:
                    cell[bit] = (t, parent)
                exceeded |= len(cell) > 1
            continue
        launch, address = data
        word = address % W
        if op == "sample":
            assert len(memory[word]) <= 1, "report oracle is specified on correctable prefixes"
            samples[data] = next((p for _, p in memory[word].values()), None)
        elif op == "edge" and samples[data] is not None:
            t0 = launch + start(address)
            memory[word] = {bit: hit for bit, hit in memory[word].items() if retain and hit[0] >= t0}
        elif (op == "clean" and samples[data] is None) or (op == "repair" and samples[data] is not None):
            complete[launch].add(address)
            last[launch] = t
            if op == "repair":
                reports[launch].append(samples[data])
    return last, complete, reports, memory, exceeded


def received(run, launch, arrival):
    last, complete, reports, _, _ = run
    if len(complete[launch]) != A or arrival is None or not last[launch] <= arrival <= launch + CUT:
        return None
    return tuple(reports[launch])


def next_level_after_fifth(report):
    # At the first possible promotion all earlier required reports were timely zero.
    return 2 if report == () else 1


def directed_cases():
    final = start(A - 1)
    # Inverted data from the partner, then a hidden check bit. Each is seen at either alias.
    for bit in (19, 37):
        run = replay([(-1, 0, [(0, bit)])])
        assert received(run, 0, CUT) == (0,) and not run[3][0]
    # +80 is after sample. The clean read leaves the new inversion for the next common scan.
    late = replay([(final + 80, 1, [(W - 1, 37)])], (0, L))
    assert received(late, 0, CUT) == () and received(late, L, L + CUT) == (1,)
    # A birth inside a repair may be seen twice across the two addresses when retained.
    for retain, expected in ((True, (4, 4)), (False, (4,))):
        run = replay([(30, 4, [(0, 37)])], retain=retain)
        assert received(run, 0, CUT) == expected
        assert len(set(expected)) == 1
    # Two different words of one parent give two repairs in this scan.
    run = replay([(-1, 7, [(0, 37), (1, 30)])])
    assert received(run, 0, CUT) == (7, 7)
    # Exactly-at-cut, late-before-install, missing and terminal incomplete.
    clean = replay([])
    assert next_level_after_fifth(received(clean, 0, CUT)) == 2
    for arrival in (CUT + 1, None):
        assert next_level_after_fifth(received(clean, 0, arrival)) == 1
    hit = [(final - 1, 4, [(W - 1, 37)])]
    truncated = replay(hit, horizon=final + WRITE - 1)
    assert received(truncated, 0, CUT) is None
    complete = replay(hit)
    assert received(complete, 0, CUT) == (4,) and received(complete, 0, None) is None
    assert not complete[3][-1]
    # Two distinct parents cancel the same position. The physical word stays correctable.
    cancelled = replay([(-2, 2, [(0, 37)]), (-1, 3, [(0, 37)])])
    assert received(cancelled, 0, CUT) == () and not cancelled[4]


def law_checks(law, index):
    marks = support(law)
    assert sum(marks.values()) == 1
    partial, masked, full_actual = {}, {}, {}
    t_partial = (start(27) + WRITE + start(28)) // 2
    for words in marks:
        # For one parent all 38 single positions have the same qualified response.
        pos = [(w, 37) for w in words]
        part = replay([(t_partial, 1, pos)])
        delivered = received(part, 0, CUT)
        assert delivered is not None and set(delivered) <= {1}
        partial[words] = bool(delivered)
        assert partial[words] == bool(set(words).intersection(range(12, 16)))
        full = replay([(start(31) + 80, 1, pos)], (0, L))
        full_actual[words] = bool(set(received(full, 0, CUT) + received(full, L, L + CUT)))
        masked[words] = any(w != 15 for w in words)
        assert full_actual[words] and masked[words] <= full_actual[words]
    probabilities = [sum(prob for mark, prob in marks.items() if event[mark])
                     for event in (partial, masked)]
    pairs = sum(pa * pb * (1 - F(1, BITS**len(set(a).intersection(b))))
                for a, pa in marks.items() for b, pb in marks.items())
    assert pairs == overlap_success(law, W) / W
    mean, kmax, _ = LAWS[law]
    for distance in range(1, W // 2 + 1):
        joint = sum(prob for mark, prob in marks.items() if 0 in mark and distance in mark)
        assert joint * W / mean == both_word_ratio(law, W, distance)
    probabilities.append(pairs)
    counts = [0, 0, 0]
    rng = random.Random(1961200 + index)
    for _ in range(N):
        first, second = draw(law, rng), draw(law, rng)
        counts[0] += partial[first]
        counts[1] += masked[first]
        # Two parents in a free interval. Apply physical XOR before any service.
        state = {word: 1 << rng.randrange(BITS) for word in first}
        exceeded = False
        for word in second:
            value = state.get(word, 0) ^ (1 << rng.randrange(BITS))
            state[word] = value
            exceeded |= value.bit_count() > 1
        counts[2] += exceeded
    assert all(abs(n / N - p) <= RADIUS for n, p in zip(counts, probabilities))
    return {"p_partial_p_masked_p_two_parents": [str(p) for p in probabilities],
            "partial_visible_rate_over_bank_inversions": str(probabilities[0] / mean),
            "partial_maximum_rate_over_bank_inversions": str(F(4, W * kmax)),
            "nominal_timely_detection_with_next_full_scan": str(sum(p for m, p in marks.items() if full_actual[m])),
            "MC_counts_in_same_order": counts}


def result():
    assert (W, A, L, CUT) == (16, 32, 11200, 10900)
    directed_cases()
    adjacent = support("adjacent_2")
    extra = sum(p for mark, p in adjacent.items() if set(mark).intersection(range(12, 16)))
    assert extra == F(5, 16)
    return {"trials_per_law": N, "simultaneous_confidence": 0.95,
            "hoeffding_halfwidth_upper": f"{math.ceil(RADIUS * 10**6) / 10**6:.6f}",
            "adjacent_2_partial_hit_control": str(extra),
            "laws": {law: law_checks(law, i) for i, law in enumerate(LAWS)}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = result()
    if args.check:
        assert data == json.loads((HERE / "cases.json").read_bytes())
        print("Enumeration, timed reports, physical pairs and 12 registered sample checks match.")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
