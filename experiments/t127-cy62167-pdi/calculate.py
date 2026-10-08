"""Bounded T127 input qualification, not a replacement memory certificate.

Reuse pinned T123 transport/GOST and T114 service; do not mutate either.
All physical gaps remain null. Numeric precision checks are not uncertainty
bounds for the response, transport, population, or device.
"""
import argparse
import ast
import csv
from datetime import datetime
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
import zipfile

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
LEGACY = ROOT / "experiments/t68-v21-inputs"
SEPEM = ROOT / "experiments/tNN-sepem-profiles"
sys.path[:0] = [str(SEPEM), str(ROOT / "experiments/t114-two-stage-err")]
import transport
import gost


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


service = load_module("t127_t114_service", ROOT / "experiments/t114-two-stage-err/calculate.py")
BITS = CFG["words"] * CFG["protected_bits_per_word"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def table(name):
    rows = []
    for line in (LEGACY / "inputs/cosrad_main" / name).read_text().splitlines():
        try:
            row = list(map(float, line.split()))
        except ValueError:
            continue
        if len(row) == 10:
            rows.append(row)
    return np.array(rows)


def old_functions():
    """Only inspected pure functions; no execution of legacy top-level code."""
    ns = dict(np=np, math=math, Nbits=2**24, ssat=2.6e-7, L0w=.15, W=70., h=1.2,
              LETpts=np.array([5.2,15,17,22,27,29,33,42,57]),
              frac=np.array([1,1,1,1,1,1,1,16969/17012,21058/21185]))
    names = {"spectra_lib.py": {"make_phi", "trapz", "rate_naive"},
             "orbital.py": {"sb", "fr", "sig_nak", "sig_p_710"}, "sep.py": {"rate_pl"}}
    with zipfile.ZipFile(LEGACY / "inputs/calc_v18.zip") as z:
        for file, selected in names.items():
            tree = ast.parse(z.read(file).decode())
            funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in selected]
            if {n.name for n in funcs} != selected:
                raise ValueError("Legacy API changed")
            exec(compile(ast.Module(body=funcs, type_ignores=[]), file, "exec"), ns)
    return ns


def sum_components(ion, proton_full, extra_hep=None):
    if extra_hep is not None:
        raise ValueError("PDI/full response already contains HEP; additive HEP forbidden")
    return ion + proton_full


def conditional_square(background, solar_peak):
    # Same-positive-transfer assumption and Teff cover printed T68 nodes only.
    exposure = 115776. * solar_peak
    bg = CFG["mission_s"] * background**2
    sep = solar_peak * exposure
    mixed = 2 * background * exposure
    return exposure, bg, sep, mixed, bg + sep + mixed


def fixed_arithmetic(b, s, square, exposure, p_upper, p_lower, dstar=None):
    """T114 general marks coefficient, no guarantee unless all inputs qualified."""
    beta0 = F(1, 2 * CFG["words"])
    p = dict(W=CFG["words"], T=F(CFG["mission_s"]), b=F(str(b)), B=F(str(b+s)),
             FS=F(str(exposure)), F=F(str(b))*CFG["mission_s"] + F(str(exposure)), beta=beta0)
    cross = service.old.cross(p, p_lower, p_upper, 1, F(str(square)), service.T["d"])
    initial = p["B"] * (p_upper + service.T["d"]) / p["W"]  # K0=1, not a free clean start
    fixed_quotas = F("3e-6")  # rho0 + delta_exec + delta_svc; no monitor quota for Fixed
    rest = fixed_quotas + initial + beta0*p_upper*F(str(square)) + cross["X"]
    upper = None if dstar is None else float(rest + F(str(dstar)))
    return dict(Q_without_D_arithmetic=float(rest), Q_conditional_upper=upper,
                D_max_for_sufficient_inequality=float(F(".001")-rest),
                initial_term=float(initial), aperture_cross=float(cross["X"]),
                fixed_quota_total=float(fixed_quotas), beta0=float(beta0),
                interpretation="conditional arithmetic; absent D is unknown, not zero")


