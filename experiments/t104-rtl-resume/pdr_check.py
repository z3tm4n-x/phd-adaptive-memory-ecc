"""Unbounded RPC safety: actual RTL -> AIGER -> ABC IC3/PDR.

Check property totals, constraints, undecided properties and the engine's
invariant validation, not exit code alone. Not physical timing or liveness.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = (
    ("historical-8", "formal_rpc", 8, 8, 5, False),
    ("contract-8", "formal_rpc_contract", 8, 8, 9, False),
    ("app-256-97", "formal_rpc_contract", 256, 97, 9, False),
    ("command-416-32", "formal_rpc_contract", 416, 32, 9, False),
    ("early-credit-mutant", "formal_rpc_contract", 8, 8, 9, True),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify(header, log, expected, returncode):
    """Reject vacuity, assumptions, partial/ambiguous and zero-exit failures."""
    fields = header.split()
    if len(fields) != 10 or fields[0] != "aig":
        raise ValueError("unexpected AIGER 1.9 header")
    if int(fields[6]) != expected or any(int(x) for x in fields[7:10]):
        raise ValueError("wrong assertion count or unexpected AIGER constraints")
    matches = re.findall(
        r"Properties:\s+All\s*=\s*(\d+)\.\s+Proved\s*=\s*(\d+)\.\s+"
        r"Disproved\s*=\s*(\d+)\.\s+Undecided\s*=\s*(\d+)\.", log)
    if returncode != 0 or len(matches) != 1:
        return {"status": "inconclusive", "reason": "engine failure or missing/ambiguous totals"}
    total, proved, disproved, undecided = map(int, matches[0])
    if total != expected or proved+disproved+undecided != total:
        raise ValueError("inconsistent proof totals")
    validated = bool(re.search(r"Verification of invariant with \d+ clauses was successful\.", log))
    status = ("disproved" if disproved else
              "proved" if proved == total and validated else "inconclusive")
    return {"status": status, "all": total, "proved": proved,
            "disproved": disproved, "undecided": undecided,
            "engine_validated_inductive_invariant": validated}


def one(case, seconds):
    name, top, request_bits, reply_bits, assertions, mutant = case
    out = HERE / ".build" / ("pdr-"+name)
    out.mkdir(parents=True, exist_ok=True)
    rtl = HERE / "rtl/rpc_cdc.sv"
    source = rtl.read_text(encoding="utf-8")
    if mutant:
        old = "assign src_ready = request==credit_sync[2];"
        if source.count(old) != 1:
            raise AssertionError("mutation target drifted")
        source = source.replace(old, "assign src_ready = request==response_sync[2];")
    # Separate build copy even for mutants: never edit production RTL.
    (out / "dut.sv").write_text(source, encoding="utf-8")
    harness = HERE / "formal" / ("rpc.sv" if top == "formal_rpc" else "rpc_contract.sv")
    params = (f"-set BITS {request_bits}" if top == "formal_rpc" else
              f"-set REQUEST_BITS {request_bits} -set REPLY_BITS {reply_bits}")
    script = (f'read_verilog -formal -sv dut.sv "{harness}"; '
              f'chparam {params} {top}; prep -top {top}; '
              'flatten; clk2fflogic; opt; techmap; opt; abc -g AND; opt_clean; '
              'write_aiger -zinit -symbols -map rpc.map rpc.aig')
    (out / "build.ys").write_text(script+"\n", encoding="utf-8")
    start = time.monotonic()
    synthesis = subprocess.run(["yosys", "-Q", "-T", "-s", "build.ys"], cwd=out,
                               text=True, capture_output=True, timeout=90)
    (out / "yosys.log").write_text(synthesis.stdout+synthesis.stderr, encoding="utf-8")
    synthesis.check_returncode()
    aig = out / "rpc.aig"
    header = aig.read_bytes().splitlines()[0].decode()
    command = f"read_aiger rpc.aig; pdr -a -v -d -I invariant.pla -T {seconds}"
    engine = subprocess.run(["yosys-abc", "-c", command], cwd=out, text=True,
                            capture_output=True, timeout=seconds+30)
    log = engine.stdout+engine.stderr
    (out / "abc.log").write_text(log, encoding="utf-8")
    result = classify(header, log, assertions, engine.returncode)
    result.update({"name": name, "top": top, "request_bits": request_bits,
        "reply_bits": reply_bits, "mutant": mutant,
        "elapsed_s": round(time.monotonic()-start, 3), "aiger_header": header,
        "aiger_sha256": sha(aig), "rtl_sha256": sha(rtl), "build_dut_sha256": sha(out/"dut.sv"),
        "harness_sha256": sha(harness), "abc_command": command,
        "abc_log_sha256": sha(out/"abc.log"), "engine_exit_code": engine.returncode,
        "invariant_sha256": sha(out/"invariant.pla") if (out/"invariant.pla").exists() else None})
    result["check_met"] = result["status"] == ("disproved" if mutant else "proved")
    (out / "result.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result), flush=True)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case", choices=[c[0] for c in CASES])
    p.add_argument("--seconds", type=int, default=60)
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    if args.seconds < 1:
        p.error("positive time limit required")
    if args.write and args.case:
        p.error("canonical output requires the whole suite")
    selected = [c for c in CASES if args.case is None or c[0] == args.case]
    results = [one(c, args.seconds) for c in selected]
    report = {"yosys": subprocess.check_output(["yosys", "-V"], text=True).strip(),
        "abc_executable_sha256": sha(shutil.which("yosys-abc")),
        "seconds_per_case": args.seconds, "cases": results,
        "scope": "RPC safety from declared initialization under arbitrary Boolean clock edges",
        "endpoint_contract": "accept once, arbitrary delayed reply, retain until retire; no fairness",
        "limitations": ["no physical metastability or bundled-data timing qualification",
                        "no liveness bound without clocks/endpoint/backpressure bounds",
                        "not composition with actual executor queue/calendar/E endpoint",
                        "Yosys/ABC translation and invariant validator are trusted dependencies"]}
    if args.write:
        (HERE/"outputs/pdr.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    return 0 if all(r["check_met"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
