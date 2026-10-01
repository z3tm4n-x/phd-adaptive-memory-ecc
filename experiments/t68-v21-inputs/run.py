"""T68: reproduce supplied code and audit its v21 interpretation.

No COSRAD executable, irradiation, adaptive simulation or RTL is run.
The original scripts run only in .cache. All pickle inputs are generated here.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
from decimal import Decimal
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import urllib.request
import zipfile

import numpy as np
from scipy.integrate import quad

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "outputs"
CHILD_ENV = {**os.environ, "PYTHONUTF8": "1"}
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
HI = {"C1080MeV": .23, "C720MeV": .31, "C360MeV": .53,
      "Ar1050MeV": 5.2, "Ar548MeV": 7.9, "U190.4GeV": 15,
      "U142.8GeV": 17, "U78.5GeV": 22, "XeLET27": 27,
      "U45.2GeV": 29, "U35.7GeV": 33, "XeLET42": 42,
      "Xe2700MeV": 44, "XeLET57": 57}
GOOD = [0, 1, 2, 3, 5, 8, 10, 11, 12, 13, 15]
PAIRS = list(itertools.combinations(GOOD, 2))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8")


def write_csv(name, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def function_namespace(path, **values):
    """Reuse original functions, without executing original top-level scripts."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    ns = {"np": np, "math": math, "defaultdict": defaultdict, **values}
    exec(compile(tree, str(path), "exec"), ns)
    return ns


def read_table(path, columns):
    rows = []
    for line in path.read_text(encoding="latin-1").splitlines():
        parts = line.split()
        if len(parts) == columns:
            try:
                rows.append([float(x) for x in parts])
            except ValueError:
                pass
    table = np.asarray(rows)
    if table.ndim != 2 or len(table) < 2 or np.any(np.diff(table[:, 0]) <= 0):
        raise ValueError(f"Invalid spectrum {path}")
    return table


def effective_duration(fluence, peak):
    if fluence.shape != peak.shape or not np.array_equal(fluence[:, 0], peak[:, 0]):
        raise ValueError("Energy grids differ")
    f, p = fluence[:, 1:], peak[:, 1:]
    if np.any((f > 0) & (p <= 0)):
        raise ValueError("Positive fluence at a zero peak: no finite bound")
    ratio = np.divide(f, p, out=np.zeros_like(f), where=p > 0)
    i, z = np.unravel_index(np.argmax(ratio), ratio.shape)
    return {"max_seconds": float(ratio[i, z]), "max_days": float(ratio[i, z]/86400),
            "energy_MeV_nucleon": float(fluence[i, 0]), "Z": int(z+1),
            "positive_components": int(np.count_nonzero(p)),
            "zero_zero_components": int(np.count_nonzero((p == 0) & (f == 0))),
            "declared_seconds": CFG["scenario"]["effective_sep_days"] * 86400}


def terms(nu_g, nu_s, mission, effective):
    return mission*nu_g**2, effective*nu_s**2, 2*effective*nu_g*nu_s


def period(exposure, nu_g, nu_s, n=38):
    s = CFG["scenario"]
    beta = (n-1)/(2*n*s["words"])
    budget = s["epsilon_conditional"] + math.expm1(-exposure)
    denominator = beta*sum(terms(nu_g, nu_s, s["mission_seconds"],
                                 s["effective_sep_days"]*86400))
    return max(0., budget/denominator)


def service_bounds(reads, write_fraction, read=45e-9, write=45e-9):
    if reads <= 0 or not 0 <= write_fraction <= 1:
        raise ValueError("Invalid service inputs")
    return reads*(read + write_fraction*write)


def peak_envelope(h, c, spacing):
    """Safe count bound for nonpreemptive service starts separated by spacing."""
    if h <= 0 or c <= 0 or spacing < c:
        raise ValueError("Invalid resource envelope")
    return min(1., c*(math.floor(h/spacing)+2)/h)


