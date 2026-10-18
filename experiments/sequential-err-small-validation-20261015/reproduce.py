"""One command: source/plan audit, E exact chain, independent MC, table and figure."""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
from arithmetic import enclosure
from exact import cases,solve
from enumerated import reference
from mc import monte_carlo
from checks import run_checks

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/"outputs"
PREREG="b11115a7d7bd422c0271dcce8f5d93e935570bd8"

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def source_audit():
    manifest=json.loads((HERE/"sources.json").read_bytes())
    for source in manifest["sources"]:
        raw=subprocess.check_output(["git","show",source["commit"]+":"+source["path"]],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==source["sha256"],source["id"]
        assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()==source["git_blob"]
        assert (ROOT/source["path"]).read_bytes()==raw,source["id"]+" changed in checkout"
    for name,expected in manifest["preregistration_sha256"].items():
        assert digest(HERE/name)==expected,name+" changed after preregistration"
        raw=subprocess.check_output(["git","show",PREREG+":"+
            (HERE/name).relative_to(ROOT).as_posix()],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==expected,name+" differs from pinned commit"
    old="experiments/sequential-small-validation-20261014"
    tree=subprocess.check_output(["git","rev-parse","HEAD:"+old],cwd=ROOT,text=True).strip()
    assert tree==manifest["accepted_U_tree"],"accepted U tree changed"
    assert not subprocess.check_output(["git","diff","HEAD","--",old],cwd=ROOT).strip()
    return len(manifest["sources"])

def ratio(a,b): return None if b==0 else float(a/b)

def differences(exact,mc):
    ql,qh=[F(exact["Q_exact"][k]) for k in ("lower","upper")]
    ll,lh=[F(exact["L"][k]) for k in ("lower","upper")]
    u=F(exact["U_E_rational"]); q=(ql+qh)/2; l=(ll+lh)/2
    m=F(mc["events_Q"],mc["trials"])
    return dict(exact_minus_L=enclosure(ql-lh,qh-ll),
        U_minus_exact=enclosure(u-qh,u-ql),U_minus_L=enclosure(u-lh,u-ll),
        L_relative_shortfall=ratio(q-l,q),U_relative_excess=ratio(u-q,q),
        width_relative_to_exact=ratio(u-l,q),MC_absolute_difference=str(float(abs(m-q))),
        MC_relative_difference=ratio(abs(m-q),q),
        exact_in_pointwise_CI=mc["CI_95_pointwise"][0]<=float(q)<=mc["CI_95_pointwise"][1])

def table(rows):
    lines=["| W | λ | D, с | L | Q_exact*; δ_num | U_E | Q_MC [95% CI] | Q−L | U_E−Q | U_E−L | (Q−L)/Q | (U_E−Q)/Q | (U_E−L)/Q | abs(MC−Q) |",
           "|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        x,m,d=r["exact"],r["MC"],r["differences"]
        fmt=lambda k:f'{float(d[k]["midpoint"]):.6f}'
        rel=lambda k:"не определено" if d[k] is None else f'{100*d[k]:.3f}%'
        lo,hi=m["CI_95_pointwise"]
        label="const" if r["profile"]=="constant" else "piece"
        lines.append(f'| {r["W"]} | {label} | {float(F(r["D_s"])):.2f} | '
            f'{float(x["L"]["midpoint"]):.6f} | {float(x["Q_exact"]["midpoint"]):.9f}; '
            f'{float(x["Q_exact"]["absolute_error"]):.1e} | {float(x["U_E"]["midpoint"]):.6f} | '
            f'{m["Q_MC"]:.6f} [{lo:.6f}; {hi:.6f}] | {fmt("exact_minus_L")} | '
            f'{fmt("U_minus_exact")} | {fmt("U_minus_L")} | {rel("L_relative_shortfall")} | '
            f'{rel("U_relative_excess")} | {rel("width_relative_to_exact")} | '
            f'{float(d["MC_absolute_difference"]):.6f} |')
    return "\n".join(lines)

def plot(rows):
    import os
    cache=HERE/".cache"/"matplotlib"; cache.mkdir(parents=True,exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR",str(cache))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"]="T177-b11115a"
    import matplotlib.pyplot as plt
    import numpy as np
    y=np.arange(len(rows))
    labels=[f'W={r["W"]}, '+("const" if r["profile"]=="constant" else "piece")+
            f', D={float(F(r["D_s"])):g}' for r in rows]
    q=np.array([float(r["exact"]["Q_exact"]["midpoint"]) for r in rows])
    l=[float(r["exact"]["L"]["midpoint"]) for r in rows]
    u=[float(r["exact"]["U_E"]["midpoint"]) for r in rows]
    v=[float(F(r["exact"]["V_rational"])) for r in rows]
    m=np.array([r["MC"]["Q_MC"] for r in rows])
    ci=np.array([r["MC"]["CI_95_pointwise"] for r in rows])
    fig,(ax,bx)=plt.subplots(1,2,figsize=(11.4,4.9),sharey=True,
        gridspec_kw={"width_ratios":[1.4,1]},layout="constrained")
    ax.hlines(y,l,u,color="#9099a3",linewidth=4,label="L–U_E")
    ax.hlines(y,v,u,color="#c78a38",linewidth=4,label="вклад X_E в верх")
    ax.plot(q,y,"D",color="#9c2f38",markersize=4,label="точный Q")
    ax.errorbar(m,y+.12,xerr=[m-ci[:,0],ci[:,1]-m],fmt="o",markersize=3,
                color="#236aa3",capsize=2,label="MC, поточечный 95% CI")
    ax.set_yticks(y,labels,fontsize=9);ax.invert_yaxis()
    ax.set_xlabel("Вероятность первого превышения SEC")
    ax.set_title("Малая E/full38-модель")
    ax.legend(fontsize=8,loc="lower right")
    bx.axvline(0,color="#9c2f38",linewidth=1)
    bx.errorbar(m-q,y,xerr=[m-ci[:,0],ci[:,1]-m],fmt="o",color="#236aa3",capsize=3)
    bx.set_xlabel("Q_MC − Q_exact; тот же CI со сдвигом")
    bx.set_title("Статистическое расхождение отдельно")
    bx.ticklabel_format(axis="x",style="sci",scilimits=(-3,-3))
    for a in (ax,bx): a.grid(axis="x",alpha=.2);a.set_axisbelow(True)
    fig.suptitle("Запись только по ERR; T=3,4 с; N=200000 на точку",fontsize=11)
    fig.savefig(OUT/"comparison.png",dpi=170)
    fig.savefig(OUT/"comparison.svg",metadata={"Date":None})
    svg=OUT/"comparison.svg"
    svg.write_text("\n".join(s.rstrip() for s in svg.read_text(encoding="utf-8").splitlines())+"\n",
                   encoding="utf-8",newline="\n")
    plt.close(fig)

def write_json(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
                         encoding="utf-8",newline="\n")

def main():
    started=time.perf_counter();OUT.mkdir(exist_ok=True)
    cfg=json.loads((HERE/"inputs.json").read_bytes())
    source_count=source_audit()
    checks=run_checks(cfg)
    assert ratio(F(0),F(0)) is None
    checks.append("zero relative denominator remains undefined")
    rows=[]
    for c in cases(cfg):
        x=solve(c,cfg["exact"]["maximum_uniformization_index"],
                cfg["exact"]["internal_decimal_places"],cfg["exact"]["output_decimal_places"])
        width=F(x["Q_exact"]["upper"])-F(x["Q_exact"]["lower"])
        assert width<=F(cfg["exact"]["max_enclosure_width"])
        ref=reference(c)
        diff=abs(ref["Q"]-float(x["Q_exact"]["midpoint"]))
        assert diff<2e-12,c["id"]+" disagrees with full-memory enumeration"
        mc=monte_carlo(c,cfg["mc"]["trials_per_case"],cfg["mc"]["seed_base"])
        rows.append(dict(id=c["id"],case_index=c["index"],W=c["W"],n=c["n"],profile=c["profile"],
            D_s=str(c["D"]),T_s=str(c["T"]),status="OWN_RESULT; independent review pending",
            exact=x,enumerated_reference={**ref,"difference_from_certified_midpoint":diff},
            MC=mc,differences=differences(x,mc)))
        print(c["id"],"Q="+format(float(x["Q_exact"]["midpoint"]),".12f"),
              "MC="+str(mc["events_Q"])+"/"+str(mc["trials"]),flush=True)
    files=["inputs.json","PLAN.md","sources.json","arithmetic.py","exact.py","enumerated.py","mc.py",
           "checks.py","reproduce.py","requirements.txt"]
    if (HERE/"METHOD.md").exists(): files.append("METHOD.md")
    result=dict(task=177,date="2026-10-18",base=cfg["base"],preregistration_commit=PREREG,
        service=cfg["service"],service_times=cfg["service_times"],process=cfg["events"],
        failure_event="ever more than one incorrect bit beforeT; irreversible historical event",
        source_sha256={n:digest(HERE/n) for n in files},
        software=dict(python=platform.python_version(),packages={n:importlib.metadata.version(n)
            for n in ["numpy","scipy","matplotlib"]}),cases=rows)
    write_json("results.json",result)
    rendered=table(rows)
    (OUT/"table.md").write_text(rendered+"\n",encoding="utf-8",newline="\n")
    report=HERE/"REPORT.md"
    matches=None if not report.exists() else rendered in report.read_text(encoding="utf-8")
    if matches is False: raise AssertionError("REPORT table differs from generated table")
    plot(rows)
    validation=dict(status="PASS",source_files_checked=source_count,preregistration_hashes_checked=2,
        accepted_U_tree_unchanged=True,accepted_U_reexecuted=False,directed_checks=checks,
        cases_certified=len(rows),full_memory_references_passed=len(rows),
        total_MC_trials=sum(r["MC"]["trials"] for r in rows),MC_counts=[r["MC"]["events_Q"] for r in rows],
        pointwise_CI_contains_exact=[r["differences"]["exact_in_pointwise_CI"] for r in rows],
        max_exact_interval_width=max(float(F(r["exact"]["Q_exact"]["upper"])-
            F(r["exact"]["Q_exact"]["lower"])) for r in rows),
        max_full_memory_reference_difference=max(r["enumerated_reference"]["difference_from_certified_midpoint"]
            for r in rows),max_mass_drift_full_memory=max(r["enumerated_reference"]["max_mass_drift"] for r in rows),
        report_table_matches=matches,results_sha256=digest(OUT/"results.json"),
        statistical_note="CI coverage is pointwise; misses are reported and are not a PASS criterion",
        scope="Eight synthetic E/full38 cases; not mission probability or physical CY62167 qualification")
    write_json("validation.json",validation)
    print("PASS:",len(checks),"directed checks,",len(rows),"certified E rows; elapsed seconds",
          format(time.perf_counter()-started,".3f"),flush=True)

if __name__=="__main__": main()
