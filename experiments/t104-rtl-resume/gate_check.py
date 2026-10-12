"""Full-width pre-edge/next-state equivalence to the immutable 3a3656b gate.

No environment assumptions. All state equality is asserted, not assumed.
Simulation also injects equal arbitrary states (not a reachability claim),
so wrap/overflow need not wait 2**64 events. Existing reachable traces remain.
"""
import argparse
import hashlib
import itertools
import json
import platform
import random
import re
import subprocess
import time
from pathlib import Path

from config_check import git_command

HERE = Path(__file__).resolve().parent
BASE = "3a3656bdf09b7e99fd5f1de2baabb1b55e6a905d"
GOLD_PATH = "experiments/t104-rtl-resume/rtl/permission_gate.sv"
GOLD_HASH = "d546a95f8a35ad1e64cebae901bb65db9f73f333305d09da6bdfd73b0d41dec2"
SEED = 10420261009
INPUTS = [(n, 1) for n in ("cold_init", "soft_reset", "loss", "err_event", "recover")]
INPUTS += [("now", 64), ("cmd_valid", 1), ("cmd_integrity", 1),
           ("cmd_mission", 32), ("cmd_config", 32)]
INPUTS += [("cmd_"+n, 64) for n in ("sequence", "issued", "not_before", "deadline", "expires")]
STATE = [(n, 1) for n in ("command_ack", "command_accepted", "active", "shadow", "healthy", "overflow", "begun", "revoked_valid")]
STATE += [(n, 64) for n in ("err_count", "last_sequence", "revoked", "active_expires",
                          "shadow_not_before", "shadow_deadline", "shadow_expires", "shadow_issued")]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pack(fields, values):
    result = 0
    for name, width in fields:
        v = values.get(name, 0)
        if not 0 <= v < 1 << width:
            raise ValueError(name)
        result = (result << width) | v
    return result


def proof_copy(source, old=False):
    marker = "output reg [63:0] err_count, last_sequence\n"
    if source.count(marker) != 1 or source.count("endmodule") != 1:
        raise ValueError("gate instrumentation target drifted")
    source = source.replace(marker, marker.rstrip()+", output wire [519:0] proof_state\n")
    if old:
        source = source.replace("module permission_gate", "module gate_gold", 1)
    return source.replace("endmodule", "assign proof_state={"+",".join(n for n, _ in STATE)+"};\nendmodule")


def harness(simulation=False):
    decl = lambda n, w: (f"[{w-1}:0] " if w > 1 else "")+n
    common = ",".join("."+n+"("+n+")" for n, _ in INPUTS)
    instances = "\n".join(f"{typ} {name}(.clk(clk),{common},.permit_at_edge({name}_permit),.proof_state({name}_state));"
                          for typ, name in (("gate_gold", "gold"), ("permission_gate", "dut")))
    outputs = "wire [519:0] gold_state,dut_state; wire gold_permit,dut_permit;\n"
    if not simulation:
        ports = ",".join("input wire "+decl(n, w) for n, w in INPUTS)
        return ("module gate_equivalence(input wire clk,"+ports+");\n"+outputs+instances+
                "\nalways @* begin assert(gold_state==dut_state); assert(gold_permit==dut_permit); end\nendmodule\n")
    regs = "\n".join("reg "+decl(n, w)+";" for n, w in INPUTS)
    state = lambda name: "{"+",".join(name+"."+n for n, _ in STATE)+"}"
    return ("module tb_gate_equivalence; reg clk=0;\n"+regs+"\n"+outputs+instances+"\n"+
            "integer file,rc,i=0; reg [519:0] injected; reg [454:0] inputs;\n"
            "initial begin file=$fopen(\"vectors.txt\",\"r\"); if(!file) $fatal(1,\"no vectors\");\n"
            "while(!$feof(file)) begin rc=$fscanf(file,\"%h %h\\n\",injected,inputs);\n"
            "if(rc==2) begin clk=0; "+state("gold")+"=injected; "+state("dut")+"=injected;\n"
            "{"+",".join(n for n, _ in INPUTS)+"}=inputs; #1;\n"
            "if(gold_state!==dut_state || gold_permit!==dut_permit) $fatal(1,\"GATE_MISMATCH pre case=%0d\",i);\n"
            "clk=1; #1; if(gold_state!==dut_state || gold_permit!==dut_permit) $fatal(1,\"GATE_MISMATCH post case=%0d\",i);\n"
            "i=i+1; end end $display(\"GATE_EQ_PASS cases=%0d\",i); $finish; end endmodule\n")


