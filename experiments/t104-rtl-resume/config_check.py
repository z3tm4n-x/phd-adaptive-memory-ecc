"""Configuration retiming: exact historical RTL miter + separate interface model.

Only equality is stored in production. The Python checker instead stores the
full last-written values. Build-only proof ports expose a representation
relation that is ASSERTED inductively, never assumed. No production port change.
"""
import argparse
import hashlib
import json
import os
import platform
import random
import re
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = "cd68afd309cc00a152dca51dd557b76991afdb13"
GOLD_PATH = "experiments/t104-rtl-resume/rtl/service_config.sv"
GOLD_HASH = "d30206ef6b70686811bb65abf81f5b769548c7f5ff5a0e261a7231e1a758f2c2"
SEED = 10420261008
PARAMETERS = [(w, pow(3, -1, 1 << w)) for w in range(3, 20)] + [(2, 3), (20, 699051), (19, 1)]


def git_command():
    command = ["git"]
    pointer = ROOT/".git"
    if os.name != "nt" and pointer.is_file():
        match = re.fullmatch(r"gitdir: ([A-Za-z]):[/\\](.+)\s*", pointer.read_text().strip())
        if match:
            directory = Path("/mnt")/match[1].lower()/match[2].replace("\\", "/")
            command += [f"--git-dir={directory}", f"--work-tree={ROOT}"]
    return command


def digest(data):
    return hashlib.sha256(data).hexdigest()


def golden_source():
    raw = subprocess.check_output([*git_command(), "show", f"{BASELINE}:{GOLD_PATH}"], cwd=ROOT)
    if digest(raw) != GOLD_HASH:
        raise ValueError("historical configuration RTL identity changed")
    return raw.decode("utf-8")


def expected_fields(bits):
    return [0x00104114, 1 << bits, 38, 3, 196, 164, 320, 8, 1312, 240, 208, 104]


class InterfaceModel:
    def __init__(self, bits, inverse):
        self.values = {}
        self.expected = dict(enumerate(expected_fields(bits)))
        self.parameters_ok = 3 <= bits <= 19 and 3*inverse % (1 << bits) == 1
        self.locked = self.fault = False

    def outputs(self, wr, commit, start_ok):
        compatible = self.parameters_ok and self.values == self.expected
        arm = commit and not wr and not self.locked and compatible and start_ok
        return int(arm) | (int(self.locked) << 1) | (int(self.fault) << 2) | (int(compatible) << 3)

    def step(self, wr, commit, start_ok, address, data):
        before = self.outputs(wr, commit, start_ok)
        if wr:
            if self.locked or address not in self.expected or commit:
                self.fault = True
            else:
                self.values[address] = data
        if commit:
            if before & 1:
                self.locked = True
            else:
                self.fault = True
        return before, self.outputs(wr, commit, start_ok)


def vectors(bits, inverse):
    inputs = [(0, 0, 0, 0, 0), (0, 1, 1, 0, 0)]
    values = expected_fields(bits)
    inputs += [(1, 0, 1, a, values[a]) for a in reversed(range(12))]
    # Correct -> every single-bit bad rewrite -> correct, while not locked.
    for address, value in enumerate(values):
        for bit in range(32):
            inputs += [(1, 0, 1, address, value ^ (1 << bit)),
                       (0, 0, 1, 0, 0), (1, 0, 1, address, value)]
    # wr+commit must reject the whole write, even with a complete good bank.
    inputs += [(1, 1, 1, a, 0) for a in range(16)]
    inputs.append((0, 1, 0, 0, 0))
    rng = random.Random(SEED + bits*100 + inverse)
    for _ in range(256):
        wr, commit = rng.randrange(2), rng.randrange(2)
        start_ok = rng.randrange(2) if wr or not commit else 0
        address = rng.randrange(16)
        data = values[address] if address < 12 and rng.randrange(2) else rng.getrandbits(32)
        inputs.append((wr, commit, start_ok, address, data))
    inputs += [(1, 0, 1, a, v) for a, v in enumerate(values)]
    inputs += [(0, 1, 1, 0, 0), (0, 1, 1, 0, 0), (0, 0, 1, 0, 0)]
    inputs += [(rng.randrange(2), rng.randrange(2), rng.randrange(2), rng.randrange(16), rng.getrandbits(32))
               for _ in range(128)]
    model = InterfaceModel(bits, inverse)
    rows = [" ".join(f"{v:x}" for v in (*row, *model.step(*row))) for row in inputs]
    return "\n".join(rows)+"\n", len(rows)


def proof_copy(source, gold):
    declaration = "output wire compatible\n"
    if source.count(declaration) != 1 or source.count("endmodule") != 1:
        raise ValueError("proof instrumentation target drifted")
    source = source.replace(declaration, "output wire compatible, output wire [11:0] proof_match\n")
    if gold:
        source = source.replace("module service_config", "module config_gold", 1)
        constants = ["32'h00104114", "(32'd1<<WORD_BITS)", "38", "3", "196", "164", "320", "8", "1312", "240", "208", "104"]
        monitor = "\n".join(f"assign proof_match[{i}]=written[{i}] && fields[{i}]=={c};" for i, c in enumerate(constants))
    else:
        monitor = "assign proof_match=field_match;"
    return source.replace("endmodule", monitor+"\nendmodule")


