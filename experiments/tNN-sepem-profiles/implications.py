"""Arithmetic consequences only; never issue or modify a memory certificate."""
import ast
import csv
import hashlib
import json
import math
from pathlib import Path
import zipfile
import numpy as np
from analysis import write_csv
from baseline import calculate

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]


def historical_components():
    """Execute only the explicitly inspected original pure functions.

    Shared historical functions make this a reproduction, not an independent
    physical confirmation. No top-level pickle, write, or original script runs.
    """
    root=REPO/"experiments/t68-v21-inputs"
    ns={"np":np,"math":math,"Nbits":2**24,"ssat":2.6e-7,"L0w":.15,"W":70.,"h":1.2,
        "LETpts":np.array([5.2,15,17,22,27,29,33,42,57]),
        "frac":np.array([1,1,1,1,1,1,1,16969/17012,21058/21185]),
        "Epdi":np.array([.6,.7,.8,.9,1,1.1,1.5,2,2.5,3,4,5]),
        "Spdi":np.array([4.1e-11,1.36e-10,1.06e-9,9.4e-10,1.30e-9,4.1e-10,5.65e-11,4.7e-12,1.6e-12,6.1e-13,1.47e-13,6.7e-14])}
    selected={"spectra_lib.py":{"make_phi","trapz","rate_naive"},
              "orbital.py":{"sb","fr","sig_nak","sig_p_710"},"sep.py":{"sig_p_pdi","rate_pl"}}
    with zipfile.ZipFile(root/"inputs/calc_v18.zip") as archive:
        for name,names in selected.items():
            tree=ast.parse(archive.read(name).decode())
            functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names]
            if {x.name for x in functions}!=names:
                raise ValueError("Historical function contract changed")
            exec(compile(ast.Module(body=functions,type_ignores=[]),name,"exec"),ns)
    def table(name):
        rows=[]
        for line in (root/"inputs/cosrad_main"/name).read_text().splitlines():
            try:
                row=list(map(float,line.split()))
            except ValueError:
                continue
            if len(row)==10:
                rows.append(row)
        return np.array(rows)
    L,phi=ns["make_phi"](7,table("sl_x.txt"))
    ion=float(ns["rate_naive"](L,np.where(L<=32.6,phi,0),ns["sig_nak"])*38/32)
    proton={kind:float(ns["rate_pl"](7,table("sp_x.txt"),ns[sigma])*2**24*38/32)
            for kind,sigma in (("HEP","sig_p_710"),("PDI_HEP","sig_p_pdi"))}
    old=calculate()
    mismatch=max(abs(ion+proton[k]-float(old[key])) for k,key in
                 (("HEP","historical_nu_S_per_s"),("PDI_HEP","historical_nu_S_PDI_per_s")))
    if mismatch>1e-12:
        raise ValueError("Historical component reproduction failed")
    return {"value_type":"calculated_historical_reproduction","LET_ion_s-1":ion,
            "proton_s-1":proton,"LET_fraction_of_historical_nuS":ion/(ion+proton["HEP"]),
            "LET_only_old_rectangle_S2_s-1":ion**2*115776,
            "maximum_absolute_reproduction_difference":mismatch,
            "scope":"Historical aggregate LET includes unresolved species; not a new He or Z>=3 temporal estimate",
            "sources_sha256":{str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                (root/"inputs/calc_v18.zip",root/"inputs/cosrad_main/sl_x.txt",root/"inputs/cosrad_main/sp_x.txt")}}


def main():
    out=HERE/"outputs"
    base=calculate()
    c=37/(76*2**19)*.108
    rows=[{"model":"old_accepted_full38_rounded","S2_s-1":6940.,
           "arithmetic_Q_acc":c*6940,"fraction_of_1e-3":c*6940/.001,
           "formal_difference_from_old_acc":0.,"value_type":"calculated"}]
    for filename,field in (("mission-model-B.csv","q90"),("design-model-A.csv","S2_s-1")):
        with (out/filename).open() as stream:
            for row in csv.DictReader(stream):
                if row["variant"]!="csda_3_pdi" or not row[field]:
                    continue
                s=float(row[field])
                label="A_H_only_"+row["shape_rule"] if "shape_rule" in row else "B_empirical_q90_H_only"
                rows.append({"model":label,
                    "S2_s-1":s,"arithmetic_Q_acc":c*s,"fraction_of_1e-3":c*s/.001,
                    "formal_difference_from_old_acc":c*(6940-s),"value_type":"calculated_from_conditional_estimate"})
    for row in rows:
        row["interpretation"]="arithmetic only; not a new Q bound, freed allowance, or policy/certificate change"
    write_csv(out/"probability-arithmetic.csv",rows)
    result={"historical":historical_components(),"multiplier_s":c,
            "issued_replacement_S2_s-1":None,"established_freed_probability":None,
            "old_accumulation":float(base["requested_old_accumulation_bound"]),
            "old_direct":float(base["requested_direct_bound"]),
            "old_remaining":float(base["requested_remaining_probability"]),
            "blocker":"Full R0-A species/response/time-envelope transfer and joint exceedance are not established by the empirical proton model",
            "accepted_rules_or_certificates_modified":False}
    (out/"implications.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
