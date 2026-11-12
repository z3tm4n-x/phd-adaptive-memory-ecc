"""Exercise the one/two-cell bound across read phases and both weak-write outcomes."""
import json
from bisect import bisect_right
from pathlib import Path


cfg = json.loads((Path(__file__).resolve().parent.parent/"t186-cluster-laws/inputs.json").read_bytes())
W, A = cfg["words"], cfg["addresses"]
cell_rounds = cfg["cell_rounds"]
phases = cfg["phases_ns"]
scan_ns = A//len(phases)*cfg["frame_ns"]
cell_ns = cell_rounds*scan_ns
sample = cfg["sample_ns"]
offsets = [j//len(phases)*cfg["frame_ns"]+phases[j%len(phases)] for j in range(A)]


def check(left_stride, right_stride):
    # Rounds 256, 512, ... close a cell. Add faster rounds after the first
    # non-common visit on the right to cover an in-cell fallback as well.
    rounds = set(range(0,cell_rounds+1,left_stride))
    rounds.update(range(cell_rounds,3*cell_rounds+1,right_stride))
    rounds.update(range(cell_rounds+right_stride,2*cell_rounds+1))
    samples = [[] for _ in range(W)]
    owners = [[] for _ in range(W)]
    for r in sorted(rounds):
        cell = (r+cell_rounds-1)//cell_rounds
        for address,offset in enumerate(offsets):
            samples[address%W].append(r*scan_ns+offset+sample)
            owners[address%W].append(cell)
    times = {2*(cell_ns-scan_ns//2)+1, 2*(cell_ns+2*scan_ns)+1}
    for r in (cell_rounds-left_stride,cell_rounds,cell_rounds+right_stride):
        for off in offsets:
            for edge in (0,sample,cfg["read_ns"],cfg["write_edge_ns"],
                         cfg["read_ns"]+cfg["repair_extra_ns"]):
                t = 2*(r*scan_ns+off+edge)
                times.update((t-1,t+1))
    tested, split = 0, False
    for twice_t in times:
        if twice_t <= 0:
            continue
        # Odd integer represents a birth half a ns before or after the port edge.
        t = twice_t//2
        in_common_scan = (twice_t % (2*cell_ns)) < 2*scan_ns
        allowed = 2 if in_common_scan else 1
        for retain in (False, True):
            touched = set()
            for word in range(W):
                j = bisect_right(samples[word],t)
                touched.add(owners[word][j])
                # The old defect is removed if it predates start. A birth
                # between start and sample can survive this repair until the next alias.
                if retain and t >= samples[word][j]-sample:
                    touched.add(owners[word][j+1])
            assert len(touched) <= allowed
            if len(touched)==2:
                assert max(touched)-min(touched)==1
                split = True
            tested += 1
    return tested, split


if __name__ == "__main__":
    total, observed_split = 0, False
    for left,right in ((1,1),(2,4),(256,256),(256,1)):
        count, split = check(left,right)
        total += count
        observed_split |= split
    assert observed_split
    print(f"{total} phase and weak-write cases passed; two adjacent reset cells are attainable.")
