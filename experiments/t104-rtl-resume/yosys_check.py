"""Available-level formal/synthesis checks; no device library, STA or Fmax."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--steps", type=int, default=60)
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
        for module in ("e_backend", "absolute_calendar", "permission_gate"):
            log = run(f'read_verilog -sv "{HERE}/rtl/{module}.sv"; '
                      f'synth -top {module}; check; tee -o stats.json stat -json')
            s = json.loads((temp/"stats.json").read_text())
            stats[module] = s["modules"]["\\"+module]
        script = (f'read_verilog -formal -sv "{HERE}/rtl/e_backend.sv" "{HERE}/formal/backend.sv"; '
                  'prep -top formal_backend; flatten; async2sync; chformal -lower; '
                  f'sat -seq {args.steps} -set-def-inputs -prove-asserts -verify -timeout 60 '
                  '-show-public -dump_json counterexample.json')
        log = run(script)
        if "SUCCESS" not in log:
            raise AssertionError("no successful SAT proof reported")
        result = {"yosys": version, "backend_bounded_formal": {
            "core_steps": args.steps, "xi_ticks": args.steps*4, "word_address_bits": 19,
            "assertion_status": "proved over the bounded initial-state traces",
            "assertions": 17,
            "assumptions": "RTL initialization; defined Boolean synchronous inputs, arbitrary go/reset/data/ERR",
            "not_proved": "induction/full mission, physical E, metastability, integrated arbitration/queue"},
            "generic_synthesis": stats, "platform_STA": None,
            "scope": "generic logic cells, not FPGA LUT/FF/Fmax or WCET"}
        if args.write:
            (HERE/"outputs/yosys.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
