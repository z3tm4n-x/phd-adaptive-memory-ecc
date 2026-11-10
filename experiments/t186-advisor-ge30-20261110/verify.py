"""Audit the saved paths, absolute charges and (optionally) PR449's independent primitives."""
import argparse
from fractions import Fraction as F
from hashlib import sha1
from importlib.util import module_from_spec, spec_from_file_location
import json
from math import ceil, isclose
from pathlib import Path
import sys

from bounds import binary_dyadic, floor_price, W, L, DATA
from original import HERE


def load(name): return json.loads((HERE/name).read_text(encoding="utf-8"))


def compare_theory(root):
    ref=root/"experiments/t196-dyadic-local-count-20261110/check.py"
    raw=ref.read_bytes().replace(b"\r\n",b"\n")
    # The scientific version used for the hand-off, not an unpinned solver.
    if sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()!="2b04b7b9c87349b98e554a658d1620bb99b883a6":
        raise ValueError("Use scientific PR449 at a25dbe2252058bae0f930d902a032377466b974c")
    spec=spec_from_file_location("pinned449",ref)
    th=module_from_spec(spec);sys.modules[spec.name]=th;spec.loader.exec_module(th)
    th.verify_engineer_calendar(HERE/"calendar.json")
    published=json.loads(ref.with_name("result.json").read_text(encoding="utf-8"))["CY62167GE30-45"]
    for k in (32,64):
        g=th.GE; P=k*g.L;s=th.WORD_RATE_FACTOR*(W-1)/2; n=ceil(300/P)
        levels=[2**i*g.L for i in range(1,k.bit_length())]
        history=g.xi_lo*(n*P-g.drain)-2*g.jitter
        a=[g.xi_hi*t/2 for t in levels]; fast=g.xi_hi*g.L+g.aperture
        base,_,_=th.scalar_bound(F(th.COVERAGE["b_s_inv"]),a,[history]*len(levels),fast,s)
        overlap=fast*th.phase_mask(g,g.L)+sum(x*th.phase_mask(g,t) for x,t in zip(a,levels))
        mass=th.B*g.xi_hi*P
        kernel=mass/(1-th.exp_upper(s*mass))+th.B*g.xi_hi*g.phase_max
        rise=(1+1/th.E_LO**2)*sum(a)*th.U*kernel
        upper=F(th.up(th.DELTA+th.PAIR_FACTOR*(base+overlap+rise)))
        ours=binary_dyadic(k,floor_price(False)["half_lower_s"],floor_price(True)["half_lower_s"])
        assert upper==ours["Qstop_upper"]
        if k==64:
            assert upper==F(published["same_binary64_by_dyadic_pairs"]["joint_stop_upper_d0"])
        print("PR449 cross-check:",k,str(upper),n,"cells")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theory-root",type=Path)
    args=parser.parse_args()
    DATA_=load("calendar.json")
    q=[DATA_["frame_ns"]*(j//2)+DATA_["word_slots_ns"][j%2] for j in range(W)]
    assert len({(3*j)%W for j in range(W)})==W and max(q)==DATA_["L_ns"]-880
    assert min(b-a for a,b in zip(q,q[1:]+[DATA_["L_ns"]]))==520
    assert DATA_["D_o_ns"]-q[-1]-500==80 and DATA_["L_ns"]-DATA_["D_o_ns"]-DATA_["I_o_ns"]==100
    bounds=load("bounds.json")
    for key in ("broad_class","exact_two_word_class"):
        assert F(bounds[key]["Q_lower"]["exact"])>F(1,1000)
    assert F(bounds["binary_split"]["32"]["Qstop_upper"]["exact"])==F("0.000880198")
    assert F(bounds["binary_split"]["64"]["Qstop_upper"]["exact"])==F("0.001234835")
    assert F(bounds["all_reserved_plus_app_peak_percent"]["exact"])<=75
    legacy,grid,ge=load("legacy-results.json"),load("ideal-results.json"),load("ge-results.json")
    for profile in legacy:
        for name,r in legacy[profile].items():
            raw=grid[profile]["rows"][name]["source"]
            assert raw["failures"]==r["raw_failures"]==r["corrected_failures"] and not r["paired_disagreements"]
        for name,r in ge[profile]["rows"].items():
            assert isclose(r["bus_s"],(240*r["mean_word_reads"]+260*r["mean_repairs"])/1e9,rel_tol=3e-15)
            assert isclose(r["bus_pct"],100*r["bus_s"]/315576000)
            assert 34.296<=r["nominal_path_peak_upper_pct"]<=34.4
            assert r["wilson95"][0]<=r["Q_MC"]<=r["wilson95"][1]
        # The constant calendars have no dependence on the generated particles.
        for rule,k in (("fixed1",1),("fixed4",4)):
            end=315576000*10**9; period=k*DATA["L_ns"]
            full,tail=divmod(end,period)
            expected=full*W+sum(t<tail for t in q)
            assert ge[profile]["rows"][rule]["mean_word_reads"]==expected
    if args.theory_root: compare_theory(args.theory_root)
    print("PASS: calendar, 72,000 original decisions, eight paired full-bank profiles, prices, peak and class tests.")


if __name__=="__main__":main()