def service_case():
    p = service.old.environment(service.old.HANDOFF["rows"][0])
    profile = dict(service.CFG["profiles"][1])  # singleton_write timings; no use of its channel assumption
    attempts = []
    for g in range(164, 201, 4):
        profile["g_ticks"] = g
        cal = service.calendar(p, profile, 1, service.CFG["growth_classes"][0])
        r = service.resource(cal)
        ok = all(r[k] >= 0 for k in ("placement_slack", "app_margin_slack", "gate_slack", "rate_max_sigma1")) and r["burst_max_latency"] >= 1
        attempts.append(dict(g_ticks=g, passes_declared_calendar_resource_test=ok,
                             placement_slack_s=float(r["placement_slack"]),
                             base_peak=float(r["peak_control_no_application"])))
        if ok:
            break
    if not ok:
        raise ValueError("No calendar passed bounded grid")
    rate = r["rate_max_sigma1"]
    peak = r["peak_control_no_application"] + cal["app"]*(1+rate*F(".001003"))/F(".001")
    q = fixed_arithmetic(float(p["b"]), float(p["B"]-p["b"]), 6940., float(p["FS"]),
                         cal["Ps"], cal["Ps_min"], float(p["D"]))
    return cal, dict(
        scope="fastest in existing batch=8,c=164,4-tick g-grid,observed-write family only",
        g_ticks=cal["g"], P_min_s=float(cal["Ps"]), P_lower_s=float(cal["Ps_min"]),
        application_burst=1., application_plus_X_rate_max_s=float(rate),
        application_at_rate_limit_peak=float(peak), base_control_plus_X_peak=float(r["peak_control_no_application"]),
        joint_delay_upper_s=float(r["one_request_delay"]), deadline_s=3e-6,
        margin=1.1, peak_window_s=.001, peak_limit=.8,
        write_time_s=float(cal["app"]), read32_time_s=float(service.T["app"]),
        write_preobservation_extra_s=float(service.T["R"]),
        FIFO_including_inflight_and_held_reply=2,
        actual_application=None, measured_WCET=None, full38_ERR_and_E_qualified=None,
        candidates=attempts, old_6940_accepted_D_arithmetic=q,
        fixed_initial_K0=1, fixed_quotas={"rho0":1e-6,"delta_exec":1e-6,"delta_svc":1e-6},
        adaptive_quotas_not_used_by_fixed={"delta_E":1e-6,"delta_M":1e-6,"alpha_M":1e-6},
        return_context=dict(a_parent_lower=.9, cluster_rate_ratio_upper=.1, growth_rho_s=.048,
                            availability_and_counter_parameters="T114 config.price_contract; conditional, not measured"))


def shield_rows(cal):
    ns = old_functions()
    out = []
    columns = {2.5:5, 3.:7, 3.5:8, 4.:9}
    for rho in CFG["shield_g_cm2"]:
        col = columns[rho]
        ions = {}
        for name in ("gl_x.txt", "sl_x.txt"):
            x, f = ns["make_phi"](col, table(name))
            # The historical cutoff applies to solar LET, not the GCR table.
            flux = np.where(x<=32.6, f, 0) if name=="sl_x.txt" else f
            ions[name] = float(ns["rate_naive"](x, flux, ns["sig_nak"])*38/32)
        for model in ("historical_HEP", "main_loglog_PDI_HEP"):
            sig = ns["sig_p_710"] if model=="historical_HEP" else transport.sigma
            # factor .5 is legacy geometry, NOT measured isotropic response.
            for angular in ([.5] if model=="historical_HEP" else [.5, 1.]):
                proton = {name:float(ns["rate_pl"](col, table(name), sig, factor=angular)*BITS)
                          for name in ("gp_x.txt", "sp_x.txt")}
                b = sum_components(ions["gl_x.txt"], proton["gp_x.txt"])
                s = sum_components(ions["sl_x.txt"], proton["sp_x.txt"])
                exposure, bg, solar, mixed, square = conditional_square(b, s)
                out.append(dict(example_group=CFG["example_group"], shield_g_cm2=rho,
                    response=model, proton_angular_factor=angular, ion_component="legacy_LET_not_species_resolved",
                    background_LET_s=ions["gl_x.txt"], background_proton_s=proton["gp_x.txt"],
                    solar_LET_peak_s=ions["sl_x.txt"], solar_proton_peak_s=proton["sp_x.txt"],
                    b_s=b, solar_peak_s=s, B_s=b+s, solar_N=exposure,
                    S2_background=bg, S2_solar=solar, S2_mixed=mixed, S2_total=square,
                    physical_Dstar=None, physical_Q_lower=None, physical_Q_upper=None,
                    **fixed_arithmetic(b, s, square, exposure, cal["Ps"], cal["Ps_min"]),
                    status="CONDITIONAL_INPUTS_NOT_PHYSICALLY_QUALIFIED", value_type="calculated"))
    return out


def gost_rows():
    rows=[]
    nbar = read_json(SEPEM/"config.json")["mission_mean_events"]
    for rho in CFG["shield_g_cm2"]:
        for model in ("pdi", "no_pdi"):
            vals=[]
            for order in (12,24):
                e, w, _, _ = transport.quadrature(transport.RangeTable(), rho, model, order)
                vals.append((float(BITS*np.dot(w, gost.spectrum(e,nbar,"fluence"))),
                             float(4*math.pi*BITS*np.dot(w,gost.spectrum(e,nbar,"peak_flux")))))
            n, peak=vals[1]
            relative=max(abs(a-b)/b for a,b in zip(vals[0],vals[1]))
            if relative>CFG["numerical_relative_check_tolerance"]:
                raise ValueError("Quadrature refinement failed")
            rows.append(dict(example_group=CFG["example_group"], shield_g_cm2=rho, response=model,
                nbar_conditional=nbar, N_solar_protons=n, peak_solar_protons_s=peak,
                marginal_product_S2=peak*n, refinement_relative_difference=relative,
                joint_S2_quantile=None, status="SEPARATE_MARGINALS_NOT_JOINT_BOUND", value_type="calculated"))
    return rows


