#!/usr/bin/env python3
"""Stage-A information-interface sensitivity.

Only the information interface is changed.  Stage-A feasible sets and the
reviewed Stage-A certificate/resource functions are reused from the pinned
Stage-A implementation directory.
"""
from __future__ import annotations
import argparse, base64, csv, gzip, importlib.util, itertools, json
from collections import defaultdict
from fractions import Fraction as R
from pathlib import Path

PATHS=("LL","LH","HL","HH")
LEVELS={"LL":("L","L"),"LH":("L","H"),"HL":("H","L"),"HH":("H","H")}
SET_RANK={"L":0,"H":1,"A":2}
TIMING_CLASSES=(
    ("T000",0,0,0),
    ("T001",0,0,1),
    ("T010",0,1,0),
    ("T011",0,1,1),
    ("T110",1,1,0),
    ("T111",1,1,1),
)
ETA_CLASSES=(("E_EXACT","[0,0.5)",False),("E_AMBIG","[0.5,infinity)",True))

def F(x): return x if isinstance(x,R) else R(str(x))
def fs(x):
    if isinstance(x,R):
        return str(x.numerator) if x.denominator==1 else f"{float(x):.15g}"
    return str(x)
def sc(x): return f"{float(x):.12e}"

def load_stage(stage_dir: Path):
    config=json.loads((stage_dir/"config.json").read_text(encoding="utf-8"))
    spec=importlib.util.spec_from_file_location("stage_a_reused",stage_dir/"stage_a.py")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    model=mod.load(config)
    if tuple(mod.PTH)!=PATHS: raise RuntimeError("Stage-A path order mismatch")
    if F(0) not in model["R"]: raise RuntimeError("rho=0 absent from Stage-A model")
    # Decode retained passing-set roots; do not rerun Stage-A search().
    text=(stage_dir/"passing_sets.json.gz.b64").read_text(encoding="utf-8").strip()
    roots=json.loads(gzip.decompress(base64.b64decode(text)))
    passing=[]
    with (stage_dir/"passing_sets.csv").open(newline="",encoding="utf-8") as h:
        passing=list(csv.DictReader(h))
    trees=json.loads((stage_dir/"selected_policy_trees.json").read_text(encoding="utf-8"))
    return config,mod,model,roots,passing,trees

def parse_case_encoding(encoded, U):
    # F=...;P=...;C=aL,aH,LLmask,LHmask,HLmask,HHmask,count|...
    parts={}
    for field in encoded.split(";"):
        k,v=field.split("=",1); parts[k]=v
    roots=[]
    if parts.get("C"):
        for z in parts["C"].split("|"):
            aL,aH,mLL,mLH,mHL,mHH,count=z.split(",")
            roots.append((F(aL),F(aH),{"LL":mLL,"LH":mLH,"HL":mHL,"HH":mHH},int(count)))
    def decode(mask):
        bits=int(mask,16)
        return tuple(U[i] for i in range(len(U)) if bits&(1<<i))
    feasible={p:{} for p in PATHS}
    for aL,aH,masks,_ in roots:
        for p in ("LL","LH"):
            vals=decode(masks[p]); old=feasible[p].get(aL)
            if old is not None and old!=vals: raise RuntimeError("inconsistent Stage-A root mask")
            feasible[p][aL]=vals
        for p in ("HL","HH"):
            vals=decode(masks[p]); old=feasible[p].get(aH)
            if old is not None and old!=vals: raise RuntimeError("inconsistent Stage-A root mask")
            feasible[p][aH]=vals
    return roots,feasible

def eligible_rho0_cases(passing):
    out=[]
    for row in passing:
        if row["rho_case"]!="0" or row["status"]!="SEARCHED": continue
        if int(row["precomputed_count"])>0 and int(row["causal_root_count"])>0:
            d=f"d{int(row['shield_mm'])}"; e=F(row["epsilon"])
            out.append((d,e,int(row["precomputed_count"]),int(row["causal_root_count"])))
    return sorted(out,key=lambda x:(int(x[0][1:]),x[1]))

