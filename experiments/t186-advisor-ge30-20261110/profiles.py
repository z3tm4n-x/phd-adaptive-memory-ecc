"""Audit the emitted decimal segments, retaining initial level and boundary jumps."""
from argparse import ArgumentParser
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/"c3-candidate-price-20261109/basis.json"


def audit(work):
    base=json.loads(BASE.read_text(encoding="utf-8"))
    scale=F(39*65536,38*524288)
    b,B,g,U,excess_cap=[scale*F(base[k]) for k in ("b","B","g","J_cap","F")]
    T=F(base["T_s"])
    result=dict(scale=str(scale),b=float(b),B=float(B),g=float(g),U=float(U),excess_cap=float(excess_cap),profiles={})
    for name in "ABCDEFGH":
        path=work/("p"+name+".txt")
        prev_t=F(0); last=None
        total=variation=rises=s2=F(0); max_g=peak=F(0); lo=B; upward_jumps=0; ramps=0
        for n,line in enumerate(path.read_text(encoding="ascii").splitlines(),1):
            left,right,a,z=map(F,line.split())
            assert left==prev_t and right>left
            if last is None:
                start=a-b
            elif a>last:
                variation+=a-last;upward_jumps+=1
            u=max(0,z-a)
            if u>0: ramps+=1
            variation+=u;rises+=u
            total+=(right-left)*(a+z)/2
            s2+=(right-left)*(a*a+a*z+z*z)/3
            max_g=max(max_g,(z-a)/(right-left))
            peak=max(peak,a,z);lo=min(lo,a,z);prev_t=right;last=z
        assert prev_t==T
        uses=start+variation
        result["profiles"][name]=dict(segments=n,sha256=sha256(path.read_bytes().replace(b"\r\n",b"\n")).hexdigest(),
            start_excess=float(start),positive_variation=float(variation),rise_count=ramps,upward_boundary_jumps=upward_jumps,
            initial_plus_rises=float(uses),quota_ratio=float(uses/U),peak_bank_s_inv=float(peak),min_minus_b=float(lo-b),
            peak_minus_cap=float(peak-B),max_slope=float(max_g),slope_minus_cap=float(max_g-g),
            S1_bank=float(total),S2_bank_s_inv=float(s2),excess=float(total-b*T),
            excess_minus_quota=float(total-b*T-excess_cap),expected_parents=float(total/2),
            variation_minus_quota=float(uses-U),exact_emitted_in_class=bool(lo>=b and peak<=B and
                total-b*T<=excess_cap and max_g<=g and not upward_jumps and uses<=U))
    return result


if __name__=="__main__":
    p=ArgumentParser(description=__doc__)
    p.add_argument("--work",type=Path,required=True)
    p.add_argument("--check",action="store_true")
    a=p.parse_args();result=audit(a.work)
    dest=HERE/"profile-audit.json"
    text=json.dumps(result,indent=2)+"\n"
    if a.check: assert dest.read_text(encoding="utf-8")==text
    else: dest.write_text(text,encoding="utf-8",newline="\n")
    for k,r in result["profiles"].items():
        print(k,r["S1_bank"],r["initial_plus_rises"],r["quota_ratio"],r["min_minus_b"],r["peak_minus_cap"],r["slope_minus_cap"],r["excess_minus_quota"])