def vectors():
    rows = []
    # All alarm/recover/command coincidences, deadline +/-1, cold-start,
    # expired/active/shadow, high counters, sequence equality and revocation.
    for flags in itertools.product((0, 1), repeat=7):
        for edge in (-1, 0, 1):
            s = dict(begun=flags[0], active=1, healthy=1, shadow=flags[1],
                     active_expires=100, shadow_not_before=20, shadow_deadline=24,
                     shadow_expires=100, shadow_issued=1, err_count=(1 << 64)-1)
            i = dict(now=24+edge, cold_init=flags[2], soft_reset=flags[3], loss=flags[4],
                     err_event=flags[5], recover=flags[6], cmd_valid=1, cmd_integrity=1,
                     cmd_mission=104, cmd_config=0x00104114, cmd_sequence=1,
                     cmd_issued=1, cmd_not_before=24, cmd_deadline=24, cmd_expires=100)
            rows.append((s, i))
    rng = random.Random(SEED)
    for j in range(6000):
        s = {n: rng.getrandbits(w) for n, w in STATE}
        i = {n: rng.getrandbits(w) for n, w in INPUTS}
        if j % 2 == 0:
            # Avoid an overwhelmingly always-invalid random command sample.
            t = rng.randrange(1, 1 << 63)
            s.update(healthy=1, overflow=0, revoked_valid=j % 3 == 0, revoked=t-1,
                     last_sequence=j, active_expires=t+10, shadow_not_before=t-1,
                     shadow_deadline=t+1, shadow_expires=t+5, shadow_issued=t)
            i.update(now=t, cmd_mission=104, cmd_config=0x00104114, cmd_integrity=1,
                     cmd_sequence=j+1, cmd_issued=t, cmd_not_before=t, cmd_deadline=t,
                     cmd_expires=t+1, cold_init=0, soft_reset=0, loss=0, err_event=0)
            # Boundaries in each independent payload condition.
            targets = ("cmd_sequence", "cmd_issued", "cmd_not_before", "cmd_deadline", "cmd_expires")
            target = targets[(j//2) % len(targets)]
            i[target] = max(0, i[target]+rng.choice((-1, 0, 1)))
        rows.append((s, i))
    return "".join(f"{pack(STATE, s):x} {pack(INPUTS, i):x}\n" for s, i in rows), len(rows)


def prove(directory):
    script = ('read_verilog -formal -sv gold.sv gate.sv proof.sv; prep -top gate_equivalence; '
              'flatten; memory_map; chformal -lower; opt_clean; '
              'sat -seq 1 -tempinduct -maxsteps 4 -set-def-inputs -prove-asserts -verify -timeout 60')
    run = subprocess.run(["yosys", "-Q", "-T", "-p", script], cwd=directory, text=True,
                         capture_output=True, timeout=120)
    raw = run.stdout+run.stderr
    (directory/"proof.log").write_text(raw, encoding="utf-8")
    if run.returncode or "Induction step proven: SUCCESS" not in raw:
        raise AssertionError(raw[-5000:])
    return {"status": "proved", "k": int(re.findall(r"\[induction step (\d+)\]", raw)[-1]),
            "assertions": 2, "state_bits": 520, "input_bits_excluding_clock": 455,
            "assumptions": 0, "log_sha256": digest(raw.encode())}


def simulate(directory, count, reject=False):
    subprocess.run(["iverilog", "-g2012", "-s", "tb_gate_equivalence", "-o", "test.vvp",
                    "gold.sv", "gate.sv", "tb.sv"], cwd=directory, check=True, capture_output=True)
    run = subprocess.run(["vvp", "test.vvp"], cwd=directory, text=True, capture_output=True, timeout=30)
    if reject:
        match = re.search(r"GATE_MISMATCH (pre|post) case=(\d+)", run.stdout)
        if run.returncode == 0 or not match:
            raise AssertionError("mutant survived or unrelated failure: "+run.stdout+run.stderr)
        return {"rejected": True, "phase": match[1], "first_case": int(match[2])}
    if run.returncode or f"GATE_EQ_PASS cases={count}" not in run.stdout:
        raise AssertionError(run.stdout+run.stderr)
    return {"cases": count, "phases": ["pre-edge", "post-edge"]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--formal", action="store_true")
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    start = time.monotonic()
    raw = subprocess.check_output([*git_command(), "show", f"{BASE}:{GOLD_PATH}"], cwd=HERE.parents[1])
    if digest(raw) != GOLD_HASH:
        raise ValueError("historical gate identity mismatch")
    gold = proof_copy(raw.decode(), True)
    production = (HERE/"rtl/permission_gate.sv").read_bytes()
    new = proof_copy(production.decode())
    data, count = vectors()
    directory = HERE/".build"/f"gate-equivalence-{time.time_ns()}"
    directory.mkdir(parents=True)
    for name, content in {"gold.sv": gold, "gate.sv": new, "proof.sv": harness(),
                          "tb.sv": harness(True), "vectors.txt": data}.items():
        (directory/name).write_text(content, encoding="utf-8")
    result = {"baseline_commit": BASE, "gold_sha256": GOLD_HASH, "production_sha256": digest(production),
              "checker_sha256": digest(Path(__file__).read_bytes()), "seed": SEED,
              "simulation": simulate(directory, count), "vector_sha256": digest(data.encode())}
    if args.formal:
        result["induction"] = prove(directory)
    result["mutants"] = {}
    for name, old, changed in (("removed_same_edge_veto", "assign permit_at_edge = !alarm_now &&", "assign permit_at_edge ="),
                               ("late_deadline", "now <= cmd_deadline;", "now < cmd_deadline;"),
                               ("recover_overrides_alarm_state", "if (alarm_now || command_blocked || shadow_late)",
                                "if ((alarm_now && !recover) || command_blocked || shadow_late)")):
        if new.count(old) != 1:
            raise ValueError("mutation target drifted")
        mutant = directory/name
        mutant.mkdir()
        for file in ("gold.sv", "tb.sv", "vectors.txt"):
            (mutant/file).write_bytes((directory/file).read_bytes())
        (mutant/"gate.sv").write_text(new.replace(old, changed), encoding="utf-8")
        result["mutants"][name] = simulate(mutant, count, True)
    result.update(elapsed_s=round(time.monotonic()-start, 3), raw_directory=str(directory),
                  tools={"python": platform.python_version(),
                         "yosys": subprocess.check_output(["yosys", "-V"], text=True).strip() if args.formal else None},
                  scope="binary synchronous gate equivalence; no new timing/clock assumptions; not full-system proof",
                  common_dependencies=["Yosys translation/SAT", "Icarus", "build-only port instrumentation"])
    if args.write:
        if not args.formal:
            raise ValueError("publication requires formal")
        (HERE/"outputs/gate_equivalence.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