def timing_predicates():
    return [
      {"timing_class":"T000","A0":0,"A1":0,"A2":0,
       "predicate":"not A1 and not A2",
       "meaning":"no report is available at either decision"},
      {"timing_class":"T001","A0":0,"A1":0,"A2":1,
       "predicate":"not A1 and A2",
       "meaning":"only the second-block report is available at t=300"},
      {"timing_class":"T010","A0":0,"A1":1,"A2":0,
       "predicate":"not A0 and A1 and not A2",
       "meaning":"first-block report arrives only by t=300; no current second-block report"},
      {"timing_class":"T011","A0":0,"A1":1,"A2":1,
       "predicate":"not A0 and A1 and A2",
       "meaning":"no report at t=0; both block reports are available at t=300"},
      {"timing_class":"T110","A0":1,"A1":1,"A2":0,
       "predicate":"A0 and not A2",
       "meaning":"first-block report is available at both decisions; no current second-block report"},
      {"timing_class":"T111","A0":1,"A1":1,"A2":1,
       "predicate":"A0 and A2",
       "meaning":"current block report is available at both decisions (Ideal timing endpoint)"},
    ]

def region_rows():
    out=[]
    for t,a0,a1,a2 in TIMING_CLASSES:
        pred=next(x for x in timing_predicates() if x["timing_class"]==t)
        for ec,er,amb in ETA_CLASSES:
            out.append({
              "region_id":f"{t}_{ec}","timing_class":t,"eta_class":ec,"eta_range":er,
              "A0":a0,"A1":a1,"A2":a2,"timing_predicate":pred["predicate"],
              "timing_meaning":pred["meaning"],
              "eta_meaning":("delivered report is necessarily singleton and identifies its true binary level"
                             if not amb else
                             "singleton or {L,H} is allowed; equality eta=0.5 belongs here"),
            })
    return out

def availability(s1,s2,ell,e1=True,e2=True):
    """Independent analytic boundary helper for focused tests."""
    s1,s2,ell=map(F,(s1,s2,ell))
    if not (R(0)<=s1<R(300) and R(300)<=s2<R(600) and ell>=0):
        raise ValueError("timestamp/latency outside declared contract")
    A0=bool(e1 and s1==0 and ell==0)
    A1=bool(e1 and s1+ell<=300)
    A2=bool(e2 and s2==300 and ell==0)
    sig=(int(A0),int(A1),int(A2))
    for t,a0,a1,a2 in TIMING_CLASSES:
        if sig==(a0,a1,a2): return t
    raise AssertionError(sig)

def eta_class(eta):
    eta=F(eta)
    if eta<0: raise ValueError("eta must be nonnegative")
    return "E_EXACT" if eta<R(1,2) else "E_AMBIG"

def allowed_report_sets(true_level, ambiguous):
    return (true_level,"A") if ambiguous else (true_level,)

def hist_key(h):
    return tuple((int(i),SET_RANK[s]) for i,s in h)
def hist_text(h):
    return "NONE" if not h else "|".join(f"{i}:{s}" for i,s in h)

def realizations(timing_class, ambiguous):
    t=next(x for x in TIMING_CLASSES if x[0]==timing_class)
    _,a0,a1,a2=t
    out={p:[] for p in PATHS}
    for p in PATHS:
        x1,x2=LEVELS[p]
        o1=allowed_report_sets(x1,ambiguous) if a1 else (None,)
        o2=allowed_report_sets(x2,ambiguous) if a2 else (None,)
        for r1 in o1:
            for r2 in o2:
                h0=(("1",r1),) if a0 else tuple()
                h300=tuple(([("1",r1)] if a1 else [])+([("2",r2)] if a2 else []))
                item=(h0,h300,r1,r2)
                if item not in out[p]: out[p].append(item)
        out[p].sort(key=lambda x:(hist_key(x[0]),hist_key(x[1])))
    return out

def mask_intersection(feasible, paths, a1):
    z=None
    for p in paths:
        vals=set(feasible[p].get(a1,()))
        z=vals if z is None else z&vals
    return tuple(sorted(z or ()))

