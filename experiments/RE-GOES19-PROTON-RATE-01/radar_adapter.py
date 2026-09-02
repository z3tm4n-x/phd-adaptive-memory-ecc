"""Thin adapter around pinned RADAR proton-Al transport for RE-GOES19-PROTON-RATE-01.

RADAR is checked out separately at the exact pinned SHA. This adapter does not
vendor RADAR code/data. It records small compatibility normalizations required
by the pinned compact TENDL/range tables and builds linear transport response
matrices exclusively by calling pinned RADAR public calculation functions.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

RADAR_SHA = "b032505d4d1b15403b8ad06aef578339f6d1c6b4"
SHIELDS_MM = (0.0, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0)
AL_DENSITY = 2.70
GRID_CANDIDATES = (96, 144, 192)
CONVERGENCE_LIMIT = 0.005


def _git_sha(root: Path) -> str:
    return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()


def _normalize_rows(src: Path, dst: Path, key_cols: tuple[str, ...], value_cols: tuple[str, ...], *, extend_mt5: bool = False):
    """Resolve repeated interpolation coordinates while preserving source values."""
    with src.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f)); fields = list(rows[0])
    groups = {}
    for row in rows:
        groups.setdefault(tuple(row[c] for c in key_cols), []).append(row)
    keep, actions = [], []
    for key, items in groups.items():
        vals = [tuple(row[c] for c in value_cols) for row in items]
        if len(items) == 1:
            keep.append(items[0]); continue
        if len(set(vals)) == 1:
            keep.append(items[-1])
            actions.append({"kind":"exact_duplicate_dedup","key":key,"n":len(items)})
        else:
            for idx, source in enumerate(items):
                row = dict(source)
                if idx < len(items)-1:
                    coord = key_cols[-1]; x = float(row[coord])
                    row[coord] = repr(float(np.nextafter(x, -np.inf)))
                keep.append(row)
            actions.append({"kind":"conflicting_duplicate_left_limit","key":key,"values":vals})

    if extend_mt5:
        mt5 = [r for r in keep if int(r["mt"]) == 5]
        first = min(mt5, key=lambda r: float(r["energy_mev"]))
        if float(first["energy_mev"]) > 0.1 and float(first["sigma_barn"]) == 0.0:
            row = dict(first); row["energy_mev"] = "0.1"; keep.append(row)
            actions.append({"kind":"zero_threshold_extension","mt":5,"from_mev":float(first["energy_mev"]),"to_mev":0.1,"sigma_barn":0.0})
        last = max(mt5, key=lambda r: float(r["energy_mev"]))
        emax = float(last["energy_mev"])
        if emax < 390.0:
            # Nuclear tables stop at 200 MeV. Do not extrapolate a reaction model.
            # CSDA transport is retained; nonelastic correction is explicitly zero
            # immediately above the TENDL support and this limitation is reported.
            left = dict(last); left["energy_mev"] = repr(float(np.nextafter(emax, np.inf))); left["sigma_barn"] = "0.0"
            high = dict(last); high["energy_mev"] = "390.0"; high["sigma_barn"] = "0.0"
            keep.extend((left, high))
            actions.append({"kind":"zero_nonelastic_above_tendl_support","mt":5,"support_max_mev":emax,"extended_to_mev":390.0})

    def sort_key(row):
        return tuple(int(row[c]) if c in {"mt","product_index"} else float(row[c]) for c in key_cols)
    keep.sort(key=sort_key)
    with dst.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(keep)
    return actions


def _load_radar(root: Path):
    sys.path.insert(0, str(root / "src"))
    from radar.core.spectra import Spectrum1D
    from radar.core.types import Particle, RadiationSource, SpectrumQuantity
    from radar.core.units import Unit
    from radar.shielding.proton_al import ProtonAlRangeEnergyTable, load_proton_al_range_energy_table
    from radar.shielding.proton_al_survival import apply_proton_nonelastic_survival_to_primary_spectrum, load_al27_nonelastic_cross_section_table
    from radar.shielding.proton_al_secondary import calculate_secondary_proton_spectrum_through_al, load_secondary_proton_kernel
    return locals()


def _make_spectrum(rad, energy, values):
    return rad["Spectrum1D"](
        x=tuple(map(float, energy)), y=tuple(map(float, values)),
        x_unit=rad["Unit"].MEV, y_unit=rad["Unit"].DIFFERENTIAL_FLUX,
        quantity=rad["SpectrumQuantity"].MEAN_DIFFERENTIAL_FLUX,
        particle=rad["Particle"].PROTON, source=rad["RadiationSource"].SEP,
        model="RE-GOES19-PROTON-RATE-01-adapter",
    )


def _grid(n: int) -> np.ndarray:
    return np.geomspace(0.11, 390.0, n)


def _prepare_physics(root: Path, temp: Path):
    rad = _load_radar(root); data = root / "src/radar/data/normative"
    base = rad["load_proton_al_range_energy_table"](data / "stopping/proton_al_range.csv")
    # Pinned secondary integration can request an inverse range between zero and
    # the first tabulated positive range. Add only the physical R->0 endpoint.
    stopping = rad["ProtonAlRangeEnergyTable"](
        energy_mev=(1.0e-9,) + tuple(base.energy_mev),
        range_g_cm2=(0.0,) + tuple(base.range_g_cm2),
        stopping_mev_cm2_g=(base.stopping_mev_cm2_g[0],) + tuple(base.stopping_mev_cm2_g),
    )
    actions = [{"kind":"stopping_zero_range_endpoint","energy_mev":1e-9,"range_g_cm2":0.0,"original_first_energy_mev":float(base.energy_mev[0]),"original_first_range_g_cm2":float(base.range_g_cm2[0])}]
    xs, yy, pp = temp/"xs.csv", temp/"yield.csv", temp/"pdf.csv"
    actions += _normalize_rows(data/"tendl/p_al27_mf3_xs.csv", xs, ("mt","energy_mev"), ("sigma_barn",), extend_mt5=True)
    actions += _normalize_rows(data/"tendl/p_al27_mf6_proton_yield.csv", yy, ("mt","product_index","incident_energy_mev"), ("yield",))
    actions += _normalize_rows(data/"tendl/p_al27_mf6_proton_pdf.csv", pp, ("mt","product_index","incident_energy_mev","emitted_energy_mev"), ("pdf_per_mev",))
    nonelastic = rad["load_al27_nonelastic_cross_section_table"](xs, mt=5)
    kernel = rad["load_secondary_proton_kernel"](xs_path=xs, yield_path=yy, pdf_path=pp)
    return rad, stopping, nonelastic, kernel, actions


def build_matrices(root: Path, n: int, *, depth_steps: int, survival_steps: int):
    with tempfile.TemporaryDirectory() as td:
        rad, stopping, nonelastic, kernel, actions = _prepare_physics(root, Path(td))
        energy = _grid(n); identity = np.eye(n)
        primary = np.zeros((len(SHIELDS_MM), n, n)); secondary = np.zeros_like(primary)
        for di, mm in enumerate(SHIELDS_MM):
            thickness = mm / 10.0 * AL_DENSITY
            for j in range(n):
                spectrum = _make_spectrum(rad, energy, identity[j])
                p = rad["apply_proton_nonelastic_survival_to_primary_spectrum"](
                    spectrum=spectrum, stopping_table=stopping, cross_section_table=nonelastic,
                    thickness_g_cm2=thickness, integration_steps=survival_steps)
                s = rad["calculate_secondary_proton_spectrum_through_al"](
                    incident_spectrum=spectrum, stopping_table=stopping, kernel=kernel,
                    thickness_g_cm2=thickness, depth_steps=depth_steps)
                primary[di,:,j] = p.y; secondary[di,:,j] = s.y
        return energy, primary, secondary, actions


def _grid_comparison(coarse, fine, points):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from sigma_model import sigma_hat
    ec, pc, sc = coarse; ef, pf, sf = fine
    sig = sigma_hat(ef, points, "main_loglog"); cases = []
    for power in (0.0, 1.5, 3.0):
        jc = (ec/10.0)**(-power) * np.exp(-ec/350.0)
        jf = (ef/10.0)**(-power) * np.exp(-ef/350.0)
        for di, mm in enumerate(SHIELDS_MM):
            yc = (pc[di]+sc[di]) @ jc; yf = (pf[di]+sf[di]) @ jf
            yc_i = np.interp(np.log(ef), np.log(ec), yc, left=0.0, right=0.0)
            lc = float(np.trapezoid(yc_i*sig, ef)); lf = float(np.trapezoid(yf*sig, ef))
            rel = abs(lf-lc)/max(abs(lf),1e-300)
            cases.append({"kind":"energy_grid","power":power,"shield_mm":mm,"coarse_n":len(ec),"fine_n":len(ef),"relative_change":rel})
    return cases


def validate_and_choose_grid(root: Path, sigma_csv: Path):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from sigma_model import load_experimental_points, sigma_hat
    points = load_experimental_points(sigma_csv)
    grid_cases = []; previous = None; selected = None; actions = None
    for n in GRID_CANDIDATES:
        e,p,s,actions = build_matrices(root, n, depth_steps=24, survival_steps=64)
        current = (e,p,s)
        if previous is not None:
            pair_cases = _grid_comparison(previous, current, points); grid_cases += pair_cases
            pair_max = max(x["relative_change"] for x in pair_cases)
            if pair_max <= CONVERGENCE_LIMIT:
                selected = current; break
        previous = current
    if selected is None:
        raise RuntimeError(f"energy-grid convergence did not reach {CONVERGENCE_LIMIT:.3%} by n={GRID_CANDIDATES[-1]}")

    ef,pf,sf = selected; sig = sigma_hat(ef, points, "main_loglog")
    depth_cases = []
    with tempfile.TemporaryDirectory() as td:
        rad, stopping, nonelastic, kernel, _ = _prepare_physics(root, Path(td))
        incident = (ef/10.0)**(-1.5)*np.exp(-ef/350.0); spectrum = _make_spectrum(rad, ef, incident)
        for mm in SHIELDS_MM[1:]:
            thickness = mm/10.0*AL_DENSITY
            p = rad["apply_proton_nonelastic_survival_to_primary_spectrum"](
                spectrum=spectrum, stopping_table=stopping, cross_section_table=nonelastic,
                thickness_g_cm2=thickness, integration_steps=64)
            vals=[]
            for steps in (24,48):
                s = rad["calculate_secondary_proton_spectrum_through_al"](
                    incident_spectrum=spectrum, stopping_table=stopping, kernel=kernel,
                    thickness_g_cm2=thickness, depth_steps=steps)
                vals.append(float(np.trapezoid((np.asarray(p.y)+np.asarray(s.y))*sig, ef)))
            depth_cases.append({"kind":"secondary_depth","shield_mm":mm,"coarse_steps":24,"fine_steps":48,"relative_change":abs(vals[1]-vals[0])/max(abs(vals[1]),1e-300)})
    return len(ef), grid_cases, depth_cases, actions


def monoenergetic_checks(root: Path, energy, primary):
    checks=[]
    with tempfile.TemporaryDirectory() as td:
        _, stopping, _, _, _ = _prepare_physics(root, Path(td))
        for target in (20.0,50.0,100.0,180.0):
            j=int(np.argmin(abs(energy-target))); ein=float(energy[j]); rin=stopping.range_at_energy(ein)
            for di,mm in enumerate(SHIELDS_MM[1:],start=1):
                thickness=mm/10.0*AL_DENSITY
                if rin <= thickness: continue
                expected=float(stopping.energy_at_range(rin-thickness))
                col=primary[di,:,j]; observed=float(energy[int(np.argmax(col))]) if np.max(col)>0 else float('nan')
                rel=abs(observed-expected)/expected
                checks.append({"incident_grid_mev":ein,"shield_mm":mm,"expected_csda_exit_mev":expected,"observed_primary_peak_mev":observed,"relative_peak_error":rel})
    return checks


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--radar-root",type=Path,required=True); ap.add_argument("--sigma-csv",type=Path,required=True); ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    sha=_git_sha(a.radar_root)
    if sha != RADAR_SHA: raise SystemExit(f"RADAR SHA mismatch: {sha}")

    selected_n, grid_cases, depth_cases, _ = validate_and_choose_grid(a.radar_root, a.sigma_csv)
    energy, primary, secondary, actions = build_matrices(a.radar_root, selected_n, depth_steps=48, survival_steps=128)
    mono = monoenergetic_checks(a.radar_root, energy, primary)
    d0p=float(np.max(np.abs(primary[0]-np.eye(selected_n)))); d0s=float(np.max(np.abs(secondary[0])))
    final_grid=[x for x in grid_cases if x["fine_n"]==selected_n]
    report={
        "radar_sha":sha,"grid_points":selected_n,"energy_min_mev":float(energy[0]),"energy_max_mev":float(energy[-1]),
        "production_depth_steps":48,"production_survival_steps":128,
        "d0_primary_identity_max_abs":d0p,"d0_secondary_max_abs":d0s,
        "secondary_nonnegative":bool(np.all(secondary>=-1e-15)),"primary_nonnegative":bool(np.all(primary>=-1e-15)),
        "normalization_actions":actions,"convergence_cases":grid_cases+depth_cases,
        "final_energy_grid_max_relative_change":max(x["relative_change"] for x in final_grid),
        "max_secondary_depth_relative_change":max(x["relative_change"] for x in depth_cases),
        "energy_grid_convergence_pass":max(x["relative_change"] for x in final_grid)<=CONVERGENCE_LIMIT,
        "secondary_depth_convergence_pass":max(x["relative_change"] for x in depth_cases)<=CONVERGENCE_LIMIT,
        "monoenergetic_csda_checks":mono,
        "monoenergetic_max_relative_peak_error":max(x["relative_peak_error"] for x in mono),
        "high_energy_nuclear_domain_note":"Pinned compact TENDL nonelastic/secondary tables end at 200 MeV. The adapter retains CSDA primary transport but applies no nuclear correction above support; the task quantifies the >200-MeV rate contribution separately.",
    }
    np.savez_compressed(a.out/"radar_transport.npz",energy_mev=energy,shield_mm=np.array(SHIELDS_MM),primary=primary,secondary=secondary)
    (a.out/"radar_validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