def verify_inputs(raw_archive):
    # Frozen reproduction, not an unvalidated general-purpose scenario solver.
    expected={"words":524288,"internal_data_bits":32,"internal_check_bits":6,
              "mission_seconds":315576000,"epsilon_conditional":.001,
              "effective_sep_days":1.34,"fluence_relative_error_theta":.3,
              "sep_let_cut_v18":31.7,"sep_let_cut_v21":32.6}
    if any(CFG["scenario"][k]!=v for k,v in expected.items()):
        raise ValueError("T68 is a frozen v21 reproduction; changed scenario needs an explicit port")
    if (CFG["numerics"]!={"let_grid_points":20001,"proton_grid_points":40001}
        or CFG["service"]["read_seconds"]!=45e-9
        or CFG["service"]["write_seconds"]!=45e-9):
        raise ValueError("The original grid and nominal cycles must remain explicit and frozen")
    checks = {}
    for name, expected in CFG["source_sha256"].items():
        checks[name] = sha((HERE/name).read_bytes()) == expected
    sources = json.loads((HERE/"source_inputs.json").read_text(encoding="utf-8"))
    for record in sources.values():
        for name, expected in record["members"].items():
            checks[name] = sha((HERE/name).read_bytes()) == expected["sha256"]
    manifest = json.loads((REPO / "experiments/RE-CY62167-ADDRESS-MAPPING-01/input_manifest.json").read_text(encoding="utf-8"))
    members = manifest["raw_files"] if "raw_files" in manifest else next(
        v for v in manifest.values() if isinstance(v, list) and v and "md5" in v[0])
    if raw_archive:
        data = Path(raw_archive).read_bytes()
        checks["raw_archive"] = sha(data) == CFG["raw_archive_sha256"]
        with zipfile.ZipFile(Path(raw_archive)) as archive:
            raw = {Path(n).name: archive.read(n) for n in archive.namelist() if n.endswith(".txt")}
    else:
        folder = HERE/".cache/raw"
        folder.mkdir(parents=True, exist_ok=True)
        raw = {}
        for record in members:
            name = record["source_file"]
            target = folder/name
            if not target.exists():
                url = f"https://zenodo.org/records/8314389/files/{name}?download=1"
                with urllib.request.urlopen(url, timeout=60) as response:
                    target.write_bytes(response.read())
            raw[name] = target.read_bytes()
    for record in members:
        name = record["source_file"]
        checks[name] = sha(raw[name]) == record["sha256"]
    if not all(checks.values()):
        raise ValueError("Input checksum failure: " + str([k for k, v in checks.items() if not v]))
    return checks, raw


def legacy_pipeline(raw):
    work = HERE/".cache/legacy"
    work.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(HERE/"inputs/calc_v18.zip") as archive:
        for name in archive.namelist():
            target = (work/name).resolve()
            if not target.is_relative_to(work.resolve()):
                raise ValueError("Unsafe archive member")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    rawdir = work/"data/New Folder"
    rawdir.mkdir(parents=True, exist_ok=True)
    for name, data in raw.items():
        (rawdir/name).write_bytes(data)
    for label, dest in [("main", "res/results"), ("thin", "res2/results")]:
        target = work/dest
        target.mkdir(parents=True, exist_ok=True)
        for path in (HERE/"inputs"/f"cosrad_{label}").glob("*.txt"):
            shutil.copyfile(path, target/path.name)
    # Original code needs no gw/sw unit SEE tables in these execution paths.
    scripts = ["parse.py", "validate_map.py", "first_type.py", "norm.py", "cosrad.py", "merged.py", "v18calc.py"]
    logs = {}
    for script in scripts:
        print(f"Reproduce {script}", flush=True)
        # Flush the originals' inline open(...,'wb') pickle handles explicitly.
        # This changes file delivery only, not numerical or classification code.
        launcher = ("import os,pickle,runpy,sys\n"
                    "original_dump=pickle.dump\n"
                    "def dump(obj,f,*a,**k):\n"
                    " original_dump(obj,f,*a,**k);f.flush();os.fsync(f.fileno())\n"
                    "pickle.dump=dump\n"
                    "runpy.run_path(sys.argv[1],run_name='__main__')\n")
        p = subprocess.run([sys.executable, "-c", launcher, script], cwd=work,
                           capture_output=True, encoding="utf-8", env=CHILD_ENV)
        (work/(script+".log")).write_text(p.stdout+p.stderr, encoding="utf-8")
        if p.returncode:
            raise RuntimeError(f"{script}: {p.stderr}")
        logs[script] = p.stdout
    # This is a documented single numerical change, not the author's v21 code.
    original = (work/"v18calc.py").read_text(encoding="utf-8")
    if original.count("Lfs<=31.7") != 1:
        raise ValueError("Unexpected original v18 cutoff")
    patched = original.replace("Lfs<=31.7", "Lfs<=32.6").replace("open('v18.json','w')", "open('v21_reconstructed.json','w')")
    (work/"v21_reconstructed.py").write_text(patched)
    p = subprocess.run([sys.executable, "v21_reconstructed.py"], cwd=work,
                       capture_output=True, encoding="utf-8", env=CHILD_ENV, check=True)
    (work/"v21_reconstructed.py.log").write_text(p.stdout+p.stderr)
    return work, logs