def solve_policy(U,feasible,timing_class,ambiguous):
    rz=realizations(timing_class,ambiguous)
    h0s=sorted({x[0] for v in rz.values() for x in v},key=hist_key)
    h300s=sorted({x[1] for v in rz.values() for x in v},key=hist_key)
    pred={}; paths_for=defaultdict(set)
    for p,v in rz.items():
        for h0,h300,_,_ in v:
            if h300 in pred and pred[h300]!=h0: raise RuntimeError("history predecessor conflict")
            pred[h300]=h0; paths_for[h300].add(p)
    candidates=[]
    for choices in itertools.product(U,repeat=len(h0s)):
        a1=dict(zip(h0s,choices)); a2={}; valid=True
        for h in h300s:
            common=mask_intersection(feasible,paths_for[h],a1[pred[h]])
            if not common: valid=False; break
            # Larger feasible tau2 strictly lowers its block pass count and also
            # wins the tertiary period-maximization tie-break.
            a2[h]=max(common)
        if not valid: continue
        costs={}; periods={}
        for p,v in rz.items():
            costs[p]=[]; periods[p]=[]
            for h0,h300,r1,r2 in v:
                aa,bb=a1[h0],a2[h300]
                costs[p].append(int(R(300)/aa)+int(R(300)/bb))
                periods[p].append((aa,bb,h0,h300,r1,r2))
        pw=tuple(max(costs[p]) for p in PATHS)
        pervec=tuple(q for p in PATHS for item in periods[p] for q in item[:2])
        key=(max(pw),pw,tuple(-q for q in pervec))
        candidates.append((key,a1,a2,costs,periods,rz))
    if not candidates: return None
    best=min(candidates,key=lambda x:x[0])
    primsec=best[0][:2]
    tied=sum(1 for x in candidates if x[0][:2]==primsec)
    return {
      "key":best[0],"a1":best[1],"a2":best[2],"costs":best[3],
      "periods":best[4],"realizations":best[5],
      "first_action_candidates":len(candidates),"primary_secondary_tie_count":tied,
    }

def stage_tree_case(trees,d,e):
    key=f"{d}_rho=0_eps={fs(e)}"
    if key not in trees: raise RuntimeError(f"missing Stage-A selected tree {key}")
    return trees[key]

def ideal_implementable(rz,ideal):
    for h0 in {x[0] for v in rz.values() for x in v}:
        acts={F(ideal[p]["tau1_s"]) for p,v in rz.items() for x in v if x[0]==h0}
        if len(acts)>1: return False
    for h in {x[1] for v in rz.values() for x in v}:
        acts={F(ideal[p]["tau2_s"]) for p,v in rz.items() for x in v if x[1]==h}
        if len(acts)>1: return False
    return True

def selected_matches_ideal(sol,ideal):
    for p,v in sol["realizations"].items():
        ia,ib=F(ideal[p]["tau1_s"]),F(ideal[p]["tau2_s"])
        for h0,h300,_,_ in v:
            if sol["a1"][h0]!=ia or sol["a2"][h300]!=ib: return False
    return True

def selected_equals_pre(sol,pre):
    pa,pb=F(pre["LL"]["tau1_s"]),F(pre["LL"]["tau2_s"])
    for p,v in sol["realizations"].items():
        for h0,h300,_,_ in v:
            if sol["a1"][h0]!=pa or sol["a2"][h300]!=pb: return False
    return True

def write_csv(path,rows,fields):
    with path.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=fields,extrasaction="ignore",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

