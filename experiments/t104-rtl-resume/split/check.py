"""First split checkpoint. Real XPM simulation is a separate optional step.

No stub claims: --vendor runs installed AMD simulation and checks every E pin
edge against the pre-existing Python reference, plus all accepted/replied IDs.
Generated products stay under ../.build; no vendor source is redistributed.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
from reference import ETransaction, Request


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(args, cwd, name, timeout=120):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    log = result.stdout + result.stderr
    (cwd / (name + ".log")).write_text(log, encoding="utf-8")
    return result.returncode, log


def decode_request(value):
    return Request(value & 3, (value >> 2) & ((1 << 19)-1),
                   (value >> 21) & 0xffffffff, (value >> 53) & 15, value >> 57)


def check_vendor_log(text):
    accepted, grants, releases, replies = [], [], [], []
    transactions, packets = {}, {}
    checks, nonzero_loss_edges = 0, 0
    accept_time, grant_time, release_time, reply_time = {}, {}, {}, {}
    for line in text.splitlines():
        fields = line.split()
        if not fields:
            continue
        event = fields[0]
        if event == "ACCEPT":
            packet = int(fields[2], 16)
            req = decode_request(packet)
            accepted.append(req.request_id)
            packets[req.request_id] = packet
            accept_time[req.request_id] = int(fields[1])
        elif event == "GRANT":
            packet = int(fields[2], 16)
            req = decode_request(packet)
            assert packet == packets[req.request_id], "cross-domain payload corruption"
            assert req.request_id not in transactions, "duplicate grant"
            grants.append(req.request_id)
            grant_time[req.request_id] = int(fields[1])
            transactions[req.request_id] = ETransaction(req, 0)
        elif event == "RELEASE":
            ident = int(fields[2])
            releases.append(ident)
            release_time[ident] = int(fields[1])
        elif event == "PIN":
            ident, age = int(fields[2]), int(fields[3])
            tr = transactions[ident]
            dq = 0xc3a5 if tr.request.kind == 1 and age == 152 else 0x5a3c
            expected = tr.step(age, dq, bool(ident & 1))
            keys = ("busy", "ce", "oe", "we", "drive", "alias", "be", "dout",
                    "sample", "flag", "done", "commit", "pending", "data")
            actual = [int(x, 16) for x in fields[4:18]]
            assert actual == [expected[k] for k in keys], (ident, age, actual, expected)
            assert int(fields[18], 16) == tr.request.word
            assert int(fields[19], 16) == int(age == 60 and tr.request.kind != 1 and ident & 1)
            nonzero_loss_edges += int(fields[20], 16)
            checks += 1
        elif event == "REPLY":
            value = int(fields[2], 16)
            ident = value >> 33
            req = decode_request(packets[ident])
            expected_data = 0xc3a55a3c if req.kind == 1 else 0x5a3c
            expected_err = int(req.kind != 1 and bool(ident & 1))
            assert value == (ident << 33) | (expected_data << 1) | expected_err
            assert ident in releases and int(fields[1]) >= release_time[ident]
            replies.append(ident)
            reply_time[ident] = int(fields[1])
    assert accepted == grants == releases == replies == list(range(360)), "loss/repeat/order"
    assert nonzero_loss_edges > 0, "loss-during-operation was not exercised"
    assert "PASS lane" in text
    assert "invalid=2" in text, "slow-domain malformed input refusal not tested"
    assert not re.search(r"\b(FATAL|ERROR):", text), "vendor or test assertion"
    return {"packets": len(accepted), "pin_edges_checked": checks,
            "operation_edges_with_slow_loss": nonzero_loss_edges,
            "max_accept_to_grant_ns_including_deliberate_out_of_contract_stall":
                max((grant_time[i]-accept_time[i])/1000 for i in accepted),
            "first_accept_to_grant_ns_empty_queue": (grant_time[0]-accept_time[0])/1000,
            "max_release_to_reply_ns": max((reply_time[i]-release_time[i])/1000 for i in accepted),
            "max_accept_to_reply_ns": max((reply_time[i]-accept_time[i])/1000 for i in accepted),
            "log_sha256": hashlib.sha256(text.encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vendor", action="store_true")
    parser.add_argument("--vivado", default="/home/z3tm4n/bin/vivado-wsl")
    parser.add_argument("--logs", nargs="*", type=Path, default=[])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    build = BASE / ".build" / ("split-check-" + str(time.time_ns()))
    build.mkdir(parents=True)
    report = {"base": "cc0ce6d7149dc8e69b4dd30c1603b7338ce9c47b",
              "scope": "components, not full executor or board closure", "calendar": [],
              "sources": {p.name: sha(p) for p in sorted(HERE.iterdir()) if p.suffix in (".sv", ".py", ".tcl")},
              "shared_reference_sha256": sha(BASE/"reference.py"),
              "shared_backend_sha256": sha(BASE/"rtl/e_backend.sv"), "vendor": []}
    for width in (3, 4, 19):
        exe = build / f"calendar-{width}"
        code, log = run(["iverilog", "-g2012", "-s", "tb_calendar",
                         f"-Ptb_calendar.WB={width}", "-o", str(exe),
                         str(HERE/"tb_calendar.sv"), str(HERE/"relative_calendar.sv"),
                         str(BASE/"rtl/absolute_calendar.sv")], build, f"compile-{width}")
        assert code == 0, log
        code, log = run(["vvp", str(exe)], build, f"calendar-{width}")
        assert code == 0 and "PASS relative_calendar" in log, log
        report["calendar"].append({"word_bits": width, "cycles": 120000, "matched": True})
    code, log = run(["iverilog", "-g2012", "-s", "tb_guard", "-o", str(build/"guard"),
                     str(HERE/"predecision_guard.sv"), str(HERE/"tb_guard.sv")], build, "guard-compile")
    assert code == 0, log
    code, log = run(["vvp", str(build/"guard")], build, "guard")
    assert code == 0 and "PASS guard" in log, log
    report["guard_generations_exercised"] = 65536
    script = (f'read_verilog -formal -sv "{HERE}/predecision_guard.sv" "{HERE}/formal_guard.sv"; '
              'prep -top formal_guard; flatten; async2sync; chformal -lower; '
              'sat -seq 1 -tempinduct -maxsteps 4 -set-def-inputs -prove-asserts -verify -timeout 30')
    code, log = run(["yosys", "-Q", "-T", "-p", script], build, "guard-induction")
    assert code == 0 and "Induction step proven: SUCCESS" in log, log[-3000:]
    report["guard_induction"] = {"assertions": 3, "status": "proved", "assumptions": "binary inputs and RTL initialization"}
    # Negative control: same-edge ERR is no longer a veto; induction must reject it.
    original = (HERE/"predecision_guard.sv").read_text()
    assert original.count("&& !err_event") == 1
    mutant = build/"guard-mutant.sv"
    mutant.write_text(original.replace("&& !err_event", ""))
    bad_script = script.replace(str(HERE/"predecision_guard.sv"), str(mutant))
    code, log = run(["yosys", "-Q", "-T", "-p", bad_script], build, "guard-mutant")
    assert code != 0 and "proof did fail" in log, log[-3000:]
    report["same_edge_mutant_rejected"] = True
    # Independent calendar sentinel: one fast cycle removed from the spacing.
    original = (HERE/"relative_calendar.sv").read_text()
    assert original.count("start_pos==7 ? 104 : 40") == 1
    mutant = build/"calendar-mutant.sv"
    mutant.write_text(original.replace("start_pos==7 ? 104 : 40", "start_pos==7 ? 104 : 39"))
    code, log = run(["iverilog", "-g2012", "-s", "tb_calendar", "-o", str(build/"bad-calendar"),
                     str(HERE/"tb_calendar.sv"), str(mutant), str(BASE/"rtl/absolute_calendar.sv")], build, "mutant-compile")
    assert code == 0, log
    code, log = run(["vvp", str(build/"bad-calendar")], build, "mutant-calendar")
    assert code != 0 and "mismatch" in log, log
    report["one_cycle_calendar_mutant_rejected"] = True
    for path in args.logs:
        report["vendor"].append(check_vendor_log(path.read_text()))
    if args.vendor:
        for phase, stress in ((0,1),(1,1),(3,1),(0,0),(1,0),(3,0)):
            project = build / f"xsim-{phase}-{stress}"
            code, log = run([args.vivado, "-mode", "batch", "-nojournal", "-nolog",
                             "-source", str(HERE/"xsim.tcl"), "-tclargs", str(phase), str(project), str(stress)],
                            build, f"vivado-{phase}-{stress}", timeout=360)
            assert code == 0, log[-6000:]
            result = check_vendor_log(log)
            result["phase_ns"] = phase
            result["stress"] = bool(stress)
            if not stress:
                assert result["max_accept_to_grant_ns_including_deliberate_out_of_contract_stall"] <= 152
                assert result["max_release_to_reply_ns"] <= 4+208+100
                assert result["max_accept_to_reply_ns"] <= 152+216+4+208+100
            report["vendor"].append(result)
    report["tools"] = {"yosys": subprocess.check_output(["yosys", "-V"], text=True).strip(),
                       "python": sys.version}
    report["local_build"] = str(build)
    assert report["sources"] == {name: sha(HERE/name) for name in report["sources"]}, "sources changed during verification"
    if args.write:
        (HERE/"checks.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
