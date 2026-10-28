"""Only published-spectrum arithmetic; no environment, Q or cost model runs."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def plot_interval(axis, y_interval):
    # Image y grows down; flux grows up. The inputs are manual readout bounds.
    lo, hi = y_interval
    assert lo <= hi
    return [10 ** (11 + (axis["y_at_1e11"] - y) /
                   axis["pixels_per_decade_y"]) for y in (hi, lo)]


def sep_fraction_from_total(trapped, total):
    assert 0 <= trapped[0] <= trapped[1]
    assert 0 < total[0] <= total[1] and trapped[0] <= total[1]
    # Enclose all combinations compatible with nonnegative SEP = total - trapped.
    return [max(0.0, 1 - trapped[1] / total[0]),
            min(1.0, 1 - trapped[0] / total[1])]


def calculate(data):
    out = {"status": data["status"], "orbits": {}}
    leo = data["LEO_51_6"]
    rows = []
    for row in leo["rows"]:
        t = row["trapped_per_day_cm2"] * leo["days_per_year_assumption"]
        s = row["sep_per_year_cm2_interval"]
        assert 0 < s[0] <= s[1] and t > 0
        f = [x / (t + x) for x in s]
        rows.append({"theta_MeV": row["theta_MeV"],
                     "trapped_per_year_cm2": t, "f_SEP_interval": f})
    out["orbits"]["LEO_51_6"] = {"rows": rows}
    graph = data["GUILD_graph_reading"]
    for orbit in ("SSO", "GEO"):
        rows = []
        for row in graph[orbit]["rows"]:
            t = (plot_interval(graph["figure10"], row["trapped_y_interval_px"])
                 if orbit == "SSO" else [0, graph[orbit]["trapped_upper_cm2"]])
            total = plot_interval(graph["figure12"], row["total_y_interval_px"])
            rows.append({"theta_MeV": row["theta_MeV"],
                         "trapped_10y_cm2_interval": t,
                         "total_10y_cm2_interval": total,
                         "f_SEP_interval": sep_fraction_from_total(t, total)})
        out["orbits"][orbit] = {"rows": rows}
    for result in out["orbits"].values():
        fractions = [row["f_SEP_interval"] for row in result["rows"]]
        hull = [min(f[0] for f in fractions), max(f[1] for f in fractions)]
        result["f_SEP_threshold_family_hull"] = hull
        # beta_tr is unbounded except by [0,1]; no forecast calibration is invented.
        result["alpha_scenario_hull_beta_tr_unknown"] = [hull[0], 1.0]
        result["physical_bank_alpha"] = "UNKNOWN"
        result["grid_upper_scenario_only"] = 1
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sources-dir", type=Path)
    args = parser.parse_args()
    data = json.loads((ROOT / "INPUTS.json").read_text(encoding="utf-8"))
    if args.sources_dir:
        for source in data["sources"]:
            path = args.sources_dir / source["local_filename"]
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != source["sha256"]:
                raise ValueError(f"Source hash mismatch: {path}")
    result = calculate(data)
    target = ROOT / "RESULTS.json"
    if args.check:
        saved = json.loads(target.read_text(encoding="utf-8"))
        if saved != result:
            raise ValueError("RESULTS.json differs from reproduction")
        print("OK: arithmetic reproduced" +
              ("; three source PDF hashes verified" if args.sources_dir else ""))
    else:
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
