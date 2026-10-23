"""Small exact checks of NEW lemmas, not a repeat of accepted campaigns.

The mathematical proofs are in theory/t196-{hold-price,krasnikov-hold}-20261023.md.
No physical Q, cost estimate, Monte Carlo, or new transport is implemented.
Run from any cwd with Python 3; only the standard library is needed.
"""
from fractions import Fraction as F
from hashlib import sha1
from importlib.util import module_from_spec, spec_from_file_location
from itertools import combinations_with_replacement, product
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments/t186-method-comparison/stage2/policies.py"
raw = SOURCE.read_bytes()
blob = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
assert blob == "2f0f94c39c9200337c267085b6262493e62ae800", blob
spec = spec_from_file_location("t196_frozen_policy", SOURCE)
policy = module_from_spec(spec)
spec.loader.exec_module(policy)


def hold_cover(records, horizon=16):
    """records = (parent birth/false anchor, source, delivery, kind).

    kind b/s is one primary background/solar ERR; x is exceptional.
    Different b/s records have different parents. An x can represent a
    repeat of any primary parent or a false event. No independence is used.
    """
    tau, pair, short, long = 2, 2, 3, 6
    # Frozen Our expires at the next strict cut; pay the full extra tick.
    wplus, hplus = short + 1, long + 1
    V, H, L = wplus + tau, hplus + tau, hplus + pair + 2*tau
    core = policy.Our(cfg=dict(NW=short, NH=long, NR=0,
                              timer_tick_ns=1, pair_source_ticks=pair,
                              source_tick_ns=1), words=8, cut=1)
    intervals = [(0, 1)]  # separately paid startup until the first wake
    primaries = []
    for birth, source, delivery, kind in records:
        assert birth <= source <= delivery <= birth + tau
        intervals.append((birth, birth + (V if kind == "b" else H if kind == "s" else L)))
        if kind != "x":
            primaries.append((birth, kind))
    for i, (u, ku) in enumerate(primaries):
        for v, kv in primaries[i+1:]:
            if abs(v-u) <= pair+tau:
                # Latest solar already has its H strip. Tied births are
                # also covered; NHPP ties need no probabilistic argument.
                if (ku == kv == "b" or
                    (ku == "b" and u >= v) or (kv == "b" and v >= u)):
                    intervals.append((max(u, v), max(u, v)+H))
    assert all(a[1] <= b[1] and a[2] <= b[2]
               for a, b in zip(records, records[1:])), records
    for tick in range(horizon+1):
        # Same-time source before delivery before expiry, as declared.
        for _, source, _, _ in records:
            if source == tick:
                core.publish(tick)
        for _, source, delivery, _ in records:
            if delivery == tick:
                core.observe(tick, source)
        if core.timer == tick:
            core.wake(tick)
        for instant in (F(tick), F(tick)+F(1, 2)):
            if instant > horizon:
                continue
            if core.mode(instant) == 1:
                assert any(left <= instant <= right for left, right in intervals), (
                    records, instant, intervals, core.times, core.modes)
    return 1


def check_hold_union():
    # All causal delivery patterns of up to three distinct primaries in
    # this small domain, each with either b/s label; birth order may differ
    # from source/delivery order. All boundaries use exact integers/halves.
    events = [(u, s, d) for u in range(4) for s in range(u, u+3)
              for d in range(s, u+3)]
    count = 0
    for length in range(4):
        for selected in combinations_with_replacement(events, length):
            ordered = tuple(sorted(selected, key=lambda x: (x[1], x[2], x[0])))
            if any(a[2] > b[2] for a, b in zip(ordered, ordered[1:])):
                continue
            for kinds in product("bs", repeat=length):
                count += hold_cover(tuple((*e, k) for e, k in zip(ordered, kinds)))
    exceptional = 0
    # Same-parent double ERR, including equal source times, then another
    # primary; x is never treated as a second independent parent.
    for u in range(3):
        positions = [(s, d) for s in range(u, u+3) for d in range(s, u+3)]
        for a, b in combinations_with_replacement(positions, 2):
            for e in events:
                for kind in "bs":
                    records = tuple(sorted(((u, *a, kind), (u, *b, "x"), (*e, kind)),
                                           key=lambda x: (x[1], x[2], x[0])))
                    if all(x[2] <= y[2] for x, y in zip(records, records[1:])):
                        exceptional += hold_cover(records)
    # False flag with adversarially chosen source/delivery beside a primary.
    for a, b in product(events, repeat=2):
        records = tuple(sorted(((*a, "b"), (*b, "x")), key=lambda x: (x[1], x[2], x[0])))
        if records[0][2] <= records[1][2]:
            exceptional += hold_cover(records)
    # A terminal pending source and expiry equality are explicitly sampled.
    hold_cover(((15, 16, 17, "b"),), horizon=16)
    return dict(primary_histories=count, exceptional_histories=exceptional,
                terminal_pending_histories=1, continuous_intervals_checked=True)


def check_krasnikov():
    cases = []
    sequences, single_cycles = 0, 0
    for words, ms in product((524288, 131072), ("0.001", "0.01")):
        p1 = F(words*196, 10**9)
        alpha = 2*words*F(ms)*p1/F(315576000)
        assert alpha < 2
        assert alpha < F("0.00000342")
        for counts in product(range(4), repeat=5):
            core = policy.Krasnikov(Ms=ms, zero="hold", words=words)
            for m in counts:
                core.count = m
                core.advance(core.anchor+core.period)
                assert core.k == 1 and core.modes == [1], (words, ms, counts)
            sequences += 1
        # Test equality branch, arbitrary inherited target and huge integer m.
        for target in (F(1), F(1)+alpha, F(1000)):
            for m in (*range(33), 10**9, 2**64):
                core = policy.Krasnikov(Ms=ms, zero="hold", words=words)
                core.target, core.count = target, m
                core.advance(core.period)
                assert core.k == 1
                if m and m != target:
                    assert core.target == 1+alpha/m
                    assert p1*(F(1, m)+alpha/(m*m)) < 3*p1
                single_cycles += 1
        # Boundary observation closes the old cycle before counting the flag.
        core = policy.Krasnikov(Ms=ms, zero="hold", words=words)
        core.observe(core.period, 0)
        assert core.k == 1 and core.count == 1 and core.anchor == core.period
        # The result must NOT accidentally include zero=longest.
        other = policy.Krasnikov(Ms=ms, zero="longest", words=words)
        other.advance(other.period)
        assert other.k == 27
        cases.append(dict(words=words, Ms=ms, alpha=str(alpha),
                          alpha_upper_decimal="0.00000342", next_stride=3))
    return dict(configurations=cases, sequences=sequences,
                single_cycles=single_cycles, negative_control_longest=True)


if __name__ == "__main__":
    report = dict(status="PASS", frozen_policy_blob=blob,
                  holds=check_hold_union(), krasnikov=check_krasnikov(),
                  physical_Q_claimed=False, price_numbers_computed=False,
                  accepted_campaign_repeated=False)
    print(json.dumps(report, ensure_ascii=False, indent=2))