def population(silso_path=None):
    with (SEPEM/"outputs/events.csv").open(encoding="utf-8") as f:
        events=list(csv.DictReader(f))
    summary=read_json(SEPEM/"outputs/analysis_summary.json")
    eligible=[r for r in events if float(r["fluence_gt30_omni_cm-2"])>1e5 and r["edge_truncated"].lower()=="false"]
    duration=(datetime(2016,1,1)-datetime(1974,7,1)).total_seconds()
    count=len(eligible)
    old_mean=summary["mission_model_B"]["mean_count"]
    result=dict(coverage_start="1974-07-01T00:00:00Z", coverage_end_exclusive="2016-01-01T00:00:00Z",
                duration_seconds=duration, Julian_years=duration/31557600,
                event_count=len(events), strict_GOST_fluence_filtered_count=count,
                old_bootstrap_eligible_count=summary["mission_model_B"]["eligible_events"],
                filtered_count_per_10_Julian_years=count*315576000/duration,
                old_conditional_nbar=old_mean,
                old_nbar_to_empirical_count_ratio=old_mean/(count*315576000/duration),
                filled_reference_rows=4365792, grid_missing=0, original_gap_fraction=None,
                GOST_event="solar proton event with omnidirectional fluence >30 MeV strictly >1e5 cm-2",
                extraction_rule=summary["event_definition"],
                population_identity=False, revised_nbar=None, revised_mission_B_quantile=None,
                reason="lambda threshold/merged episodes and fluence filter do not establish GOST population completeness",
                original_background_subtraction="H not subtracted; He subtracted",
                post2015="2016 gap; selected overlapping T67 windows cannot estimate a continuation event rate")
    annual=[]
    if silso_path:
        for line in Path(silso_path).read_text().splitlines():
            row=line.split(); y,m=int(row[0]),int(row[1])
            if (1974,7)<=(y,m)<(2016,1):
                if float(row[3])<0 or "*" in row:
                    raise ValueError("Missing/provisional SILSO month")
                annual.append(dict(year=y, month=m, smoothed_wolf_v2=float(row[3])))
        if len(annual)!=498:
            raise ValueError("SILSO coverage mismatch")
        result.update(silso_sha256=sha(silso_path), silso_months=len(annual),
                      GOST_actual_cycle_expected_events=.00925*math.fsum(r["smoothed_wolf_v2"] for r in annual),
                      actual_cycle_is_not_a_mission_forecast=True)
        result["actual_cycle_expected_per_10_Julian_years"]=result["GOST_actual_cycle_expected_events"]*315576000/duration
        result["count_over_actual_cycle_expected"]=count/result["GOST_actual_cycle_expected_events"]
    if not silso_path:
        with (HERE/'inputs/silso-yearly-derived.csv').open(encoding='utf-8') as f:
            saved=list(csv.DictReader(f))
        if sum(int(r['months']) for r in saved)!=498:
            raise ValueError('Saved SILSO month coverage mismatch')
        total=.00925*math.fsum(float(r['sum_monthly_smoothed_Wolf_v2']) for r in saved)
        result.update(silso_sha256='9d0b875cf70fdc7f6dfb1f61bf187845a17ea06e91e8aacdc4f8b0f5c4e76e40',
                      silso_months=498,GOST_actual_cycle_expected_events=total,actual_cycle_is_not_a_mission_forecast=True,
                      actual_cycle_expected_per_10_Julian_years=total*315576000/duration,
                      count_over_actual_cycle_expected=count/total)
    return result, annual


