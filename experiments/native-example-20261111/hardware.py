"""Run reduced native8 fault scenarios or vendor synthesis, in a fresh work dir."""
import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import timing

HERE = Path(__file__).resolve().parent


def inject(work, checked):
    sim = work/"sim"
    subprocess.run(["iverilog","-g2012","-s","inject_tb",f"-Pinject_tb.CHECK_LOCAL={checked}","-o",sim,
                    HERE/"native8.sv", HERE/"inject_tb.sv"],check=True)
    for scenario in range(9):
        out = subprocess.check_output(["vvp",sim,f"+case={scenario}"],text=True)
        print(next(line for line in out.splitlines() if line.startswith("case=")),flush=True)


def synth(work, checked, reports):
    for name in ("native8.sv","synth.tcl"):
        shutil.copyfile(HERE/name,work/name)
    tool = shutil.which("vivado") or shutil.which("vivado-wsl") or str(Path.home()/"bin/vivado-wsl")
    with (work/"run.log").open("w") as log:
        run = subprocess.run([tool,"-mode","batch","-nojournal","-source","synth.tcl","-tclargs",str(checked)],
                             cwd=work,stdout=log,stderr=subprocess.STDOUT)
    lines = (work/"run.log").read_text(errors="replace").splitlines()
    if run.returncode:
        raise RuntimeError("\n".join(lines[-50:]))
    result = [line for line in lines if re.match(r"^(Vivado v|NATIVE8_)",line)]
    # A primitive count also includes LUTs which can share a physical LUT.
    utilization = (work/"native8_utilization.rpt").read_text()
    slice_luts = re.search(r"^\|\s*Slice LUTs\*?\s*\|\s*(\d+)\s*\|", utilization, re.MULTILINE)
    if not slice_luts:
        raise ValueError("missing Slice LUTs in the Vivado utilization report")
    lut_line = next(line for line in result if line.startswith("NATIVE8_LUT "))
    if int(lut_line.split()[1]) <= 0 or int(slice_luts[1]) <= 0:
        raise ValueError("expected positive LUT usage for the native8 controller")
    result.append("NATIVE8_SLICE_LUTS " + slice_luts[1])
    if reports:
        destination = reports/f"check_local_{checked}"
        destination.mkdir(parents=True, exist_ok=True)
        for name in ("native8_utilization.rpt", "native8_timing.rpt", "run.log"):
            shutil.copyfile(work/name, destination/name)
    print("\n".join(result))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["inject","timing","synth"])
    parser.add_argument("--rtl", type=Path, help="alternative RTL for the timing regression")
    parser.add_argument("--reports", type=Path, help="retain both sets of Vivado reports")
    args=parser.parse_args()
    if args.rtl and args.mode != "timing":
        parser.error("--rtl is only used for the timing regression")
    if args.reports and args.mode != "synth":
        parser.error("--reports is only used for synthesis")
    passed = True
    for checked in (0,1):
        print("CHECK_LOCAL =",checked,flush=True)
        with tempfile.TemporaryDirectory() as tmp:
            if args.mode == "timing":
                if not timing.run(Path(tmp), checked, args.rtl or HERE/"native8.sv"):
                    passed = False
            elif args.mode == "synth":
                synth(Path(tmp), checked, args.reports)
            else:
                inject(Path(tmp), checked)
    raise SystemExit(0 if passed else 1)
