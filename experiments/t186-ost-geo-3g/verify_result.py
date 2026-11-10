"""Independent scalar integration. Optional check of the frozen 5-minute SEPEM H cache."""

import argparse
from bisect import bisect_right
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path

from scipy.integrate import quad

HERE = Path(__file__).resolve().parent
EXP = HERE.parent


def compare(actual, saved, path="result"):
    if isinstance(actual, dict):
        assert actual.keys() == saved.keys(), path
        for key, value in actual.items():
            compare(value, saved[key], f"{path}.{key}")
    elif isinstance(actual, (list, tuple)):
        assert len(actual) == len(saved), path
        for i, value in enumerate(actual):
            compare(value, saved[i], f"{path}[{i}]")
    elif isinstance(actual, float):
        assert math.isclose(actual, saved, rel_tol=2e-11, abs_tol=1e-19), path
    else:
        assert actual == saved, path


def interpolate(x, grid, values, proton):
    i = min(len(grid) - 2, max(0, bisect_right(grid, x) - 1))
    u = math.log(x / grid[i]) / math.log(grid[i + 1] / grid[i])
    a, b = values[i:i + 2]
    if not proton and (a == 0 or b == 0):
        return (1 - u) * a + u * b
    y = math.exp((1 - u) * math.log(max(1e-300, a)) + u * math.log(max(1e-300, b)))
    return 0.0 if proton and y < 1e-290 else y


def export_data(name, proton):
    path = EXP / "t68-v21-inputs/inputs/cosrad_main" / name
    lines = path.read_text(encoding="ascii").splitlines()
    assert any("8col.-shielding=3.00E+0000" in line.replace(" ", "") for line in lines)
    pairs = []
    for line in lines:
        items = line.split()
        if len(items) == 10 and "E" in items[0] and items[0][0].isdigit():
            x, y = float(items[0]), float(items[7])
            pairs.append((x, y) if proton else (x / 1000, y * 1000))
    return pairs


def check_folds(result):
    with (EXP / "RE-CY62167-PROTON-01/sigma_bit_experimental.csv").open(encoding="utf-8-sig") as f:
        response = sorted((float(row["energy_mev"]), float(row["sigma_bit_cm2_per_bit"]))
                          for row in csv.DictReader(f) if row["sigma_bit_cm2_per_bit"].strip())
    energy, sigma = zip(*response)
    slope = (sigma[1] - sigma[0]) / (energy[1] - energy[0])
    zero = energy[0] - sigma[0] / slope

    def sigma_h(x):
        if x < energy[0]:
            return max(0, (x - zero) * slope)
        if x >= energy[-1]:
            return sigma[-1]
        return interpolate(x, energy, sigma, True)

    with (HERE / "ost_3g.csv").open(encoding="utf-8") as stream:
        columns = list(csv.DictReader(stream))
    for tid, details in result["table_rows"].items():
        proton = tid.endswith(".2")
        solar = tid.startswith("Л.3.1.")
        norm = [(float(r["coordinate"]), float(r["density_at_3g_cm2"])) for r in columns if r["table"] == tid]
        for source, pairs in (("ost", norm), ("cosrad", export_data(details["export"], proton))):
            grid, flux = zip(*pairs)
            def integrand(x):
                if proton:
                    cross = sigma_h(x)
                else:
                    cross = 0.0 if x <= 0.15 or (solar and x > 32.6) else (
                        -2.6e-7 * math.expm1(-((x - 0.15) / 70.0)**1.2))
                return 19922944 * cross * interpolate(x, grid, flux, proton)
            cases = [("native_s_inv", grid[0], grid[-1]), ("common_s_inv", *details["common_range"])]
            if proton:
                cases.extend([("H_1_to_5_MeV_s_inv", 1.0, 5.0), ("H_5_to_max_MeV_s_inv", 5.0, grid[-1])])
                if grid[0] < 1:
                    cases.append(("native_below_common_s_inv", grid[0], 1.0))
            for key, lo, hi in cases:
                knots = (*energy, zero, 5) if proton else (0.15, 32.6)
                cuts = sorted({lo, hi, *(x for x in (*grid, *knots) if lo < x < hi)})
                y = math.fsum(quad(integrand, a, b, epsabs=1e-19, epsrel=2e-11)[0]
                              for a, b in zip(cuts, cuts[1:]))
                assert math.isclose(y, details[source][key], rel_tol=2e-8, abs_tol=1e-17), (tid, source, key, y)


def check_bins(cache, result):
    import numpy as np
    metadata = json.loads((EXP / "t141-radiation-chain/outputs/profile-provenance.json").read_text(encoding="utf-8"))
    path = cache / "bands.npy"
    with path.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == metadata["input"]["arrays_sha256"]["bands.npy"]
    bins = np.load(path, mmap_mode="r")[:, 1, :].sum(axis=1)
    h = np.maximum(bins - np.quantile(bins, 0.1), 0.0)
    b = result["ost_tabulated"]["b"]
    excess = (1 + result["archive"]["beta_ost_tabulated"]) * h
    width = 315576000 // 300
    sums = np.r_[0., np.cumsum(excess, dtype="float64")]
    i = int(np.argmax(sums[width:] - sums[:-width]))
    archived = result["archive"]["archives_on_transferred_profiles"]["SEPEM_archive"]
    assert len(h) - width + 1 == result["archive"]["old_archive"]["SEPEM_windows"]
    assert math.isclose(b * 315576000 + 300 * math.fsum(excess[i:i + width]),
                        archived["S1_on_accepted_windows_or_gap_completion"], abs_tol=1e-6, rel_tol=0)
    assert math.isclose(2 * np.diff(excess).max() / 300, archived["max_upward_slope_inside_bins"], rel_tol=2e-12)


def check_goes_pair(cache, result):
    import numpy as np
    cadence = json.loads((EXP / "c1-common-geo-20261109/cadence.json").read_text(encoding="utf-8"))
    info = json.loads((EXP / "c1-geo-fixed-20261109/goes.json").read_text(encoding="utf-8"))
    pair = cadence["decisive_raw_quality"]
    with (cache / "raw" / pair["name"]).open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == pair["sha256"]
    assert pair["direction"] == "East"
    epoch = datetime.fromisoformat("2017-01-01T00:00:00+00:00")
    minutes = [int((datetime.fromisoformat(row["utc"]) - epoch).total_seconds()) // 60
               for row in pair["bins"]]
    assert minutes[1] == minutes[0] + 1
    with np.load(cache / "folded" / (pair["name"] + ".npz")) as sample:
        index = np.searchsorted(sample["index"], minutes)
        assert np.array_equal(sample["index"][index], minutes)
        h = sample["values"][index, 0, :2].sum(axis=1)
    beta = result["archive"]["beta_ost_tabulated"]
    nu = result["ost_tabulated"]["b"] + (1 + beta) * np.maximum(h - info["directions"]["East"]["proton_p10_per_s"], 0)
    assert math.isclose((nu[1] - nu[0]) / 60, result["archive"]["observed_max_upward_mean_slope_new"], rel_tol=2e-12)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sepem-cache", type=Path)
    parser.add_argument("--goes-minute-cache", type=Path)
    args = parser.parse_args()
    data = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
    check_folds(data)
    if args.sepem_cache:
        check_bins(args.sepem_cache, data)
    if args.goes_minute_cache:
        check_goes_pair(args.goes_minute_cache, data)
    print("OK: independent response, interpolation, adaptive quadrature and requested archive checks")