def zenodo_check(path):
    manifest=read_json(ROOT/"experiments/RE-CY62167-PROTON-01/source_manifest.json")
    rows=[]
    with zipfile.ZipFile(path) as z:
        for row in manifest["zenodo"]["raw_files"]:
            data=z.read(row["filename"])
            digest=hashlib.sha256(data).hexdigest()
            if digest!=row["sha256"]:
                raise ValueError("Zenodo raw mismatch: "+row["filename"])
            rows.append(dict(filename=row["filename"], sha256=digest, matched=True))
        total=len(z.infolist())
    return dict(archive_sha256=sha(path), members=total, proton_files=rows,
                matched_fluence_or_exact_publication_run=False, full38_observed=False)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--silso", type=Path)
    parser.add_argument("--zenodo", type=Path)
    parser.add_argument("--out", type=Path, default=HERE/"outputs")
    args=parser.parse_args(); start=time.perf_counter(); out=args.out
    cal, resource=service_case()
    rows=shield_rows(cal)
    write_csv(out/"shield-conditional.csv", rows)
    write_csv(out/"gost-proton-conditional.csv", gost_rows())
    write_json(out/"service.json", resource)
    # One group, four points; neither the empirical B model nor a marginal
    # product is promoted to a full physical coordinate or a class lower bound.
    transfer=[]
    for r in rows:
        if r['response']=='main_loglog_PDI_HEP' and r['proton_angular_factor']==.5:
            transfer.append(dict(example_group=CFG['example_group'],shield_g_cm2=r['shield_g_cm2'],
                source_row='shield-conditional.csv:main_loglog_PDI_HEP:angular=.5',
                W=CFG['words'],n=38,T_s=CFG['mission_s'],epsilon=.001,P_min_calendar_s=float(cal['Ps']),
                b_conditional_s=r['b_s'],B_conditional_s=r['B_s'],N_solar_conditional=r['solar_N'],
                S2_solar_conditional=r['S2_solar'],S2_mixed_conditional=r['S2_mixed'],S2_total_conditional=r['S2_total'],
                sigma_uniform38_conditional=(37/(76*524288))*float(cal['Ps'])*r['S2_solar']/.001,
                sigma_general_marks_conditional=float(cal['Ps'])*r['S2_solar']/(2*524288*.001),
                eta_conditional=r['S2_total']/r['S2_background'],delta=None,chi=None,
                full38_Dstar=None,joint_S2_quantile=None,physical_Q_upper=None,class_Q_lower=None,
                Q_without_D_arithmetic=r['Q_without_D_arithmetic'],
                margin_before_D_arithmetic=r['D_max_for_sufficient_inequality'],
                status='UNRESOLVED_PHYSICAL_INPUTS; conditional sufficient expression does not pass',
                missing_inputs=['isotropic/package/lot response bound','full38 parent marks and direct contribution',
                                'joint temporal/species envelope','actual load/WCET/E/ERR qualification','GOST event population identity']))
    write_json(out/'inputs-126.json',dict(task=127,recipient=126,examples=1,rows=transfer,
                                        allow_replacement_of_accepted_6940=False,necessity_exclusion_established=False))
    pop, monthly=population(args.silso)
    write_json(out/"population.json", pop)
    if monthly:
        # Compact derived yearly sums, not a redistribution of the full live series.
        yearly=[dict(year=y, months=sum(r["year"]==y for r in monthly),
                     sum_monthly_smoothed_Wolf_v2=math.fsum(r["smoothed_wolf_v2"] for r in monthly if r["year"]==y))
                for y in sorted({r["year"] for r in monthly})]
        write_csv(out/"silso-yearly-derived.csv",yearly)
    if args.zenodo:
        write_json(out/"zenodo-check.json",zenodo_check(args.zenodo))
    inputs=[SEPEM/name for name in ("config.json","transport.py","gost.py","inputs/nist_pstar_al.csv","inputs/gost_selected_coefficients.csv",
                                   "outputs/events.csv","outputs/analysis_summary.json","outputs/input_audit.json")]
    inputs += [LEGACY/"inputs/calc_v18.zip"]+[LEGACY/"inputs/cosrad_main"/n for n in ("gl_x.txt","gp_x.txt","sl_x.txt","sp_x.txt")]
    inputs += [ROOT/"experiments"/name for name in ("t104-new-rtl-executor/handoff.json","t110-err-write-service/calculate.py","t110-err-write-service/inputs.json",
               "t114-two-stage-err/calculate.py","t114-two-stage-err/config.json","t114-two-stage-err/intervals.py",
               "RE-CY62167-PROTON-01/source_manifest.json")]
    inputs += [HERE/'inputs/silso-yearly-derived.csv',ROOT/"experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv", ROOT/"experiments/RE-GOES19-PROTON-RATE-01/sigma_model.py"]
    write_json(out/"reproduction.json",dict(
        code_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        config_sha256=sha(HERE/"config.json"), code_sha256=sha(Path(__file__)),
        python=platform.python_version(), numpy=np.__version__, scipy=__import__('scipy').__version__, platform=platform.platform(),
        ru_maxrss_bytes=__import__('psutil').Process().memory_info().peak_wset if sys.platform=='win32' else None,
        wall_seconds=time.perf_counter()-start,
        inputs_sha256={str(p.relative_to(ROOT)).replace("\\","/"):sha(p) for p in sorted(set(inputs))},
        outputs_sha256={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!="reproduction.json"},
        scope="reproduction with shared production dependencies; see independent checker for additional evidence"))
    print(json.dumps(dict(resource=resource, population=pop, rows=len(rows)),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
