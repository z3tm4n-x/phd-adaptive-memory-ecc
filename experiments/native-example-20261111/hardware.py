"""Run reduced native8 fault scenarios or vendor synthesis, in a fresh work dir."""
import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def inject(work, checked):
    sim = work/"sim"
    subprocess.run(["iverilog","-g2012","-s","inject_tb",f"-Pinject_tb.CHECK_LOCAL={checked}","-o",sim,
                    HERE/"native8.sv", HERE/"inject_tb.sv"],check=True)
    for scenario in range(9):
        out = subprocess.check_output(["vvp",sim,f"+case={scenario}"],text=True)
        print(next(line for line in out.splitlines() if line.startswith("case=")),flush=True)


def synth(work, checked):
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
    lut = next(line for line in result if line.startswith("NATIVE8_LUT "))
    assert int(lut.split()[1])>0
    print("\n".join(result))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["inject","synth"])
    args=parser.parse_args()
    for checked in (0,1):
        print("CHECK_LOCAL =",checked,flush=True)
        with tempfile.TemporaryDirectory() as tmp:
            (inject if args.mode=="inject" else synth)(Path(tmp), checked)
