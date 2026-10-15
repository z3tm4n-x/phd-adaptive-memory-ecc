"""One command: pinned-source audit, analytic tests, eight certified/MC rows, figure."""
from fractions import Fraction as F
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import time

from exact import cases,solve,enclosure
from enumerated import enumerate_reference
from mc import monte_carlo
from checks import run_checks

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/"outputs"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def source_audit():
    manifest=json.loads((HERE/"sources.json").read_bytes())
    for source in manifest["sources"]:
        raw=subprocess.check_output(["git","show",source["commit"]+":"+source["path"]],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==source["sha256"],source["id"]
        blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        assert blob==source["git_blob"],source["id"]
        current=(ROOT/source["path"]).read_bytes()
        assert current==raw,source["id"]+": source in checkout differs"
    for name,expected in manifest["preregistration_sha256"].items():
        assert digest(HERE/name)==expected,"preregistered input changed: "+name
    return len(manifest["sources"])

def ratio(value,denominator):
    return None if denominator==0 else float(value/denominator)

def differences(exact,mc):
    ql,qh=(F(exact["Q_exact"][k]) for k in ("lower","upper"))
    ll,lh=(F(exact["L"][k]) for k in ("lower","upper"))
    u=F(exact["U_rational"]); q=(ql+qh)/2; l=(ll+lh)/2
    qmc=F(mc["events_Q"],mc["trials"])
    low_gap=enclosure(ql-lh,qh-ll)
    high_gap=enclosure(u-qh,u-ql)
    width=enclosure(u-lh,u-ll)
    return dict(exact_minus_L=low_gap,U_minus_exact=high_gap,U_minus_L=width,
        L_relative_shortfall=ratio(q-l,q),U_relative_excess=ratio(u-q,q),
        width_relative_to_exact=ratio(u-l,q),
        MC_absolute_difference=str(float(abs(qmc-q))),
        MC_relative_difference=ratio(abs(qmc-q),q),
        exact_in_pointwise_CI=mc["CI_95_pointwise"][0]<=float(q)<=mc["CI_95_pointwise"][1])

def table(rows):
    lines=[
        "| W | λ | D, с | L | Q_exact* | U | Q_MC [95% CI] | Q−L | U−Q | U−L | (Q−L)/Q | (U−Q)/Q | (U−L)/Q | |Q_MC−Q| |",
        "|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|"]
    # Escape absolute-value bars in the Markdown header.
    lines[0]=lines[0].replace("| |Q_MC−Q| |","| abs(Q_MC−Q) |")
    for row in rows:
        x,m,d=row["exact"],row["MC"],row["differences"]
        rel=lambda key:"не определено" if d[key] is None else f'{100*d[key]:.3f}%'
        label="const" if row["profile"]=="constant" else "piece"
        lo,hi=m["CI_95_pointwise"]
        lines.append(f'| {row["W"]} | {label} | {float(F(row["D_s"])):.2f} | '
            f'{float(x["L"]["midpoint"]):.6f} | {float(x["Q_exact"]["midpoint"]):.6f} | '
            f'{float(x["U"]["midpoint"]):.6f} | {m["Q_MC"]:.6f} [{lo:.6f}; {hi:.6f}] | '
            f'{float(d["exact_minus_L"]["midpoint"]):.6f} | {float(d["U_minus_exact"]["midpoint"]):.6f} | '
            f'{float(d["U_minus_L"]["midpoint"]):.6f} | {rel("L_relative_shortfall")} | '
            f'{rel("U_relative_excess")} | {rel("width_relative_to_exact")} | '
            f'{float(d["MC_absolute_difference"]):.6f} |')
    return "\n".join(lines)

def plot(rows):
    import os
    cache=HERE/".cache"/"matplotlib"
    cache.mkdir(parents=True,exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR",str(cache))
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"]="T166-1627981"
    import matplotlib.pyplot as plt
    import numpy as np
    labels=[f'W={r["W"]}, '+("const" if r["profile"]=="constant" else "piece")
            +f', D={float(F(r["D_s"])):g}' for r in rows]
    y=np.arange(len(rows))
    q=np.array([float(r["exact"]["Q_exact"]["midpoint"]) for r in rows])
    l=np.array([float(r["exact"]["L"]["midpoint"]) for r in rows])
    u=np.array([float(r["exact"]["U"]["midpoint"]) for r in rows])
    m=np.array([r["MC"]["Q_MC"] for r in rows])
    ci=np.array([r["MC"]["CI_95_pointwise"] for r in rows])
    fig,(ax,bx)=plt.subplots(1,2,figsize=(11.2,4.8),sharey=True,
                             gridspec_kw={"width_ratios":[1.35,1]},layout="constrained")
    ax.hlines(y,l,u,color="#88929d",linewidth=4,label="L–U")
    ax.plot(q,y,"D",color="#9c2f38",markersize=4,label="Точный Q")
    ax.errorbar(m,y+.12,xerr=[m-ci[:,0],ci[:,1]-m],fmt="o",markersize=3,
                color="#236aa3",capsize=2,label="MC, 95% поточечный CI")
    ax.set_yticks(y,labels,fontsize=9);ax.invert_yaxis()
    ax.set_xlabel("Вероятность первого превышения SEC")
    ax.set_title("Границы и малый эталон")
    ax.legend(fontsize=8,loc="lower right")
    bx.axvline(0,color="#9c2f38",linewidth=1)
    bx.errorbar(m-q,y,xerr=[m-ci[:,0],ci[:,1]-m],fmt="o",color="#236aa3",capsize=3)
    bx.set_xlabel("Q_MC − Q_exact; тот же CI со сдвигом")
    bx.set_title("Статистическая погрешность отдельно")
    bx.ticklabel_format(axis="x",style="sci",scilimits=(-3,-3))
    for a in (ax,bx):
        a.grid(axis="x",alpha=.2);a.set_axisbelow(True)
    fig.suptitle("Последовательный U, full39; T=3,4 с; N=200000 на точку",fontsize=11)
    fig.savefig(OUT/"comparison.png",dpi=170)
    fig.savefig(OUT/"comparison.svg",metadata={"Date":None})
    svg=OUT/"comparison.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines())+"\n",
                   encoding="utf-8",newline="\n")
    plt.close(fig)

def write_json(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",
                         encoding="utf-8",newline="\n")

def main():
    started=time.perf_counter()
    OUT.mkdir(exist_ok=True)
    cfg=json.loads((HERE/"inputs.json").read_bytes())
    pinned=source_audit()
    checks=run_checks(cfg)
    assert ratio(F(0),F(0)) is None
    checks.append("zero denominator stays undefined")
    rows=[]
    for case in cases(cfg):
        exact=solve(case,cfg["exact"]["uniformization_terms"],cfg["exact"]["output_decimal_places"])
        box=exact["Q_exact"]
        assert F(box["upper"])-F(box["lower"])<=F(cfg["exact"]["max_enclosure_width"])
        reference=enumerate_reference(case)
        delta=abs(reference["Q"]-float(box["midpoint"]))
        assert delta<=2e-12,"full-state reference differs: "+case["id"]
        mc=monte_carlo(case,cfg["mc"]["trials_per_case"],cfg["mc"]["seed_base"])
        rows.append(dict(id=case["id"],case_index=case["index"],W=case["W"],n=case["n"],
            profile=case["profile"],D_s=str(case["D"]),T_s=str(case["T"]),
            status="OWN_RESULT; pending independent review",
            exact=exact,enumerated_reference={**reference,"difference_from_certified_midpoint":delta},
            MC=mc,differences=differences(exact,mc)))
        print(case["id"],"Q="+format(float(box["midpoint"]),".12f"),
              "MC="+str(mc["events_Q"])+"/"+str(mc["trials"]),flush=True)
    files=["inputs.json","sources.json","PLAN.md","exact.py","enumerated.py","mc.py","checks.py",
           "reproduce.py","requirements.txt","METHOD.md"]
    versions={name:importlib.metadata.version(name) for name in ["numpy","scipy","matplotlib"]}
    result=dict(task=166,preregistration_commit="1627981320243d5537f50b89a17f268bfd05fa46",
        base=cfg["base"],process=cfg["events"],
        failure_event="exists t in [0,T],word: Hamming weight>1; absorbing even after correction",
        service=cfg["service"],initial_state=cfg["initial"],
        source_sha256={name:digest(HERE/name) for name in files},
        software=dict(python=platform.python_version(),packages=versions),cases=rows)
    write_json("results.json",result)
    rendered=table(rows)
    (OUT/"table.md").write_text(rendered+"\n",encoding="utf-8",newline="\n")
    report=HERE/"REPORT.md"
    report_matches=None if not report.exists() else rendered in report.read_text(encoding="utf-8")
    if report_matches is False:
        raise AssertionError("REPORT table must be refreshed from outputs/table.md; no silent stale numbers")
    plot(rows)
    validation=dict(status="PASS",source_files_checked=pinned,preregistration_hashes_checked=2,
        directed_checks=checks,cases_certified=len(rows),enumerated_references_passed=len(rows),
        total_MC_trials=sum(r["MC"]["trials"] for r in rows),
        MC_counts=[r["MC"]["events_Q"] for r in rows],
        pointwise_CI_contains_exact=[r["differences"]["exact_in_pointwise_CI"] for r in rows],
        max_exact_interval_width=max(float(F(r["exact"]["Q_exact"]["upper"])
            -F(r["exact"]["Q_exact"]["lower"])) for r in rows),
        max_global_mass_drift=max(r["enumerated_reference"]["max_mass_drift"] for r in rows),
        max_global_reference_difference=max(r["enumerated_reference"]["difference_from_certified_midpoint"] for r in rows),
        report_table_matches=report_matches,results_sha256=digest(OUT/"results.json"),
        statistical_note="Pointwise coverage; an individual miss is not a failed mathematical bound",
        scientific_scope="Eight synthetic singleton U cases; not general theorem proof or physical qualification")
    write_json("validation.json",validation)
    print("PASS:",len(checks),"directed checks,",len(rows),"certified rows; elapsed seconds",
          format(time.perf_counter()-started,".3f"))

if __name__=="__main__":
    main()
