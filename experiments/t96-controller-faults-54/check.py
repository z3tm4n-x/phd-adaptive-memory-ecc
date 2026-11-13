"""Independent pin-only replay and exact ten-year allocation, without importing run.py."""
import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parent / "native-example-20261111"

# Physical recovery signatures relative to the registered external read 1280.
# A target=1280 pair is relative to its start, the quiet_after pair to 1536.
# Values follow from the registered single-bit XOR and the pinned HDL equation.
EXPECTED = {
    "clean":         (("control",2,4), ("control",2,4)),
    "last_err":      (("control",1,2), ("control",1,2)),
    "count_extra":   (("fast_return",1,2), ("fast_return",1,2)),
    "sealed_early":  (("fast_return",1,2), ("fast_return",1,2)),
    "sealed_lost":   (("fast_return",1,2), ("fast_return",1,2)),
    "seen_last":     (("fast_return",1,2), ("fast_return",1,2)),
    "proposal_zero": (("dangerous",512,514), ("fast_return",1,2)),
    "gap_zero":      (("dangerous",512,514), ("fast_return",1,2)),
    "step_zero":     (("dangerous",2,514), ("fast_return",2,3)),
    "wait_short":    (("masked",2,4), ("fast_return",2,3)),
    "wait_check":    (("masked",2,4), ("fast_return",2,3)),
    "quiet_before":  (("dangerous",4,8), ("dangerous",4,8)),
    "quiet_after":   (("dangerous",4,8), ("dangerous",4,8)),
    "hit_before":    (("masked",1,2), ("masked",1,2)),
    "hit_lost":      (("dangerous",2,3), ("dangerous",1,2)),
    "hit_spent":     (("masked",1,2), ("masked",1,2)),
    # phase jumps by two ticks. Subsequent starts are consistently 20 ns early.
    "timer_skip":    (("dangerous",2,3), ("dangerous",2,3)),
}


def assert_equal(left, right, context):
    if left != right:
        raise ValueError(f"{context}: observed {left}, expected {right}")


def check_one(raw, case, variant, result):
    name = case["id"]
    dirty = case["memory"] == "dirty"
    offset = (case["look_after_round"]-1280)*2800
    expected_label, r1, r2 = EXPECTED[name][variant]
    skew = -20 if name=="timer_skip" else 0
    goal = [offset+r1*2800+skew, offset+r2*2800+skew]
    # Reconstruct addresses, write completion and the four-round tariff from
    # changes of output pins alone. The HDL's WRITE, SAMPLE, CTL and FAULT
    # records cannot turn a late/missing strobe into a passing repair.
    pin = {}
    for line in raw.splitlines():
        if line.startswith("BUS "):
            t, addr, select, oe, we, drive, data = map(int,line.split()[1:])
            pin[t] = (addr,select,oe,we,drive,data)
    end = int(next(x.split()[1] for x in raw.splitlines() if x.startswith("END ")))
    reads, writes = [], []
    was_qualified, previous_we = False, 1
    for t,(addr,select,oe,we,drive,data) in pin.items():
        qualified = bool(select and not oe and we and not drive)
        if qualified and not was_qualified:
            reads.append((t,addr))
        if we and not previous_we:
            if not select or not drive or not oe:
                raise ValueError("unqualified end of WE#")
            # These inputs use only the old isolated check-bit error in word 3.
            assert_equal((addr,data),(7,0xa5bf) if t<2800 else (3,0x3413),name)
            writes.append(t)
        previous_we,was_qualified=we,qualified
    assert_equal(reads[:8],list(zip((0,240,520,760,1400,1640,1920,2160),range(8))),name)
    starts = [t for t,addr in reads if addr==0]
    chosen = [t for t in starts if t>offset][:2]
    assert_equal(chosen,goal,name)
    assert_equal(chosen,result["first_two_after_focus_ns"],name)
    correct_edge = {"hit_lost": [6520,3720][variant], "timer_skip": 6500}.get(name,2320)
    assert_equal(writes, [correct_edge] if dirty else [], name)
    first_actual = result["first_actual_repair"]
    assert_equal(writes[:1], [first_actual[0]] if first_actual else [], name)
    missed = dirty and correct_edge>2320
    assert_equal(result["repair_missed_by_2320_ns"],missed,name)
    assert_equal(result["memory_dirty_at_2320"],missed,name)
    assert_equal(result["outcome"],expected_label,name)
    if name=="quiet_after":
        assert_equal(starts[:129],list(range(0,716801,5600)),name)
        assert_equal(result["first_missed_scan"]["due_ns"],722400,name)
    # On this geometry every input/transition is recorded on the 5 ns test
    # grid. Charge one 5 ns slot at a time independently of the edge integrator.
    assert end >= 11200
    state = None
    t0 = 0
    read_starts = {t for t,addr in reads}
    read_ns = write_ns = 0
    for t in range(0,11200,5):
        state = pin.get(t,state)
        if t in read_starts:
            t0=t
        if state[1]:
            if t-t0 < 100:
                read_ns+=5
            else:
                write_ns+=5
    assert_equal(result["port_first_4_rounds_ns"],dict(read=read_ns,write=write_ns),name)


