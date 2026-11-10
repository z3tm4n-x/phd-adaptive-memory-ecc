"""Fixed, deterministic fault campaign. Horizons are exclusive native 10ns tick counts."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
from build_model import build, run, HERE

L=280  # eight external addresses, 2 frames of 140 cycles
CASES={
 "clean":(0,L,0,1), "last_check_bit":(1,L,0,1), "two_parent_burst":(2,L,0,1),
 "one_birth_two_alias_ERR":(3,L,0,1), "post_sample_residual":(4,2*L,0,1),
 "lost_last_completion":(5,L,0,1), "repeated_physical_address":(6,L,0,1),
 "duplicate_release":(7,L,0,1), "missing_mandatory_write":(8,L,0,1),
 "duplicate_report":(9,L,0,1), "loss_and_requalification":(10,2819*L,0,0),
 "one_tick_late_and_stale":(11,1285*L,0,0), "exact_cut":(12,1283*L,0,0),
 "exact_cut_literal":(12,1283*L,0,1), "missed_install":(13,1282*L,0,0),
 "all_rungs_long_pause":(14,152834*L,0,0), "last_ERR_at_promotion":(15,1282*L,0,0),
 "terminal_inside_write":(16,233,0,1), "all_38_positions":(17,38*L,0,1),
 "lost_report_after_write":(18,2*L,0,1), "before_cut":(19,1283*L,0,0),
 "conflicting_report":(20,1282*L,0,0), "outside_partner":(1,L,1,1),
 "duplicate_at_threshold":(21,1281*L,0,0), "late_at_threshold":(22,1282*L,0,0),
 "post_stop_accounting":(23,3*L,0,1),
}
def capture(work):
    work.mkdir(parents=True,exist_ok=False)
    import hashlib
    files=["native.sv","tb.sv","policy_vpi.c","build_model.py","cases.py"]
    def source(): return {n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in files}
    frozen=source()
    build(work)
    def one(item):
        name, args=item
        path=run(work,*args)
        path.rename(work/(name+".trace"))
        return name
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for n in pool.map(one,CASES.items()): print("captured",n,flush=True)
    # Do not trust old traces if any part of the test/execution boundary changed.
    assert source()==frozen, "execution sources changed during capture"
    (work/"source.json").write_text(json.dumps(frozen,indent=2)+"\n")
if __name__=="__main__":
    capture(Path(sys.argv[1]).resolve())