def simulate(source, bits, inverse, directory, should_fail=False):
    data, count = vectors(bits, inverse)
    (directory/"vectors.txt").write_text(data, encoding="ascii")
    (directory/"simulation.sv").write_text(source, encoding="utf-8")
    command = ["iverilog", "-g2012", "-s", "tb_config", "-o", "config.vvp",
               f"-Ptb_config.WORD_BITS={bits}", f"-Ptb_config.INVERSE={inverse}",
               "simulation.sv", str(HERE/"formal/tb_config.sv")]
    subprocess.run(command, cwd=directory, check=True, capture_output=True, timeout=30)
    run = subprocess.run(["vvp", "config.vvp", "+vectors=vectors.txt"], cwd=directory,
                         text=True, capture_output=True, timeout=30)
    if should_fail:
        if run.returncode == 0 or "CONFIG_MISMATCH" not in run.stdout:
            raise AssertionError("configuration mutant not detected")
        location = re.search(r"CONFIG_MISMATCH (pre|post) case=(\d+)", run.stdout)
        if not location:
            raise AssertionError("mutation rejection location missing")
        return {"vectors_available": count, "first_mismatch_case": int(location[2]),
                "edge_phase": location[1], "vector_sha256": digest(data.encode()), "mutant_rejected": True}
    elif run.returncode or f"T104_CONFIG_PASS cases={count}" not in run.stdout:
        raise AssertionError(run.stdout+run.stderr)
    return {"edges": count, "vector_sha256": digest(data.encode()), "mutant_rejected": should_fail}


def prove(bits, inverse, directory):
    script = (f'read_verilog -formal -sv gold.sv gate.sv "{HERE}/formal/config_equivalence.sv"; '
              f'chparam -set WORD_BITS {bits} -set INVERSE {inverse} config_equivalence; '
              'prep -top config_equivalence; flatten; memory_map; chformal -lower; opt_clean; '
              'sat -seq 1 -tempinduct -maxsteps 4 -set-def-inputs -prove-asserts -verify -timeout 30')
    run = subprocess.run(["yosys", "-Q", "-T", "-p", script], cwd=directory,
                         text=True, capture_output=True, timeout=60)
    (directory/"proof.log").write_text(run.stdout+run.stderr, encoding="utf-8")
    if run.returncode or "Induction step proven: SUCCESS" not in run.stdout:
        raise AssertionError((run.stdout+run.stderr)[-4000:])
    return {"status": "proved", "assertions": 16,
            "k": int(re.findall(r"\[induction step (\d+)\]", run.stdout)[-1]),
            "log_sha256": digest((run.stdout+run.stderr).encode())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    start = time.monotonic()
    gold = golden_source()
    source = (HERE/"rtl/service_config.sv").read_text(encoding="utf-8")
    directory = HERE/".build"/f"config-{time.time_ns()}"
    directory.mkdir(parents=True)
    (directory/"gold.sv").write_text(proof_copy(gold, True), encoding="utf-8")
    (directory/"gate.sv").write_text(proof_copy(source, False), encoding="utf-8")
    results = []
    for bits, inverse in PARAMETERS:
        case = directory/f"w{bits}-i{inverse}"
        case.mkdir()
        result = {"word_bits": bits, "inverse": inverse, **simulate(source, bits, inverse, case)}
        if args.formal:
            # Each proof retains its own sources/log rather than overwriting evidence.
            for name in ("gold.sv", "gate.sv"):
                (case/name).write_bytes((directory/name).read_bytes())
            result["induction"] = prove(bits, inverse, case)
        results.append(result)
        print(json.dumps(result), flush=True)
    mutants = {}
    for name, old, new in (("wr_commit", "commit && !wr &&", "commit &&"),
                          ("sticky_match", "field_match[2]<=data==38;", "field_match[2]<=field_match[2] || data==38;")):
        if source.count(old) != 1:
            raise ValueError("mutation target drifted")
        case = directory/name
        case.mkdir()
        mutants[name] = simulate(source.replace(old, new), 19, 174763, case, True)
    report = {"baseline_commit": BASELINE, "gold_sha256": GOLD_HASH,
              "production_sha256": digest((HERE/"rtl/service_config.sv").read_bytes()),
              "checker_sha256": digest(Path(__file__).read_bytes()), "seed": SEED,
              "harness_sha256": {name: digest((HERE/"formal"/name).read_bytes())
                                  for name in ("config_equivalence.sv", "tb_config.sv")},
              "tools": {"python": platform.python_version(),
                        "yosys": subprocess.check_output(["yosys", "-V"], text=True).strip() if args.formal else None,
                        "iverilog": subprocess.check_output(["iverilog", "-V"], stderr=subprocess.STDOUT, text=True).splitlines()[0]},
              "cases": results, "mutants": mutants, "elapsed_s": round(time.monotonic()-start, 3),
              "raw_directory": str(directory),
              "scope": "complete service_config interface under synchronous binary inputs; not whole executor",
              "shared_dependencies": ["Yosys SAT/translation", "Icarus", "declared constants"],
              "proof_relation": "last matching written value iff field_match; asserted, not assumed"}
    if args.write:
        if not args.formal:
            raise ValueError("published report requires formal checks")
        (HERE/"outputs/config_equivalence.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"cases": len(results), "mutants": mutants, "elapsed_s": report["elapsed_s"]}, indent=2))


if __name__ == "__main__":
    main()
