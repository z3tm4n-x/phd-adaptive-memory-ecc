"""Check settled port signals and register readbacks against the #456 calendar."""
import subprocess
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
READ_NS = (0, 240, 520, 760, 1400, 1640, 1920, 2160)


class Sample(NamedTuple):
    ns: int
    addr: int
    sel: int
    oe_n: int
    we_n: int
    drive: int
    dq_out: int
    hit: int
    sealed: int
    count: int
    report_ok: int
    proposed: int
    step: int
    gap: int


def check_trace(raw, arrival, repair, aperture):
    rows = {}
    samples = []
    for line in raw.splitlines():
        fields = line.split()
        if fields and fields[0] in {"PIN", "CONFIRM", "NEXT", "ORIGIN"}:
            # int() also rejects X/Z readbacks.
            values = tuple(map(int, fields[1:]))
            if fields[0] == "PIN":
                samples.append(Sample(*values))
            elif fields[0] in rows:
                raise ValueError(f"duplicate {fields[0]}")
            else:
                rows[fields[0]] = values

    if [s.ns for s in samples] != list(range(0, 2800, 10)):
        raise ValueError("incomplete observation of the target scan")
    errors = []

    def expect(name, actual, expected):
        if actual != expected:
            errors.append(f"{name}: got {actual}, expected {expected}")

    def changes(field):
        return [(cur.ns, getattr(cur, field)) for prev, cur in zip(samples, samples[1:])
                if getattr(cur, field) != getattr(prev, field)]

    def first(sequence):
        return next(iter(sequence), None)

    expect("natural promotion opportunity", rows["ORIGIN"], (1280 * 2800,))
    expect("confirmation transition", rows["CONFIRM"], (arrival,))
    usable_zero = not repair and arrival <= 2500
    expected_gap = 2 if usable_zero else 1
    next_ns, *next_pins = rows["NEXT"]
    expect("next physical start (ns)", next_ns, 2800 * expected_gap)
    expect("next addr/select/OE#/WE#/drive", next_pins, [0, 1, 0, 1, 0])

    # Decode ownership and strobes at every registered edge, including idle
    # spaces, without reading the controller's tick, frame or release logic.
    bad_port = []
    for s in samples:
        addr = max(i for i, start in enumerate(READ_NS) if start <= s.ns)
        age = s.ns - READ_NS[addr]
        write = addr == 7 and repair
        selected = age < (200 if write else 100)
        pins = (s.sel, s.oe_n, s.we_n, s.drive)
        expected = (selected, age >= 70, not (write and 110 <= age < 160),
                    bool(write and 100 <= age < 180))
        if pins != expected or (selected and s.addr != addr):
            bad_port.append((s.ns, s.addr, pins))
    expect("bad port edges (first)", first(bad_port), None)

    last = READ_NS[-1]
    final_visit = [s for s in samples if s.ns >= last]
    sample_edges = [(ns-last, val) for ns, val in changes("dq_out") if ns >= last]
    expect("last DQ capture (ns, value)", sample_edges, [(60, 0x5aa5)])
    expect("captured ERR transitions", changes("hit"), [(last+60, 1)] if repair else [])
    expect("DQ driven during write", {s.dq_out for s in samples if s.drive},
           {0x5aa5} if repair else set())

    release = first(s.ns-last for s in final_visit if not s.sel)
    publication = [(ns-last, val) for ns, val in changes("sealed")]
    release_ns = 200 if repair else 100
    expect("release (from last read)", release, release_ns)
    expect("publication (from last read)", publication, [(release_ns, 1)])
    expect("count transitions", changes("count"), [(last+200, 1)] if repair else [])
    expect("initial registers", (samples[0].hit, samples[0].sealed, samples[0].count,
                                  samples[0].proposed, samples[0].step, samples[0].gap),
           (0, 0, 0, 1, 1, 1))
    expect("published count", samples[-1].count, repair)
    expect("confirmation at cut", samples[250].report_ok, int(arrival <= 2500))
    proposal = changes("proposed")
    installed = changes("step")
    expect("proposal", proposal, [(2500, 2)] if usable_zero else [])
    expect("installed command", installed, [(2700, 2)] if usable_zero else [])
    expect("executed gap register", changes("gap"), [(2700, 2)] if usable_zero else [])

    # "-" means that the register held its existing value throughout.
    def edge(events):
        return events[0][0] if events else "-"

    def pin_edges(field):
        return ",".join(str(ns-last) for ns, _ in changes(field) if ns>last) or "-"

    print(f"arrival={arrival} repair={repair} aperture={aperture}"
          f" sample={edge(sample_edges)} dq={final_visit[-1].dq_out:04x}"
          f" err={final_visit[-1].hit} oe_off={pin_edges('oe_n')}"
          f" drive={pin_edges('drive')} we={pin_edges('we_n')}"
          f" release={release} sealed={edge(publication)}"
          f" count={samples[-1].count} proposed={edge(proposal)} installed={edge(installed)}"
          f" next_ns={next_ns} next_round={1280 + next_ns // 2800}", flush=True)
    for error in errors:
        print(f"  FAIL {error}", flush=True)
    return not errors


def run(work, checked, rtl):
    image = work / "timing_sim"
    subprocess.run(["iverilog", "-g2012", "-s", "timing_tb",
                    f"-Ptiming_tb.CHECK_LOCAL={checked}", "-o", image,
                    rtl, HERE / "timing_tb.sv"], check=True)
    cases = [(ns, 0, 0) for ns in (2495, 2500, 2505, 2515)]
    cases.extend([(2500, 1, 0), (2500, 0, 1), (2500, 1, 1)])
    passed = True
    for arrival, repair, aperture in cases:
        raw = subprocess.check_output(["vvp", image, f"+arrival={arrival}",
                                       f"+repair={repair}", f"+aperture={aperture}"], text=True)
        if not check_trace(raw, arrival, repair, aperture):
            passed = False
    return passed