def cluster_audit(work):
    with (work/"runs.pkl").open("rb") as f:
        runs = pickle.load(f)
    with (work/"merged.pkl").open("rb") as f:
        merged_summary = pickle.load(f)
    with (work/"tab.pkl").open("rb") as f:
        tab = pickle.load(f)
    ns = function_namespace(work/"merged.py")
    records, group_totals = [], Counter()
    geometry=[]
    x16_rows = []
    residual = {}
    for name, let in HI.items():
        evs = runs[name]
        for d in range(23):
            geometry.append({"run":name,"LET":let,"d":d,
                "fraction_dy_ge_d":float(np.mean([np.ptp(e["ys"])>=d for e in evs])),
                "fraction_dx_ge_d":float(np.mean([np.ptp(e["xs"])>=d for e in evs]))})
        merged = ns["merge_events"](evs)
        # Raw address projection only; no claim about post-internal-ECC DQ.
        for selector in [0,20]:
            mask=1<<selector
            count=lambda seq:sum(len(np.unique(e["a"] & ~mask))<len(e["a"]) for e in seq)
            x16_rows.append({"run":name,"assumed_raw_byte_selector_bit":selector,
                "raw_same_x16_registered_objects":count(evs),
                "raw_same_x16_merged_objects":count(merged),
                "external39_uncorrectable_events":"unknown"})
        smu = [e for e in merged if ns["smu_count"]([e], (0, 1))]
        residual[let] = sum(len(e["a"]) for e in merged if not ns["smu_count"]([e], (0, 1))) / sum(e["m"] for e in evs)
        rec = {"run": name, "LET": let, "registered_clusters": len(evs),
               "registered_cell_occurrences": sum(e["m"] for e in evs),
               "merged_objects": len(merged), "multipart_objects": sum(e["parts"] > 1 for e in merged),
               "SMU_objects_A0_A1": len(smu), "SMU_cell_occurrences": sum(len(e["a"]) for e in smu),
               "max_dy_registered": max(int(e["ys"].max()-e["ys"].min()) for e in evs),
               "max_dx_registered": max(int(e["xs"].max()-e["xs"].min()) for e in evs),
               "mean_y_span_registered":float(np.mean([np.ptp(e["ys"])+1 for e in evs])),
               "mean_x_span_registered":float(np.mean([np.ptp(e["xs"])+1 for e in evs])),
               "fluence_inferred_cm2": tab[name]["Fn"],
               "fluence_coverage_to_weibull_ratio": tab[name]["Fc"]/tab[name]["Fn"],
               "physical_parent_count": "unknown"}
        records.append(rec)
        group_totals.update(merged_summary[name]["cnt"])
    write_csv("clusters.csv", records)
    # Table 1: registered N/S/extents, inferred F, and merged N1 are distinct.
    targets=[(1406,1478,"1149",5,3,0),(5088,5122,"1734",3,3,0),
      (16871,17148,"2057",7,6,0),(637,1628,"8.94",7,2,0),
      (1050,4368,"14.6",12,3,0),(924,5484,"8.73",10,3,0),
      (950,6707,"9.28",15,6,0),(1026,9822,"10.3",14,7,0),
      (998,10876,"9.19",16,5,0),(1050,12340,"9.69",15,10,0),
      (476,6230,"4.30",9,4,0),(1119,17012,"9.35",18,8,2),
      (1041,16735,"8.82",14,9,0),(1060,21185,"8.97",20,13,4)]
    comparison=[]
    for r, printed in zip(records,targets):
        for key,target in zip(["registered_clusters","registered_cell_occurrences",
          "fluence_inferred_cm2","max_dy_registered","max_dx_registered","SMU_objects_A0_A1"],printed):
            actual=r[key]/1000 if key=="fluence_inferred_cm2" else r[key]
            tol=.5*10**Decimal(target).as_tuple().exponent if isinstance(target,str) else 0
            quantity="fluence_inferred_1000_cm2" if key=="fluence_inferred_cm2" else key
            comparison.append({"run":r["run"],"quantity":quantity,"v21_printed":target,
                "reproduced":actual,"difference":actual-float(target),
                "within_printed_rounding":abs(actual-float(target))<=tol,
                "reason":"inferred F in 1000/cm2; printed rounding" if isinstance(target,str) else "exact count/extent"})
    write_csv("v21_table1_comparison.csv",comparison)
    write_csv("figure2_geometry.csv",geometry)
    example=next(e for e in runs["XeLET42"] if e["m"]==43)
    write_csv("figure2_example.csv",[{"x":int(x),"y":int(y),"A":int(a),"W32_seq":int(a>>2)}
        for x,y,a in zip(example["xs"],example["ys"],example["a"])])
    write_csv("raw_x16_hypotheses.csv",x16_rows)
    write_csv("groupings.csv", [{"address_bits": f"{a},{b}", "SMU_merged_HI": group_totals[(a, b)]} for a, b in PAIRS])
    gap_cfg = CFG["gap_diagnostic"]
    near = function_namespace(work/"pileup.py")
    gap = function_namespace(work/"gapstats.py", rng=np.random.default_rng(gap_cfg["seed"]))
    rows = []
    for name in gap_cfg["runs"]:
        evs = runs[name]
        observed = near["near_pairs"](evs)
        expected = gap["area_by_gap"](evs, gap_cfg["pairs_per_run"])*len(evs)*(len(evs)-1)/(2*2**24)
        for d in range(4, 8):
            rows.append({"run": name, "gap_L1": d, "observed_pairs": observed.get(d, 0),
                         "random_expected_pairs": float(expected[d])})
    write_csv("gaps.csv", rows)
    observed45 = sum(r["observed_pairs"] for r in rows if r["gap_L1"] <= 5)
    expected45 = sum(r["random_expected_pairs"] for r in rows if r["gap_L1"] <= 5)
    observed67 = sum(r["observed_pairs"] for r in rows if r["gap_L1"] >= 6)
    expected67 = sum(r["random_expected_pairs"] for r in rows if r["gap_L1"] >= 6)
    return {"ordinary_clusters": sum(len(x) for x in runs.values()),
            "cell_occurrences": sum(e["m"] for x in runs.values() for e in x),
            "HI_registered_clusters": sum(r["registered_clusters"] for r in records),
            "HI_merged_objects": sum(r["merged_objects"] for r in records),
            "HI_grouping_distribution": dict(Counter(group_totals.values())),
            "gap45_observed": observed45, "gap45_expected": expected45,
            "gap45_ratio": observed45/expected45,
            "gap67_ratio": observed67/expected67}, residual


