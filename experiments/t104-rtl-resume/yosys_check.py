"""Available-level formal/synthesis checks; no device library, STA or Fmax."""
import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--steps", type=int, default=60)
    parser.add_argument("--rpc-steps", type=int, default=40)
    args = parser.parse_args()
    build = HERE / ".build"
    build.mkdir(exist_ok=True)
    version = subprocess.check_output(["yosys", "-V"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="yosys-", dir=build) as td:
        temp = Path(td)
        # Paths are quoted for spaces; Yosys reads Unicode source paths here.
        def run(script, timeout=90):
            p = subprocess.run(["yosys", "-Q", "-T", "-p", script], cwd=temp,
                               text=True, capture_output=True, timeout=timeout)
            if p.returncode:
                (build/"last_formal_failure.log").write_text(p.stdout+p.stderr, encoding="utf-8")
                if (temp/"counterexample.json").exists():
                    shutil.copyfile(temp/"counterexample.json", build/"counterexample.json")
                raise RuntimeError((p.stdout+p.stderr)[-7000:])
            return p.stdout
        stats = {}
        spacing_log = run(f'read_verilog -formal -sv "{HERE}/formal/spacing.sv"; '
                          'prep -top spacing; flatten; chformal -lower; '
                          'sat -set-def-inputs -prove-asserts -verify -timeout 30')
        if "SUCCESS" not in spacing_log:
            raise AssertionError("64-bit spacing equivalence not proved")
        for module in ("e_backend", "absolute_calendar", "permission_gate"):
            log = run(f'read_verilog -sv "{HERE}/rtl/{module}.sv"; '
                      f'synth -top {module}; check; tee -o stats.json stat -json')
            s = json.loads((temp/"stats.json").read_text())
            stats[module] = s["modules"]["\\"+module]
        from integration_check import MODULES
        sources = " ".join(f'"{HERE}/rtl/{m}.sv"' for m in MODULES)
        run(f'read_verilog -sv {sources}; synth -top executor; check; tee -o stats.json stat -json')
        stats["integrated_executor"] = json.loads((temp/"stats.json").read_text())["design"]
        script = (f'read_verilog -formal -sv "{HERE}/rtl/e_backend.sv" "{HERE}/formal/backend.sv"; '
                  'prep -top formal_backend; flatten; async2sync; chformal -lower; '
                  f'sat -seq {args.steps} -set-def-inputs -prove-asserts -verify -timeout 60 '
                  '-show-public -dump_json counterexample.json')
        log = run(script)
        if "SUCCESS" not in log:
            raise AssertionError("no successful SAT proof reported")
        induction_script = (f'read_verilog -formal -sv "{HERE}/rtl/e_backend.sv" "{HERE}/formal/backend.sv"; '
            'prep -top formal_backend; flatten; async2sync; chformal -lower; opt_clean; '
            'sat -seq 1 -tempinduct -maxsteps 64 -set-def-inputs -prove-asserts -verify -timeout 30')
        induction_log = run(induction_script, timeout=90)
        if "Induction step proven: SUCCESS" not in induction_log:
            raise AssertionError("backend induction not closed")
        induction_k = int(re.findall(r"\[induction step (\d+)\]", induction_log)[-1])
        rpc_script = (f'read_verilog -formal -sv "{HERE}/rtl/rpc_cdc.sv" "{HERE}/formal/rpc.sv"; '
                      'prep -top formal_rpc; flatten; clk2fflogic; chformal -lower; '
                      f'sat -seq {args.rpc_steps} -set-def-inputs -prove-asserts -verify -timeout 60 '
                      '-show-public -dump_json counterexample.json')
        rpc_log = run(rpc_script)
        if "SUCCESS" not in rpc_log:
            raise AssertionError("no successful multi-clock RPC proof")
        result = {"yosys": version,
            "spacing_equivalence": {"assertions": 2, "timestamp_bits": 64, "status": "proved",
                                    "scope": "separate arithmetic miter; full core covered by regression, not this proof"},
            "backend_bounded_formal": {
            "core_steps": args.steps, "xi_ticks": args.steps*4, "word_address_bits": 19,
            "assertion_status": "proved over the bounded initial-state traces",
            "assertions": 24,
            "assumptions": "RTL initialization; defined Boolean synchronous inputs, arbitrary go/reset/data/ERR",
            "not_proved": "physical E, metastability, integrated arbitration/queue"},
            "backend_induction": {"k": induction_k, "assertions": 24, "word_address_bits": 19,
                "status": "proved for all synchronous steps from declared RTL initialization",
                "scope": "backend atomicity/control properties, not whole-executor induction"},
            "rpc_bounded_formal": {"global_steps": args.rpc_steps, "assertions": 5,
                "payload_bits": 8, "clock_model": "arbitrary defined source/destination edges via clk2fflogic",
                "status": "bounded safety; no fairness/liveness or physical metastability guarantee"},
            "inconclusive_attempts": ["RPC 8-bit100-step BMC:60s solver timeout",
                "RPC 1-bit k-induction through40: base cases proved, induction not closed",
                "backend17-assertion induction:90s timeout; strengthened reachable-state assertions then proved"],
            "generic_synthesis": stats, "platform_STA": None,
            "scope": "generic logic cells, not FPGA LUT/FF/Fmax or WCET"}
        if args.write:
            (HERE/"outputs/yosys.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