def allowance(other, common, mission_seconds=315576000):
    total = Fraction(6,10**6)
    if not (0 <= other <= 1 and 0 <= common <= 1):
        raise ValueError("bounds must be probabilities")
    residual = total - other - common
    # A negative subtraction is an insufficient allocation, not a zero bound.
    return residual, residual / mission_seconds if residual>=0 else None


def budget():
    total=Fraction(6,10**6)
    rows=[]
    for other,common in [(0,0),(Fraction(1,10**6),Fraction(1,10**6)),(total,0),(total,Fraction(1,10**6))]:
        left, per_sec=allowance(other,common)
        rows.append(dict(other=str(other),common=str(common),available=str(left),
                         rate_per_s=str(per_sec) if per_sec is not None else None,
                         FIT=float(per_sec*3600*10**9) if per_sec is not None else None))
    assert rows[-1]["rate_per_s"] is None and rows[-2]["rate_per_s"]=="0"
    return rows


def check_sources():
    for name in ("native8.sv","inject_tb.sv","observations.txt","synth.tcl"):
        source=(LEGACY/name).read_bytes().replace(b"\r\n",b"\n")
        yield name,hashlib.sha1(b"blob "+str(len(source)).encode()+b"\0"+source).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work",type=Path,help="output directory of run.py with the raw Icarus logs")
    args=parser.parse_args()
    cfg=json.loads((HERE/"config.json").read_bytes())
    data=json.loads((args.work/"results.json").read_bytes())
    assert set(EXPECTED)=={case["id"] for case in cfg["cases"]}
    assert cfg["mission_seconds"]==315576000 and Fraction(cfg["exception_quota"])==Fraction(6,10**6)
    for v in (0,1):
        for case in cfg["cases"]:
            name=case["id"]
            raw=(args.work/f"{v}-{name}.log").read_text(encoding="utf-8")
            check_one(raw,case,v,data[str(v)][name])
    # Negative control: replace the observed late repair of hit_lost with an
    # asserted success at the nominal deadline. Physical strobes must overrule it.
    case=next(c for c in cfg["cases"] if c["id"]=="hit_lost")
    reported=dict(data["1"]["hit_lost"],repair_missed_by_2320_ns=False)
    try:
        check_one((args.work/"1-hit_lost.log").read_text(encoding="utf-8"),case,1,reported)
    except ValueError:
        pass
    else:
        raise AssertionError("checker accepted a fictitiously timely repair")
    sources=dict(check_sources())
    assert sources["native8.sv"]==cfg["rtl_blob"]
    print(f"Independent pin audit: {len(EXPECTED)*2} cases, late-write sentinel rejected")
    print(json.dumps({"sources":sources,"quota_examples":budget()},indent=2))


if __name__ == "__main__":
    main()