def quadrature_integral(table, col, sigma, cutoff=None):
    """Independent node-split quadrature for original log/log + zero-node rule."""
    x, y = table[:, 0]/1000, table[:, col]*1000
    points = sorted(set([*x, .15, 5.2, 15, 17, 22, 27, 29, 31.7, 32.6, 33, 42, 43, 44, 57, 200]))
    if cutoff is not None:
        points = sorted(set(points+[cutoff]))
    total = 0.
    def phi(v):
        i = min(max(int(np.searchsorted(x, v, side="right"))-1, 0), len(x)-2)
        t = math.log(v/x[i])/math.log(x[i+1]/x[i])
        return math.exp(math.log(y[i])+t*math.log(y[i+1]/y[i])) if min(y[i:i+2]) > 0 else y[i]*(1-t)+y[i+1]*t
    for a, b in zip(points, points[1:]):
        if a < x[0] or b > min(x[-1], 200) or (cutoff is not None and a >= cutoff):
            continue
        total += quad(lambda v: phi(v)*float(sigma(v)), a, b, epsabs=1e-18, epsrel=2e-9)[0]
    return total


def numeric_audit(work, residual):
    old = json.loads((work/"v18.json").read_text(encoding="utf-8"))
    new = json.loads((work/"v21_reconstructed.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(HERE/"inputs/calc_v18.zip") as z:
        frozen = json.loads(z.read("v18.json"))
    relative = [abs(a[k]-b[k])/max(abs(b[k]), 1e-300) for a, b in zip(old["rows"], frozen["rows"]) for k in a if isinstance(a[k], (int, float))]
    spec = function_namespace(work/"spectra_lib.py")
    orbital = function_namespace(work/"orbital.py", Nbits=2**24, ssat=2.6e-7, L0w=.15, W=70., h=1.2,
                                 LETpts=np.array([5.2,15,17,22,27,29,33,42,57]),
                                 frac=np.array([1,1,1,1,1,1,1,16969/17012,21058/21185]))
    sep = function_namespace(work/"sep.py", **{k:v for k,v in orbital.items() if not k.startswith("__")})
    v17 = json.loads((work/"v17.json").read_text(encoding="utf-8"))
    spt = lambda l: np.where(np.asarray(l)<=33, 0., np.interp(l, [33,43,57], [0.,v17["s43"],v17["s57"]]))
    levels = sorted(map(int, new["F"]))
    def envelope(l, bounds):
        index = np.minimum(np.searchsorted(levels, l, side="left"), len(levels)-1)
        return np.where(np.asarray(l)<27, 0., np.array([bounds[str(x)] for x in levels])[index])
    audit = []
    for a, b in zip(old["rows"], new["rows"]):
        rho = b["rho"]
        shields = ([.1,.2,.27,.3,.5,.7,1.,1.25] if rho<1.5 else [1.5,1.75,2.,2.25,2.5,2.75,3.,3.5,4.])
        label = "thin" if rho<1.5 else "main"
        tables = {n:read_table(HERE/"inputs"/f"cosrad_{label}"/(n+"_x.txt"), len(shields)+1) for n in ["gl","sl","gp","sp"]}
        col = shields.index(rho)+1
        g, solar, mixed = terms(b["nuG"], b["nuS"], CFG["scenario"]["mission_seconds"], 1.34*86400)
        rec = {**{k:v for k,v in b.items() if k not in ["ok","okp"]},
               "gcr_I2_upper_s_inv":g,"sep_I2_upper_s_inv":solar,"mixed_I2_upper_s_inv":mixed,
               "SEP_to_GCR_I2":(solar+mixed)/g,
               "sep_exposure_upper":1.34*86400*b["nuS"],
               "cutoff_delta_nuS_percent":100*(b["nuS"]/a["nuS"]-1),
               "cutoff_delta_UA0_percent":100*(b["UA0"]/a["UA0"]-1),
               "cutoff_delta_tU_percent":100*(b["tU"]/a["tU"]-1),
               "theta0_UA0":b["UA0"]*.7, "theta0_UR":b["UR"]*.7,
               "full38_upper_certificate":False}
        rec["quad_L1"]=315576000*quadrature_integral(tables["gl"],col,spt)
        for field, key in [("UA0","bA0"),("UR","bRow")]:
            sig=lambda l,key=key:envelope(l,new[key])
            rec["quad_"+field]=315576000*quadrature_integral(tables["gl"],col,sig)+1.34*86400*quadrature_integral(tables["sl"],col,sig,32.6)
        # Pure sensitivity: disjoint residual after merging, and all-bit upper.
        rf=lambda l: np.interp(l, sorted(residual), [residual[x] for x in sorted(residual)])
        merged_sigma=lambda l:2**24*orbital["sb"](l)*rf(l)
        all_sigma=lambda l:2**24*orbital["sb"](l)
        for kind, sig in [("merged", merged_sigma),("all",all_sigma)]:
            rates=[]
            for tn,pn,cut in [("gl","gp",None),("sl","sp",32.6)]:
                xx,pp=spec["make_phi"](col,tables[tn]); pp=np.where(xx<=cut,pp,0.) if cut else pp
                rates.append((spec["rate_naive"](xx,pp,sig)+sep["rate_pl"](col,tables[pn],orbital["sig_p_710"])*2**24)*38/32)
            rec["tU_"+kind+"_residual"]=period(b["L1"],*rates)
        # Sensitivity of the article's angular diagnostic, not physical evidence.
        gx,gp=spec["make_phi"](col,tables["gl"]); sx,sp=spec["make_phi"](col,tables["sl"])
        sp=np.where(sx<=32.6,sp,0.)
        if rho==2.5:
            def cumulative_tail(x,y):
                # Reverse accumulation avoids subtracting nearly equal totals.
                cells=.5*(y[1:]+y[:-1])*np.diff(x)
                return np.r_[np.cumsum(cells[::-1])[::-1],0.]
            gtail=cumulative_tail(gx,gp)*315576000
            stail=cumulative_tail(sx,sp)*1.34*86400
            sample=np.unique(np.r_[np.arange(0,len(gx),100),
                np.searchsorted(gx,[27,29,31.7,32.6,33,42,43,44,57]),len(gx)-1])
            write_csv("figure4_samples.csv",[{"LET":float(gx[i]),"GCR_fluence_above_L":float(gtail[i]),
                "SEP_fluence_envelope_above_L":float(stail[i]),"SMU_point_cm2":float(spt(gx[i])),
                "SMU_upper_rows_cm2":float(envelope(gx[i],new["bA0"])),
                "SMU_upper_one_row_cm2":float(envelope(gx[i],new["bRow"]))} for i in sample])
        angular=315576000*spec["rate_thin"](gx,gp,spt,60,200)+1.34*86400*spec["rate_thin"](sx,sp,spt,60,200)
        rec["thin_layer_diagnostic_multiplier"]=angular/b["L1"]
        # Original bisector caps its bracket at 1e8, including where it fails.
        weights=[]
        for j,lev in enumerate(levels):
            lo=27 if j==0 else levels[j-1]
            hi=lev if j<len(levels)-1 else float("inf")
            # At 57 and above the last measured upper is held constant.
            if j==len(levels)-1:lo=levels[j-1]
            ind=lambda x,lo=lo,hi=hi:((np.asarray(x)>lo)&(np.asarray(x)<=hi)).astype(float)
            if j==0:ind=lambda x:np.asarray(x)==27
            weights.append(315576000*spec["rate_naive"](gx,gp,ind)+1.34*86400*spec["rate_naive"](sx,sp,ind))
        fluences=np.array([sum(new["F"][str(v)] for v in levels if v>=lev) for lev in levels])
        def row_upper(extra):return float(np.sum(np.array(weights)*3/(.7*(fluences+extra))))
        lo,hi=0.,1e8
        while row_upper(hi)>5e-4:hi*=2
        for _ in range(70):
            mid=(lo+hi)/2
            if row_upper(mid)>5e-4:lo=mid
            else:hi=mid
        rec["Fadd_bracketed"]=hi
        rec["Fadd_original_hits_cap"]=b["Fadd"]>=1e8
        audit.append(rec)
    write_csv("numerics.csv",audit)
    write_json(OUT/"v18_reproduced.json",old)
    write_json(OUT/"v21_reconstructed.json",new)
    for name in ["sfn","sfxm"]:
        if not np.array_equal(read_table(HERE/f"inputs/cosrad_main/{name}.txt",29),
                              read_table(HERE/f"inputs/cosrad_thin/{name}.txt",29)):
            raise ValueError("Orbital inputs differ between shielding exports")
    teff=effective_duration(read_table(HERE/"inputs/cosrad_main/sfn.txt",29),read_table(HERE/"inputs/cosrad_main/sfxm.txt",29))
    # Roundoff in printed spectra does not supply a continuum/tail guarantee.
    teff["nodes_within_declared_bound"]=teff["max_seconds"]<=teff["declared_seconds"]
    return {"v18_frozen_max_relative_difference":max(relative),"effective_duration":teff,
            "accumulation_38_to_32_factor":38*37/(32*31),
            "theta_upper_factor":1/.7,
            "point_sigma43_archived":v17["s43"],
            "point_sigma43_from_unrounded_F":2/(new["F"]["42"]+new["F"]["44"]),
            "point_sigma57_archived":v17["s57"],
            "point_sigma57_from_unrounded_F":4/new["F"]["57"],
            "quad_upper_max_relative_difference":max(abs(r["quad_"+k]/r[k]-1) for r in audit for k in ["UA0","UR"])},audit


def resource_audit(numerics):
    modes=[("internal_x8_known",2**19),("internal_x8_unknown",2**21),
           ("internal_x16_known",2**19),("internal_x16_unknown",2**20),
           ("external39_parallel3_nominal",2**19)]
    rows=[]
    allowances=[]
    for mode,reads in modes:
        for f in [0.,1.]:
            busy=service_bounds(reads,f)
            for rho in [2.5,3.]:
                a=next(r for r in numerics if r["rho"]==rho)["tU"]
                rows.append({"mode":mode,"shield_g_cm2":rho,"write_fraction":f,
                    "reads":reads,"nominal_busy_s":busy,"point_period_s":a,
                    "occupancy_percent_at_point_period":100*busy/a,
                    "interpretation":"read-only lower bound" if f==0 else "serial U total; ERR worst case",
                    "external_risk_period_applicable":False if mode.startswith("external") else "conditional v21 surrogate only"})
                if mode.startswith("internal") and f==1.:
                    r=next(x for x in numerics if x["rho"]==rho)
                    pair=(37/(2*38*2**19))*busy*sum(terms(r["nuG"],r["nuS"],315576000,1.34*86400))
                    allowance=-math.log1p(-(0.001-pair)) if pair<.001 else 0.
                    allowances.append({"mode":mode,"shield_g_cm2":rho,"period_s":busy,
                        "pair_bound_at_read_write_floor":pair,"full38_direct_exposure_max":allowance,
                        "extra_above_data_point_max":max(0.,allowance-r["L1"]),
                        "scope":"optimistic formula-only, no startup/service/channel reserves"})
    write_csv("service.csv",rows)
    write_csv("direct_allowance.csv",allowances)
    thresholds={}
    for mode,reads in modes[:4]:
        for f in [0.,1.]:
            eligible=[r["rho"] for r in numerics if r["tU"]>=service_bounds(reads,f)]
            thresholds[f"{mode}_writes_{f:g}"]=min(eligible) if eligible else None
    return {"thresholds_point_only":thresholds,
            "existing_executor_busy_upper_s":2**19*CFG["service"]["existing_slot_upper_seconds"],
            "existing_executor_nominal_reserved_s":2**19*24e-8,
            "peak_delay_qualified":False}


def comparison_report(rows,summary):
    # v21 Table 2 as printed, not inferred from prior outputs.
    targets={.1:["11.2e-4","113","1.9e-4","5","8.0","1.8"],
      .5:["3.33e-4","7.6","8.2e-5","12",".23",".052"],
      1.:["2.38e-4","2.0","5.9e-5","17",".061",".014"],
      1.5:["2.02e-4",".93","4.8e-5","21",".031",".0071"],
      2.:["1.81e-4",".53","4.1e-5","25",".021",".0046"],
      3.:["1.55e-4",".24","3.1e-5","32",".012",".0028"],
      4.:["1.37e-4",".14","2.5e-5","41",".0090",".0020"]}
    compare=[]
    for r in rows:
        if r["rho"] not in targets:continue
        for key,printed in zip(["nuG","nuS","L1","kstar","UA0","UR"],targets[r["rho"]]):
            target=float(printed)
            rounding=.5*10**Decimal(printed).as_tuple().exponent
            compare.append({"shield_g_cm2":r["rho"],"quantity":key,"v21_printed":printed,
                            "reproduced":r[key],"relative_difference_percent":100*(r[key]/target-1),
                            "within_printed_rounding":abs(r[key]-target)<=rounding+1e-15,
                            "status":"v18 with v21 cutoff; remaining difference: printed rounding"})
    write_csv("v21_comparison.csv",compare)
    lines=["# Воспроизведение v21", "", "Числа ниже — условная свёртка экспортов COSRAD; новый запуск COSRAD не выполнялся.",
           "Результат не является сертификатом полного 38-разрядного слова или всей Θ.", "",
           "| Защита, г/см² | νГ, с⁻¹ | νС, с⁻¹ | Λ₁ point | Λ₁ upper | τ ГКЛ, с | τ ГКЛ+СКЛ, с | смешанный / весь I₂ |",
           "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        mixed=r["mixed_I2_upper_s_inv"]/(r["gcr_I2_upper_s_inv"]+r["sep_I2_upper_s_inv"]+r["mixed_I2_upper_s_inv"])
        lines.append(f'| {r["rho"]:g} | {r["nuG"]:.8g} | {r["nuS"]:.8g} | {r["L1"]:.8g} | {r["UA0"]:.8g} | {r["tG"]:.8g} | {r["tU"]:.8g} | {mixed:.6g} |')
    lines += ["", "## v21 — воспроизведено — расхождение — причина", "",
      "Таблица 1 (84 значения): `v21_table1_comparison.csv`; таблица 2 (42 значения): `v21_comparison.csv`.", "",
      "| Проверка | v21 | Воспроизведено | Причина / статус |", "|---|---|---|---|"]
    n=summary["numeric"];c=summary["clusters"]
    lines += [f'| Кластеры / ячейки | 173802 / 299026 | {c["ordinary_clusters"]} / {c["cell_occurrences"]} | Совпало |',
      '| SMU после объединения, LET 42 / 57 | 2 / 4 | 2 / 4 | Совпало для 10 группировок с A₀; физические родители не идентифицированы |',
      f'| Избыток пар, промежуток 4–5 | ≈8 | {c["gap45_ratio"]:.5g} | Шесть серий, случайные размещения из gapstats.py, seed 7 |',
      f'| Tэфф | ≤1,34 сут | {n["effective_duration"]["max_days"]:.10g} сут | Максимум напечатанных компонент; единый положительный перенос и хвосты условны |',
      f'| v18.json | Точный код v21 не указан | max относительное отклонение {n["v18_frozen_max_relative_difference"]:.3g} | v18 воспроизведён отдельно; cutoff 31,7 → 32,6 изменяет upper |',
      '| Валидация A | 143609 | 143609 исходных, 143590 после 19 повторов | Разный учёт, те же нулевые остатки |',
      '| Нижняя граница по двум XOR-инверсиям | 1−exp(−Λ₁) | Не перенесена | SEMANTICS-REPAIR: возможна отмена прежней ошибки; остаётся upper-суррогат |',
      '| ГКЛ 20,4586 / 45,6849 с | Исторические | Сохранены в PAPER-COMPLETION | 32 data bits, прежняя SMU-нормировка, GCR-only; не текущие τ |',
      "", "`numerics.csv` дополнительно содержит GCR/SEP/смешанное I₂, влияние θ, независимую квадратуру, остаток после объединения и угловую чувствительность.",
      "Прогноз флюенса и угловая чувствительность — воспроизведение формул, не поручение на новые облучения."]
    (OUT/"reproduction.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-archive",type=Path,help="Existing Zenodo New Folder.zip (otherwise fetch 28 checksum-pinned files)")
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    checks,raw=verify_inputs(args.raw_archive)
    work,logs=legacy_pipeline(raw)
    print("Audit merged clusters and gap diagnostic",flush=True)
    clusters,residual=cluster_audit(work)
    print("Audit spectra, quadrature and resource",flush=True)
    numeric,rows=numeric_audit(work,residual)
    summary={"input_checks":checks,"clusters":clusters,"numeric":numeric,"service":resource_audit(rows),
             "qualification":{"conditional_model_only":True,"full38_ready":False,"full39_ready":False,
                "accepted_theory_changed":False,"original_manuscript_changed":False}}
    write_json(OUT/"summary.json",summary)
    comparison_report(rows,summary)
    # Necessary scientific gates, not merely tests mirroring implementation.
    assert clusters["ordinary_clusters"]==173802 and clusters["cell_occurrences"]==299026
    assert numeric["v18_frozen_max_relative_difference"]<1e-10
    assert numeric["effective_duration"]["nodes_within_declared_bound"]
    test=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(HERE),"-p","test_*.py","-v"],
                        capture_output=True,encoding="utf-8",env=CHILD_ENV)
    (OUT/"tests.txt").write_text(test.stdout+test.stderr,encoding="utf-8")
    if test.returncode:raise RuntimeError(test.stderr)
    print(test.stderr.strip())
    print(f"Complete: {OUT/'reproduction.md'}")


if __name__=="__main__":
    main()
