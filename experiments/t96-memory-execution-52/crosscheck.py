"""Replay the pinned numerical engine behind #500; independently count pairs in ns bins."""
import bisect
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

import numpy as np
from scipy.stats import beta

from inputs import parents
from reference import CFG, CHECKPOINT, L, Run, oracle

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "t186-cluster-laws"
ENGINE_BLOB = "74b679f92e9db1d99e0acfe4993540bc54ea55bf"


def load_original(directory):
    path = directory / "engine.py"
    shutil.copyfile(OLD / path.name, path)
    data = path.read_bytes().replace(b"\r\n", b"\n")
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data)
    if blob.hexdigest() != ENGINE_BLOB:
        raise ValueError("the source of the #500 evaluator has changed")
    original = json.loads((OLD / "inputs.json").read_bytes())
    original.update(words=4, addresses=8)
    (directory / "inputs.json").write_text(json.dumps(original))
    spec = importlib.util.spec_from_file_location("section52_original", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def independent_upper():
    # Count pairs of unit ns exposure bins, not interval integrals. Two distinct
    # Poisson parents in the same bin contribute half a bin squared.
    pulses = [range(a*2800, b*2800) for a,b in CFG["pulse_rounds"]]
    bins = [ns for pulse in pulses for ns in pulse]
    if list(map(len, pulses)) != [5600, 5600]:
        raise ValueError("expected two equal 5600 ns pulses")
    weight = Fraction(1, 5*5600)  # per word per occupied ns bin
    doubled_pairs = 0
    for phase in (0, 240, 520, 760):
        starts = {0}
        for r in range(CFG["T_ns"]//2800 + 1):
            if r <= 1280 or r % 2 == 0:
                starts.update([r*2800 + phase, r*2800 + 1400 + phase])
        starts = sorted(starts)
        counts = [0]*len(starts)
        for ns in bins:
            gap = bisect.bisect_right(starts, ns) - 1
            doubled_pairs += 2*counts[gap] + 1
            if gap and ns-starts[gap] < 160:
                doubled_pairs += 2*counts[gap-1]
            counts[gap] += 1
    return Fraction(doubled_pairs, 2)*weight**2*Fraction(37,38)


def crosscheck(engine, saved):
    assert (engine.W, engine.D, engine.L, engine.CUT, engine.INSTALL) == (4,8,2800,2500,2700)
    horizon = saved["horizon_ns"]
    clean = oracle([], CHECKPOINT, record_from=CHECKPOINT)
    totals = np.zeros(len(engine.FIELDS), dtype=np.int64)
    failures = 0
    digest = hashlib.sha256()
    for trial in range(saved["trials"]):
        events = parents(trial)
        digest.update(f"{trial} {len(events)}\n".encode())
        marks = []
        for ns, word, bit, neighbour_bit in events:
            digest.update(f"{ns} {word} {bit} {neighbour_bit}\n".encode())
            marks.append((ns, word, bit))
            if neighbour_bit >= 0:
                marks.append((ns, (word+1)%4, neighbour_bit))
        times, words, bits = np.asarray(marks, dtype=np.int64).reshape(-1,3).T
        result = engine.trajectory(times, words, bits, 0, len(marks), horizon, 0)
        # Start the new reference in its physically reached clean state and
        # suppress trace storage here. The original engine starts from zero.
        start = Run(passes=clean.passes, read_ns=clean.read_ns, sealed=clean.sealed,
                    fast_ns=clean.fast_ns)
        ref = oracle(events, horizon, prefix=start, record_from=horizon)
        measured = (ref.first_ns, ref.passes, ref.read_ns, ref.write_ns, ref.positive,
                    ref.switches, ref.fast_ns, ref.writes, sum(map(len,ref.words)))
        fields = (engine.FIRST,engine.PASSES,engine.READ_NS,engine.WRITE_NS,engine.REPORTS,
                  engine.SWITCHES,engine.FAST_NS,engine.REPAIRS,engine.REMAIN)
        actual = tuple(int(result[i]) for i in fields)
        if actual != measured:
            raise ValueError(f"trial {trial}: #500 {actual}, reference {measured}, parents {events}")
        totals += result
        failures += int(result[engine.FIRST] >= 0)
    assert digest.hexdigest() == saved["random_event_sha256"]
    assert failures == saved["first_count"] and totals[engine.REMAIN] == 0
    for offset,name in ((engine.READ_NS,"read_ns"),(engine.WRITE_NS,"write_ns"),
                        (engine.PASSES,"passes"),(engine.SWITCHES,"switches"),
                        (engine.REPAIRS,"writes"),(engine.FAST_NS,"fast_ns"),(engine.REPORTS,"positive")):
        assert totals[offset] == saved["totals"][name], name
    return failures


if __name__ == "__main__":
    saved = json.loads((HERE / "result.json").read_bytes())
    upper = independent_upper()
    assert upper == Fraction(saved["analytic"]["first_upper_exact"])
    n = saved["trials"]
    with TemporaryDirectory(prefix="t96_52_check_") as scratch:
        failures = crosscheck(load_original(Path(scratch)), saved)
    cp = (beta.ppf(0.025, failures, n-failures+1), beta.ppf(0.975, failures+1, n-failures))
    assert max(abs(x-y) for x,y in zip(cp, saved["clopper_pearson_95"])) < 1e-12
    print(f"#500: {n} paths, 9 fields each; {failures} first exceedances")
    print(f"ns-bin pair upper={upper}; independent 95% interval={cp[0]:.15f} {cp[1]:.15f}")
