"""Read immutable Git blobs; hourly serialized values are exact rationals."""
import csv
import datetime as dt
import hashlib
import io
import json
import subprocess
from fractions import Fraction as F
from certificate import rarity


def blob(repo, ref, path, expected=None):
    content = subprocess.check_output(["git", "-C", str(repo), "show", f"{ref}:{path}"])
    if expected and hashlib.sha256(content).hexdigest() != expected:
        raise ValueError(f"source checksum mismatch: {path}")
    return content


def history(content, cfg):
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8"))))
    start = dt.datetime.fromisoformat(cfg["scenario"]["calendar_start"].replace("Z", "+00:00"))
    end = dt.datetime.fromisoformat(cfg["scenario"]["calendar_end_exclusive"].replace("Z", "+00:00"))
    if len(rows) != int((end-start).total_seconds())//3600:
        raise ValueError("incomplete historical calendar")
    nu, backgrounds, masks, timestamps = [], [], [], []
    for i, row in enumerate(rows):
        timestamp = (start+dt.timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if row["timestamp_utc"] != timestamp or int(row["hour_index"]) != i:
            raise ValueError("duplicate/gap/order in hourly series")
        if row["is_missing_proton"] not in ("true", "false"):
            raise ValueError("unknown missing mask")
        missing = row["is_missing_proton"] == "true"
        if missing != (row["upsets_proton_raw"] == ""):
            raise ValueError("raw/missing mask mismatch")
        if row["fill_method"] != ("linear_interpolation" if missing else "raw"):
            raise ValueError("unexpected imputation policy")
        value = F(row["upsets_total_nu"])/3600
        gp = F(row["background_proton_gp"])*F("11.7")/3600
        if value < 0 or gp < 0:
            raise ValueError("negative hourly intensity")
        nu.append(value)
        backgrounds.append(gp)
        masks.append(missing)
        timestamps.append(timestamp)
    T, N = F(len(rows)*3600), cfg["scenario"]["n"]*cfg["scenario"]["W_reference"]
    I1 = sum(nu, F(0))*3600
    I2 = sum((x*x for x in nu), F(0))*3600
    B, b = max(nu), max(backgrounds)
    FS = sum((max(F(0), x-b) for x in nu), F(0))*3600
    exposure, square = rarity(B, b, FS, T)
    # Input serialization was 12 significant digits. Do not silently force
    # equality to the pre-serialization float summary.
    reconstructed_error = max(abs(F(row["upsets_total_nu"])-
        (F(row["background_proton_gp"])*F("11.7")+
         F(row["event_proton_sp"])*4)) for row in rows)
    groups = {}
    for label, indices in [("all", range(len(rows))),
                           ("not_imputed", [i for i in range(len(rows)) if not masks[i]])]:
        groups[label] = dict(hours=len(indices),
            I1_nu=sum((nu[i]*3600 for i in indices), F(0)),
            I2_nu_s_inverse=sum((nu[i]*nu[i]*3600 for i in indices), F(0)))
    growth = {}
    for label, pairs in [("all", range(1, len(rows))),
                         ("raw_neighbors", [i for i in range(1, len(rows))
                                            if not masks[i-1] and not masks[i]])]:
        allowed = [i for i in pairs if nu[i-1] > 0]
        j = max(allowed, key=lambda i: nu[i]/nu[i-1])
        growth[label] = dict(pairs=len(allowed), max_ratio=nu[j]/nu[j-1],
                             previous=timestamps[j-1], current=timestamps[j], step_s=3600)
    return dict(T_s=T, hours=len(rows), missing_hours=sum(masks),
        start=timestamps[0], end_exclusive=cfg["scenario"]["calendar_end_exclusive"],
        I1_nu=I1, I2_nu_s_inverse=I2, I1_per_bit=I1/N, I2_per_bit_s_inverse=I2/(N*N),
        mean_nu_s_inverse=I1/T, max_nu_s_inverse=B,
        max_timestamp=timestamps[nu.index(B)], bbar_diagnostic_nu_s_inverse=b,
        FS_diagnostic_nu=FS, F_diagnostic_nu=exposure, S2_diagnostic_nu_s_inverse=square,
        B_per_bit_s_inverse=B/N, bbar_per_bit_s_inverse=b/N,
        FS_per_bit=FS/N, F_per_bit=exposure/N, S2_per_bit_s_inverse=square/(N*N),
        initial_peak_duration_s=min(T, FS/(B-b)) if B > b else T,
        mean_background_nu_s_inverse=sum(backgrounds, F(0))/len(rows),
        J=I2*T/(I1*I1), serialized_reconstruction_max_error_per_hour=reconstructed_error,
        masks=groups, hourly_growth_diagnostic=growth)


def load_sources(master, project, cfg):
    content = blob(master, cfg["master_sha"], "data/ch3_five_year_upsets.csv",
                   "5b1f77b83c2c1a708c99663b7da13437414527e1a1ecebeee091bc71356eea22")
    original = json.loads(blob(master, cfg["master_sha"], "configs/ch3_main_1pct.json"))
    if original["geometry"] != {"word_bits": cfg["scenario"]["n"],
                                "codeword_count": cfg["scenario"]["W_reference"]}:
        raise ValueError("geometry mismatch")
    # Original XLSX availability/hash verified without re-running its writer.
    blob(master, cfg["master_sha"], "data/raw/upsets.xlsx",
         "06e042e70dd305e83ba78bfe291551ee32644bd3fd04d15c2e3d6fadbe2145dd")
    t52_checks = blob(project, cfg["t52_sha"], "theory/check_fixed_period_resource_contract.py",
                      "7789416e2754a887d0891e5b0708465ce29a3551107e942dcb14e2d4bbd078d8")
    archived = json.loads(blob(master, cfg["master_sha"], "results/schedules/ch3_series_import_summary.json"))
    h = history(content, cfg)
    if h["hours"] != original["expected_checks"]["hour_count"] or h["missing_hours"] != 148:
        raise ValueError("historical count mismatch")
    for actual, key in [(h["I1_nu"], "total_nu_sum"),
                        (h["max_nu_s_inverse"]*3600, "total_nu_max"),
                        (h["J"], "total_nu_eta_const")]:
        if abs(actual-F(str(archived["metrics"][key]))) > F("1e-8"):
            raise ValueError(f"archive regression: {key}")
    return h, t52_checks
