#!/usr/bin/env python3
"""C1-C5 only: refine accepted price, without new periods or stochastic runs."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from itertools import product
import hashlib, json, sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SOURCE=HERE.parent/"theory/result.json"
EXPECTED="ed9e06357483e2d69944a66ff670c39ddc36799f58b74b4bdee93e8333d27f04"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
src=json.loads(SOURCE.read_text(encoding="utf-8"))
W,T=131072,315576000
dc=F(1,20000)
nh=src["constants"]["hard_reads"]

def ends(K,k):
    """All complete-pass endpoints of a single already selected cell."""
    return tuple([2]+list(range(2+k,K,k))+[K])

def ceil(x):
    return -((-x.numerator)//x.denominator)

def fmt(x,places=9,upper=True):
    with localcontext() as ctx:
        ctx.prec=100
        return str((Decimal(x.numerator)/Decimal(x.denominator)).quantize(
            Decimal(1).scaleb(-places),rounding=ROUND_CEILING if upper else ROUND_FLOOR))

rows=[]
for old in src["rows"]:
    a,rv=old["adaptive"],old["rivals"]
    row={"epsilon":old["epsilon"],"rivals":rv,"adaptive_status":a["status"]}
    if "k_base" not in a:
        row["conclusion"]="No new adaptive Q; preserve accepted optional-point residue."
        rows.append(row)
        continue
    K,kb,ks=a["cell_blocks"],a["k_base"],a["k_rare"]
    b,s=ends(K,kb),ends(K,ks)
    nb,ns=len(b),len(s)
    assert kb<=ks and nb>=ns
    assert nb==1+ceil(F(K-2,kb))==a["baseline_passes_per_cell"]
    assert ns==1+ceil(F(K-2,ks))==a["rare_passes_per_cell"]
    N=a["attempts_upper"]; mb=W*(1+N*nb)
    assert mb==a["main_reads_hard_on_good_execution"] and mb<nh
    # Finite check of arbitrary choices, every terminal prefix, and a necessity example.
    # The induction for all choices is the proof C2, not this finite enumeration.
    assert all(sum((nb,ns)[x] for x in seq)<=6*nb for seq in product((0,1),repeat=6))
    assert max(sum(t<=cut for t in b) for cut in range(K+1))<=nb
    assert max(sum(t<=cut for t in s) for cut in range(K+1))<=nb
    union=len(set(b)|set(s))
    assert union>nb  # An erroneous double install cannot be called "one of two".
    dc_old=F(a["deltaC_design_cap"])
    assert dc==dc_old
    data={"k_base":kb,"k_rare":ks,"n_base":nb,"n_rare":ns,
          "M_b":mb,"N_cells_upper":N,"unsafe_union_passes":union,
          "delta_C_design_cap":dc,"delta_0":a["delta0"],
          "Q_upper_at_design_UNCHANGED":a["Q_upper_at_deltaC_design"],
          "risk_margin_UNCHANGED":a["risk_margin_at_design"],"coordinates":{}}
    for x in ("bus","core"):
        ch=F(a[f"{x}_deltaC_coefficient"])
        assert ch==F(src["constants"][f"hard_{x}"])
        cb=ch*F(mb,nh)
        u0=F(a[f"{x}_intercept_U0"])
        v=u0+dc*cb
        oldv=u0+dc*ch
        az=F(a[f"{x}_additional_invalid_coefficient"])
        ag=F(a[f"{x}_guard_read_coefficient"])
        comp={}
        for target in ("constant","schedule"):
            lower=F(rv[f"{target}_read_{x}_lower"])
            amounts={str(saving): (1-saving)*lower-v for saving in (F(1,5),F(3,10))}
            comp[target]={"rival_read_lower":lower,"allowance_20":amounts["1/5"],
                          "allowance_30":amounts["3/10"],
                          "diagnostic_saving_at_zero_unpriced_additions":1-v/lower,
                          "status_20":"PARAMETRIC_SUFFICIENT_REGION" if amounts["1/5"]>0 else "THIS_CERTIFICATE_INSUFFICIENT"}
            if amounts["1/5"]>0:
                comp[target]["z_only_limit_NOT_ASSIGNED"]=amounts["1/5"]/az
                comp[target]["G_only_limit_NOT_ASSIGNED"]=amounts["1/5"]/ag
                comp[target]["escape_only_limit_NOT_ASSIGNED"]=amounts["1/5"]/(ch-cb)
        data["coordinates"][x]={"old_C_h":ch,"new_C_b":cb,
            "old_delta_C_charge":dc*ch,"new_delta_C_charge":dc*cb,
            "U0":u0,"V_at_design_delta_C":v,"old_V_at_design_delta_C":oldv,
            "price_improvement_exact":oldv-v,"A_z":az,"A_G":ag,
            "escape_coefficient":ch-cb,
            "unpriced":{"z":None,"G_expected_on_G0_including_BC_and_A":None,
                        "controller_average":None},
            "comparison":comp,
            "formula":"V + A_z*z + A_G*G + controller; optional escape_coefficient*delta_escape if two-calendar correspondence unproved"}
        assert oldv-v==dc*(ch-cb)
    row["adaptive"]=data
    rows.append(row)

out={"base_main":"c0864fff17eb1bdd28d66e81e4d9f7fc2acf4b22",
     "plan_commit":"c0af46478d5a97a4718929517635850d4f10be52",
     "source":{"path":SOURCE.relative_to(ROOT).as_posix(),"sha256":EXPECTED,
               "git_blob":"96d4b6e70ecddc437c42da1eca788a466b1eb464"},
     "status":"Author refinement C1-C5. Parameters and Q are unchanged; no physical quota or zero extra cost assigned.",
     "N_h":nh,"rows":rows,
     "CPU_energy":"Use all-history operation counts with unknown unit coefficients; bus/core results do not identify CPU or energy saving."}
encoded=json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2,default=str)+"\n"

def table():
    text=["# Два сравнения после уточнения цены счёта",
          "",
          "C1–C5, без перенастройки PR281. Во всех строках δ_C=5e−5 — прежнее",
          "**проектное условие**, не измерение. V — верх известной части с ценой",
          "δ_C и δ₀; к нему добавляются G/z/обработка. При отсутствии соответствия",
          "двум календарям сохраняется также член δ_escape. Q не пересчитывался.",
          ""]
    for x,name in (("bus","Чистая шина"),("core","Core, включая decode")):
        text += [f"## {name}","",
                 "| ε | V, % срока, вверх | L_F / L_S, %, вниз | Остаток20% F / S, мкс/с, вниз | Остаток30% F / S, мкс/с, вниз |",
                 "|---:|---:|---:|---:|---:|"]
        for row in rows:
            ep=str(float(F(row["epsilon"])))
            if "adaptive" not in row:
                text.append(f"| {ep} | Не сертифицировано | Отдельный постоянный кандидат | — | — |")
                continue
            d=row["adaptive"]["coordinates"][x]
            f,s=(d["comparison"][k] for k in ("constant","schedule"))
            def pair(key,scale=1,places=6):
                return " / ".join(fmt(q[key]*scale,places,False) for q in (f,s))
            text.append(f"| {ep} | {fmt(100*d['V_at_design_delta_C'],12)} | "
                        f"{pair('rival_read_lower',100,12)} | {pair('allowance_20',10**6)} | {pair('allowance_30',10**6)} |")
        text+=[""]
    text += ["Положительный остаток — достаточная область всех неустановленных",
             "добавок C5; их значения не приравнены нулю. Отрицательный остаток",
             "означает недостаточность этого сертификата, не невозможность А.",
             "L_F/L_S — нижние цены двух полных классов, не найденные оптимумы.",
             "CPU, энергия, память, пиковые сроки и приложение учитываются отдельно.",""]
    return "\n".join(text)

if "--write" in sys.argv:
    (HERE/"result.json").write_text(encoded,encoding="utf-8",newline="\n")
    (HERE/"TABLE.md").write_text(table(),encoding="utf-8",newline="\n")
    print("PASS: accepted snapshot/hash; C1 counts; 64 choices per epsilon; all terminal prefixes; double-install counterexample; C3/C5 bus/core.")
else:
    print(encoded,end="")

