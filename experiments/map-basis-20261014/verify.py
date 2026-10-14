"""Read-only audit of T161 transfers and existing arithmetic, not a new model."""
import argparse
import csv
from fractions import Fraction as F
import hashlib
import io
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git_blob(commit, path):
    return subprocess.check_output(["git", "show", commit + ":" + path], cwd=ROOT)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def pointer(obj, path):
    for part in path.split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def near(a, b):
    return abs(float(a) - float(b)) <= 2e-12 * max(1, abs(float(b)))


def main(record=False):
    data = json.loads((HERE / "examples.json").read_bytes())
    manifest = json.loads((HERE / "sources.json").read_bytes())
    require(data["base"] == manifest["base"], "base mismatch")
    raw_sources = {}
    differences = []
    for key, source in manifest["sources"].items():
        raw = git_blob(source["commit"], source["path"])
        require(sha256(raw) == source["sha256"], key + ": sha256")
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        require(blob == source["git_blob"], key + ": Git blob")
        raw_sources[key] = raw
        base_raw = git_blob(data["base"], source["path"])
        require((raw == base_raw) == source["identical_at_base"], key + ": base comparison")
        if raw != base_raw:
            difference = source["base_difference"]
            require(sha256(base_raw) == difference["sha256"], key + ": recorded difference")
            require(key == "146conditions", "unexpected source divergence: " + key)
            require(raw.replace("§4.3.3: наблюдаемые".encode(),
                                "§4.3.5: наблюдаемые".encode()) == base_raw,
                    "T146 difference is no longer locator-only")
            differences.append(key)
    for acceptance in manifest["acceptances"]:
        require(acceptance["scientific_sha"].encode() in raw_sources["acceptance"],
                acceptance["id"] + ": acceptance SHA absent from pinned MAP")

    parsed = {}
    gaps = {g["id"] for g in data["gaps"]}
    transfers = unknowns = 0

    def walk(value):
        nonlocal transfers, unknowns
        if isinstance(value, dict):
            if "value" in value:
                require(value.get("unit") and value.get("kind") and value.get("evidence"),
                        "untyped cell")
                if value["value"] is None:
                    require(value["kind"] == "unknown" and value["gap"] in gaps
                            and value["evidence"] == "UNKNOWN", "unnamed unknown")
                    unknowns += 1
                else:
                    ref = value["source"]
                    key = ref["source"]
                    if key not in parsed:
                        raw = raw_sources[key]
                        parsed[key] = (json.loads(raw) if "pointer" in ref else
                                       list(csv.DictReader(io.StringIO(raw.decode("utf-8")))))
                    if "pointer" in ref:
                        original = pointer(parsed[key], ref["pointer"])
                    else:
                        selected = [r for r in parsed[key] if all(
                            r[k] == v for k, v in ref["where"].items())]
                        require(len(selected) == 1, "ambiguous CSV row: " + key)
                        original = selected[0][ref["column"]]
                    require(type(original) is type(value["value"])
                            and original == value["value"], "transfer changed: " + str(ref))
                    transfers += 1
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data["entries"])
    rows = {r["id"]: r for r in data["entries"]}
    expected = {"R0A_ERR_T119_ka5", "R0A_r4_B_V", "R0A_fullU_T146",
                "A2_T140_pointwise", "CY_T150_shape_input"}
    require(set(rows) == expected and len(data["entries"]) == 5, "five distinct contracts")
    for row in rows.values():
        require(set(row["gaps"]) <= gaps, "undefined gap")
        for key in ("radiation", "word", "observations", "service", "useful_work",
                    "price_metric", "fixed", "metrics", "potentials", "next_action"):
            require(row.get(key), row["id"] + ": missing " + key)
    e, r, u, a, s = (rows[key] for key in (
        "R0A_ERR_T119_ka5", "R0A_r4_B_V", "R0A_fullU_T146",
        "A2_T140_pointwise", "CY_T150_shape_input"))

    def val(row, section, key):
        return F(str(row[section][key]["value"]))

    def fixed(row, key):
        return F(str(row["fixed"]["metrics"][key]["value"]))

    checks = []

    def check(name, condition):
        require(condition, name)
        checks.append(name)

    check("T119 row name", pointer(parsed["119"], "/rows/3/name") == "one_presented")
    for row in (e, r, u):
        check(row["id"] + ": source slack identity",
              val(row, "radiation", "epsilon") - val(row, "metrics", "Q_upper")
              == val(row, "metrics", "risk_slack"))
        check(row["id"] + ": F from same b,T,FS",
              val(row, "radiation", "F") == val(row, "radiation", "b")
              * val(row, "radiation", "T") + val(row, "radiation", "F_solar"))
    for key in ("T", "W", "n", "epsilon", "b", "B", "F_solar", "F"):
        check("old environment matching only: " + key,
              val(e, "radiation", key) == val(r, "radiation", key)
              == val(u, "radiation", key))
    for row in (e, u):
        check(row["id"] + ": gain ratio",
              val(row, "metrics", "G_cert")
              == fixed(row, "L_fixed") / val(row, "metrics", "U_adaptive"))
    for row in (r, a, s):
        check(row["id"] + ": no transplanted G_cert",
              row["metrics"]["G_cert"]["value"] is None)
    check("T146 tight S2 (not rounded 6940)",
          val(u, "radiation", "S2") == val(u, "radiation", "b")**2
          * val(u, "radiation", "T")
          + (val(u, "radiation", "B") + val(u, "radiation", "b"))
          * val(u, "radiation", "F_solar"))
    check("T146 whole-bus gain uses equal 4% application",
          val(u, "metrics", "whole_bus_G_at_equal_app_cap")
          == (fixed(u, "L_fixed") + F(".04")) / val(u, "metrics", "whole_bus"))
    for row in (u, a):
        check(row["id"] + ": diagnostic ideal identity on witness",
              val(row, "potentials", "ideal") == val(row, "radiation", "T")
              * val(row, "potentials", "witness_S2")
              / val(row, "potentials", "witness_F")**2)
    check("T146 oracle interval lower", val(u, "potentials", "declared_fixed_over_oracle_lower")
          == val(u, "potentials", "fixed_numerator_lower")
          / val(u, "potentials", "oracle_denominator_upper"))
    check("T146 oracle interval upper", val(u, "potentials", "declared_fixed_over_oracle_upper")
          == val(u, "potentials", "fixed_numerator_upper")
          / val(u, "potentials", "oracle_denominator_lower"))
    check("A2 pointwise ceiling direction", val(a, "metrics", "pointwise_gain_upper")
          == fixed(a, "witness_price") / val(a, "metrics", "pointwise_price_lower_free_information"))
    a2_inputs = parsed["140"]["inputs"]
    constant_pair = (F(a2_inputs["c_s"]) * F(a2_inputs["n"] - 1, 2 * a2_inputs["n"])
                     * F(a2_inputs["S2"]) / F(a2_inputs["epsilon"]))
    check("A2 numerator is continuous pair cost, not the Fixed witness",
          val(a, "potentials", "pair_constant_over_pair_relaxation")
          == constant_pair / val(a, "potentials", "pair_relaxation_denominator")
          and constant_pair != fixed(a, "witness_price"))
    check("T150 moments with full background cross term",
          near(val(s, "radiation", "S2"), val(s, "radiation", "b")**2
               * val(s, "radiation", "T") + 2 * val(s, "radiation", "b")
               * val(s, "radiation", "F_solar") + val(s, "radiation", "r")
               * val(s, "radiation", "solar_peak") * val(s, "radiation", "F_solar")))
    check("T150 ideal identity on SAME modeled moments",
          near(val(s, "potentials", "ideal"), val(s, "radiation", "T")
               * val(s, "radiation", "S2") / val(s, "radiation", "F")**2))
    check("T150 tested fixed exceeds full bus", fixed(s, "candidate_price") > 1)
    check("T150 negative sufficient channel threshold",
          val(s, "metrics", "sufficient_channel_D_max") < 0)
    check("reported T119 gain lower", val(e, "metrics", "G_cert") >= F("2.80545"))
    check("reported T146 gain lower", val(u, "metrics", "G_cert") >= F("5.251393"))
    check("reported A2 scoped strict ceiling", val(a, "metrics", "pointwise_gain_upper") < F("4.067058"))
    check("all five remaining groups have a concrete next input",
          len(data["remaining_groups"]) == 5
          and all(g["missing"] and g["next_action"] for g in data["remaining_groups"]))
    output = {
        "task": 161, "status": "PASS", "base": data["base"],
        "scope": "Source-byte/locator transfer and existing arithmetic only; no new scientific acceptance, physical qualification, MC or RTL run",
        "source_count": len(raw_sources), "transferred_numeric_cells": transfers,
        "explicit_unknown_cells": unknowns, "known_source_differences": differences,
        "arithmetic_and_scope_checks": checks,
        "local_inputs_sha256": {name: sha256((HERE / name).read_bytes()) for name in
                               ("examples.json", "sources.json", "REPORT.md", "README.md", "verify.py")},
    }
    if record:
        (HERE / "verification.json").write_text(json.dumps(output, ensure_ascii=False,
            indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in output.items()
                      if k not in ("arithmetic_and_scope_checks", "local_inputs_sha256")}, ensure_ascii=False))
    print("Existing arithmetic/scope checks:", len(checks))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true", help="write task-local verification.json")
    main(parser.parse_args().record)
