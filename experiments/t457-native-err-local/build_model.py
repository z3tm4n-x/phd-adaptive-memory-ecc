"""Build the model using only published source; never link the private generator."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
RULE = EXP / "t186-advisor-ge30-20261110/replay.c"
CAL = EXP / "t186-native-ge30-x16/calendar.json"
CERT = EXP / "t196-native-err-20261110/result.json"
BANK = EXP / "t104-rtl-resume/memory_oracle.py"
PINS = {
    RULE: "86c954381d84d7f19afc18ee9b4c502c91486344b2942b974876c5cb358ff6db",
    BANK: "9465ea3bcc57e2856b29edefd64ce470d54fef9223718258547a0efd7d75ad8f",
    CAL: "315fc36b793b232576f0075272cd6eda755700519c0dea04d7d2a9a5ab671849",
    CERT: "4c494cfbd0602a9e4256c46b0481fb0975466a322ee3cad5d5c9eed3f5438276",
}

def verify_inputs():
    for path, pin in PINS.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == pin, path
    cal = json.loads(CAL.read_text())
    assert cal["tick_ns"] == 10 and cal["frame_ns"] == 1400
    assert cal["visit_offsets_ns"] == [0,240,520,760]
    assert list(cal["operation_ns"].values()) == [0,60,70,100,110,160,180,200]
    assert (cal["report_cut_ns_before_next_pass"],cal["command_install_ns"]) == (300,200)
    assert cal["management_ns"] == [1260,1300] and cal["application_ns"] == [1020,1260]

def build(tmp):
    verify_inputs()
    src=RULE.read_text(encoding="utf8")
    def section(a,b):
        return src[src.index(a):src.index(b,src.index(a))]
    # Verbatim subranges: enums/structs, ceil_pos, registered_cells and choose.
    header=(section("typedef int64_t Tick;", "static Tick earlier(")
            +section("static Tick ceil_pos(", "static Tick offset(")
            +section("static int registered_cells(", "static void watch("))
    (tmp/"frozen_rule.h").write_text(header, encoding="utf8")
    shutil.copyfile(HERE/"policy_vpi.c",tmp/"policy_vpi.c")
    # Use the installed public VPI headers. Some distro wrappers split a
    # version-bearing build flag into an extra, nonexistent source '0-3'.
    include=os.environ.get("VPI_INCLUDE","/usr/include/iverilog")
    subprocess.run(["cc","-std=gnu11","-O2","-fPIC","-shared","-I",include,
                    "-o","policy_vpi.vpi","policy_vpi.c"],cwd=tmp,check=True)
    subprocess.run(["iverilog","-g2012","-Wall","-s","tb","-o",str(tmp/"sim"),
                    str(HERE/"native.sv"),str(HERE/"tb.sv")],cwd=tmp,check=True)

def run(tmp,case,end,mixed=False,literal=False):
    path=tmp/f"case-{case}-{int(mixed)}-{int(literal)}.trace"
    with path.open("w", encoding="ascii") as out:
        subprocess.run(["vvp","-M",str(tmp),"-mpolicy_vpi",str(tmp/"sim"),
                        f"+case={case}",f"+end={end}",f"+mixed={int(mixed)}",
                        f"+literal={int(literal)}"],stdout=out,check=True)
    return path