def run(stage_dir:Path,out_dir:Path):
    config,sa,m,root_art,passing,trees=load_stage(stage_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    U=tuple(m["U"])
    regs=region_rows()
    write_csv(out_dir/"information_regions.csv",regs,list(regs[0]))
    boundary={
      "decision_times_s":[0,300],
      "sample_contract":{"s1":"0 <= s1 < 300","s2":"300 <= s2 < 600","ell":"ell >= 0"},
      "availability_predicates":{
        "A0":"enabled1 AND s1=0 AND ell=0",
        "A1":"enabled1 AND s1+ell<=300 (equality included)",
        "A2":"enabled2 AND s2=300 AND ell=0",
      },
      "logical_constraint":"A0 implies A1, hence exactly six timing signatures",
      "eta_boundary":{
        "exact":"0 <= eta < 1/2: intervals around b_L and b_H are disjoint, so every valid delivered report is singleton",
        "ambiguous":"eta >= 1/2: overlap exists; at eta=1/2 equality y=(b_L+b_H)/2 already permits {b_L,b_H}",
      },
      "aligned_enabled_samples":{
        "s1=0,s2=300,ell=0":"T111",
        "s1=0,s2=300,0<ell<=300":"T010",
        "s1=0,s2=300,ell>300":"T000",
      },
      "regions":regs,
      "scope":"Stage-A contract only; no pre-window observations; not a real-sensor latency limit",
    }
    (out_dir/"information_boundaries.json").write_text(json.dumps(boundary,indent=2)+"\n",encoding="utf-8")
    eligible=eligible_rho0_cases(passing)
    detail=[]; summary=[]; breakpoints=[]
    root_store=root_art["nonempty_searched_cases"]
    for d,e,pre_count,root_count in eligible:
        cid=f"{d}_rho=0_eps={fs(e)}"
        if cid not in root_store: raise RuntimeError(f"passing roots missing for {cid}")
        roots,feasible=parse_case_encoding(root_store[cid],U)
        if len(roots)!=root_count: raise RuntimeError(f"root count mismatch for {cid}")
        st=stage_tree_case(trees,d,e)
        ideal=st["Causal"]; pre=st["Precomputed"]
        pre_pass=int(pre["LL"]["passes"])
        ideal_pass={p:int(ideal[p]["passes"]) for p in PATHS}
        for reg in regs:
            t=reg["timing_class"]; amb=(reg["eta_class"]=="E_AMBIG")
            sol=solve_policy(U,feasible,t,amb)
            if sol is None: raise RuntimeError(f"unexpected no imperfect policy {cid} {reg['region_id']}")
            imp=ideal_implementable(sol["realizations"],ideal)
            match=selected_matches_ideal(sol,ideal)
            eqpre=selected_equals_pre(sol,pre)
            for p in PATHS:
                vals=[]
                for h0,h300,r1,r2 in sol["realizations"][p]:
                    a,b=sol["a1"][h0],sol["a2"][h300]
                    q,raw,D,A=sa.cert(m,*sa.rates(m,d,p),R(0),a,b)
                    if q>e: raise RuntimeError("selected action violates reused certificate")
                    ps,rd,wr,oc,of=sa.res(m,a,b)
                    vals.append(ps)
                    detail.append({
                      "case_id":cid,"shield_mm":d[1:],"epsilon":fs(e),
                      "region_id":reg["region_id"],"timing_class":t,"eta_class":reg["eta_class"],
                      "path":p,"h0":hist_text(h0),"h300":hist_text(h300),
                      "report1":r1 or "NONE","report2":r2 or "NONE",
                      "tau1_s":fs(a),"tau2_s":fs(b),"Q":sc(q),"certificate_margin":sc(e-q),
                      "passes":ps,"reads":rd,"writes":wr,"occupied_s":fs(oc),
                      "occupied_fraction":sc(of),"occupied_percent":f"{100*float(of):.9f}",
                    })
                p_worst=max(vals); p_best=min(vals)
                den=pre_pass-ideal_pass[p]
                gain=pre_pass-p_worst
                ret=None if den<=0 else R(gain,den)
                pp_saved=100*float(m["P"]*gain/m["T"])
                summary.append({
                  "case_id":cid,"shield_mm":d[1:],"epsilon":fs(e),
                  "region_id":reg["region_id"],"timing_class":t,"eta_class":reg["eta_class"],
                  "path":p,"ideal_action_implementable":int(imp),
                  "selection_matches_ideal":int(match),"policy_equals_precomputed_all_reports":int(eqpre),
                  "guaranteed_cost_equals_precomputed":int(p_worst==pre_pass),
                  "precomputed_passes":pre_pass,"ideal_passes":ideal_pass[p],
                  "imperfect_best_report_passes":p_best,"imperfect_worst_report_passes":p_worst,
                  "guaranteed_pass_saving":gain,"ideal_pass_saving":den,
                  "retention":("NA" if ret is None else f"{float(ret):.12g}"),
                  "guaranteed_occupied_s_saving":fs(m["P"]*gain),
                  "guaranteed_occupancy_percentage_points":f"{pp_saved:.9f}",
                  "first_action_candidate_maps":sol["first_action_candidates"],
                  "primary_secondary_tie_count":sol["primary_secondary_tie_count"],
                  "primary_information_limit":(
                     "NONE" if match else
                     ("UNCERTAINTY" if amb and t=="T111" else
                      "TIMING+UNCERTAINTY" if amb else "TIMING")
                  ),
                  "grid_certificate_note":"frozen Stage-A U/Q; no new grid/certificate sweep",
                })
                if ret is not None:
                    breakpoints.append({
                      "case_id":cid,"path":p,"region_id":reg["region_id"],
                      "retention":f"{float(ret):.12g}",
                    })
    write_csv(out_dir/"policy_region_map.csv",detail,list(detail[0]))
    write_csv(out_dir/"resource_summary.csv",summary,list(summary[0]))
    write_csv(out_dir/"retention_breakpoints.csv",breakpoints,list(breakpoints[0]))
    # Commit the two large tabular outputs in deterministic gzip+base64 form;
    # decoded CSVs are still generated in every reproduction run.
    for name in ("policy_region_map.csv","resource_summary.csv"):
        src=out_dir/name
        packed=base64.b64encode(gzip.compress(src.read_bytes(),mtime=0)).decode()+"\n"
        (out_dir/(name+".gz.b64")).write_text(packed,encoding="utf-8")
    distinct_bp=defaultdict(set)
    for r in breakpoints: distinct_bp[(r["case_id"],r["path"])].add(r["retention"])
    bp_json={f"{k[0]}:{k[1]}":sorted(v,key=float) for k,v in distinct_bp.items()}
    all3={}
    for d,e,_,_ in eligible:
        cid=f"{d}_rho=0_eps={fs(e)}"
        rows=[x for x in summary if x["case_id"]==cid]
        z={}
        for reg in regs:
            rr=[x for x in rows if x["region_id"]==reg["region_id"] and x["path"] in ("LL","LH","HL")]
            positive=all(int(x["guaranteed_pass_saving"])>0 for x in rr)
            if positive:
                z[reg["region_id"]]=min(float(x["retention"]) for x in rr)
        all3[cid]=z
    compact={
      "task_id":"STAGE-A-INFORMATION-INTERFACE-01",
      "rho":"0",
      "eligible_stage_a_cases":[f"{d}_rho=0_eps={fs(e)}" for d,e,_,_ in eligible],
      "timing_class_count":6,"eta_class_count":2,"information_region_count":12,
      "ideal_action_region":"T111_E_EXACT only in every eligible case",
      "guaranteed_ambiguity_result":"for eta>=0.5, worst-report cost equals Precomputed in every timing class and eligible case",
      "positive_guaranteed_savings_all_LL_LH_HL":all3,
      "retention_breakpoints":bp_json,
      "scope":"conditional on Stage-A two-level/no-pre-window-observation contract",
    }
    (out_dir/"summary.json").write_text(json.dumps(compact,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return compact

def validate_new_config(path: Path):
    c=json.loads(path.read_text(encoding="utf-8"))
    if c.get("task_id")!="STAGE-A-INFORMATION-INTERFACE-01":
        raise RuntimeError("unexpected task config")
    if F(c["information_channel"]["eta_equivalence_boundary"])!=R(1,2):
        raise RuntimeError("eta boundary config mismatch")
    if c["fixed_model"]["rho"]!="0" or c["fixed_model"]["decision_times_s"]!=["0","300"]:
        raise RuntimeError("fixed Stage-A information-study contract mismatch")
    return c

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",required=True,type=Path)
    ap.add_argument("--stage-a-dir",required=True,type=Path)
    ap.add_argument("--output-dir",required=True,type=Path)
    x=ap.parse_args()
    validate_new_config(x.config)
    z=run(x.stage_a_dir,x.output_dir)
    print(json.dumps({"status":"PASS","regions":z["information_region_count"],
                      "cases":len(z["eligible_stage_a_cases"])},sort_keys=True))
if __name__=="__main__": main()
