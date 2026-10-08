"""Generate bounded test vectors from E reference, run independent new RTL.

Requires iverilog/vvp in PATH or explicit executable paths. No old RTL imports.
Temporary vectors/build products are outside Git; deterministic summary only.
"""
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
from pathlib import Path

from reference import (Calendar, CONTROL, ETransaction, Permission, READ32,
                       Request, ServiceConfig, WRITE32)

HERE = Path(__file__).resolve().parent


def packed(p, accepted=0, err_due=0):
    value = 0
    for name, shift in [("busy", 0), ("ce", 1), ("oe", 2), ("we", 3), ("drive", 4),
                        ("alias", 5), ("be", 6), ("dout", 8), ("sample", 24),
                        ("flag", 25), ("done", 26), ("commit", 27), ("pending", 28)]:
        value |= p[name] << shift
    return value | ((1-p["busy"]) << 29) | (accepted << 30) | (err_due << 32)


def backend_vectors():
    rng = random.Random(104)
    cases = [(k, e, be, reset) for k in range(3) for e in (0, 1)
             for be in range(1, 16) for reset in (-1, 60, 64, 128, 148, 200)]
    cases += [(rng.randrange(3), rng.randrange(2), rng.randrange(1, 16), rng.randrange(55)*4)
              for _ in range(1000)]
    lines = []
    for index, (kind, err, be, reset) in enumerate(cases):
        # Qualified fresh fixture initialization, not an in-service reset.
        lines.append("1 0 0 0 0 0 f 0 0 200000c0 0 0 0")
        req = Request(kind, rng.randrange(1 << 19), rng.randrange(1 << 32), be, index)
        transaction = ETransaction(req, 0)
        for age in range(0, 220, 4):
            dq = rng.randrange(65536)
            # Deliberately change ERR around the latch; decision uses only age60.
            pin_err = err if age == 60 else rng.randrange(2)
            p = transaction.step(age, dq, pin_err)
            vals = [0, int(age == reset), int(age == 0 or (age > 0 and rng.random() < .3)),
                    req.kind if age == 0 else rng.randrange(4),
                    req.word if age == 0 else rng.randrange(1 << 19),
                    req.data if age == 0 else rng.randrange(1 << 32),
                    req.byte_enable if age == 0 else rng.randrange(16), dq, pin_err,
                    packed(p, int(age == 0), int(age == 60 and kind != READ32 and bool(err))),
                    p["data"], req.word, age]
            lines.append(" ".join(f"{v:x}" for v in vals))
            if p["done"]:
                break
    return "\n".join(lines)+"\n", len(cases), len(lines)


def calendar_vectors():
    rng = random.Random(104)
    c = ServiceConfig(words=8)
    ref = Calendar(c)
    ref.freeze(0, 0); ref.freeze(1, 0)
    next_start, next_freeze = 0, 2
    lines = []
    for t in range(0, 1568*256, 4):
        permit = rng.random() < .80
        alarm = t % 164 == 8 or rng.random() < .001
        reset = t % 1568 == 1248 or rng.random() < .001
        # An authorized producer, with deliberately synthetic LOW values.
        # This tests the execution interface, not a scientific controller.
        if permit:
            ref.recovered(t)
            permit = ref.command(Permission(104, t+1, t, t, t+4, t+8), t)
        else:
            ref.loss(t)
        if alarm or reset:
            ref.loss(t)
        is_freeze = t == c.start(next_freeze)-c.lead
        frozen = int(ref.freeze(next_freeze, t)) if is_freeze else 0
        fj = next_freeze
        if is_freeze:
            next_freeze += 1
        is_slot = t == c.start(next_start)
        sj = next_start
        execute, word = ref.start_slot(next_start, t) if is_slot else (False, 0)
        if is_slot:
            next_start += 1
        fields = [t, int(permit), int(alarm), int(reset), int(is_slot), int(execute),
                  int(is_slot and not execute), int(is_freeze), frozen,
                  int(t % 1568 == 1312), sj, fj, word]
        lines.append(" ".join(f"{v:x}" for v in fields))
    return "\n".join(lines)+"\n", len(lines)


def simulate(iverilog, vvp, temp, top, source, vectors):
    vector_path = temp / f"{top}.txt"
    vector_path.write_text(vectors, encoding="ascii")
    executable = temp / f"{top}.vvp"
    build = [iverilog, "-g2012", "-s", f"tb_{top}", "-o", str(executable),
             str(source), str(HERE/"rtl"/f"tb_{top}.sv")]
    compiled = subprocess.run(build, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError(compiled.stdout+compiled.stderr)
    # Keep HDL $fopen names ASCII: some Icarus versions cannot decode UTF-8
    # passed through a packed Verilog string (e.g. Windows user's home name).
    runtime = str(Path(vvp).resolve()) if Path(vvp).is_file() else vvp
    result = subprocess.run([runtime, str(executable), f"+vectors={vector_path.name}"],
                            cwd=temp, capture_output=True, text=True, timeout=90)
    return result


def permission_vectors():
    rng = random.Random(104)
    ref = Calendar(ServiceConfig(words=8))
    directed = {
        4: Permission(104, 1, 4, 20, 24, 40),
        24: Permission(104, 2, 24, 24, 24, 44),
        28: Permission(104, 3, 28, 28, 28, 44),
        36: Permission(104, 3, 24, 24, 48, 64),
        44: Permission(104, 3, 44, 44, 44, 64),
        56: Permission(104, 4, 56, 57, 58, 90),
        68: Permission(104, 4, 68, 68, 68, 100, False),
        76: Permission(104, 5, 76, 76, 76, 100),
    }
    lines = []
    for t in range(0, 20000, 4):
        late_shadow = ref.shadow is not None and t > ref.shadow.deadline
        err = t == 28 or (t > 100 and rng.random() < .003)
        reset = t == 48 or (t > 100 and rng.random() < .003)
        loss = t > 100 and rng.random() < .003
        recover = t in (32, 40, 52, 64, 72) or (
            t > 100 and not ref.healthy and not late_shadow and rng.random() < .5)
        recover = recover and not (err or reset or loss)
        ref.at(t)
        if err:
            ref.err(t)
        if reset or loss:
            ref.loss(t)
        if recover:
            ref.recovered(t)
        cmd = directed.get(t)
        if t > 100 and rng.random() < .035:
            nbf = t + rng.choice([0, 0, 8, 16])
            cmd = Permission(104 if rng.random() > .05 else 105,
                             ref.sequence + (0 if rng.random() < .05 else 1),
                             t if rng.random() > .05 else 0, nbf,
                             nbf + (4 if rng.random() > .05 else -4), nbf+24,
                             rng.random() > .05)
        accepted = ref.command(cmd, t) if cmd is not None else False
        cp = cmd or Permission(104, 0, 0, 0, 0, 0)
        fields = [t, int(reset), int(loss), int(err), int(recover), int(cmd is not None),
                  int(cp.integrity), cp.mission, 0x00104114, cp.sequence, cp.issued,
                  cp.not_before, cp.deadline, cp.expires,
                  int(ref.active is not None and ref.healthy), int(ref.active is not None),
                  int(ref.shadow is not None), int(ref.healthy), int(cmd is not None),
                  int(accepted), ref.err_count, ref.sequence]
        lines.append(" ".join(f"{x:x}" for x in fields))
    return "\n".join(lines)+"\n", len(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--iverilog", default="iverilog")
    p.add_argument("--vvp", default="vvp")
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    def version(executable):
        p = subprocess.run([executable, "-V"], capture_output=True, text=True, check=True)
        return (p.stdout or p.stderr).splitlines()[0]
    versions = {"iverilog": version(args.iverilog), "vvp": version(args.vvp)}
    v, n, rows = backend_vectors()
    c, calendar_rows = calendar_vectors()
    commands, permission_rows = permission_vectors()
    build_root = HERE / ".build"
    build_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="t104-rtl-", dir=build_root) as td:
        temp = Path(td)
        for top, source, text in (("backend", "e_backend.sv", v),
                                  ("calendar", "absolute_calendar.sv", c),
                                  ("permission", "permission_gate.sv", commands),
                                  ("guards", "absolute_calendar.sv", "")):
            result = simulate(args.iverilog, args.vvp, temp, top, HERE/"rtl"/source, text)
            if result.returncode:
                raise RuntimeError(result.stdout+result.stderr)
            print(result.stdout.strip())
        gray_exe = temp / "gray.vvp"
        modules = sorted(str(path) for path in (HERE/"rtl").glob("*.sv")
                         if not path.name.startswith("tb_"))
        compile_gray = subprocess.run([args.iverilog, "-g2012", "-s", "tb_gray", "-o", str(gray_exe),
                                       *modules, str(HERE/"rtl/tb_gray.sv")], capture_output=True, text=True)
        if compile_gray.returncode:
            raise RuntimeError(compile_gray.stdout+compile_gray.stderr)
        gray = subprocess.run([args.vvp, str(gray_exe)], check=True, capture_output=True,
                              text=True, timeout=30)
        if "T104_GRAY_PASS cases=185" not in gray.stdout:
            raise AssertionError("incomplete Gray boundary regression")
        print(gray.stdout.strip())
        spacing_exe = temp / "spacing.vvp"
        spacing_command = [args.iverilog, "-g2012", "-s", "tb_spacing", "-o", str(spacing_exe),
                           *modules, str(HERE/"formal/tb_spacing.sv")]
        subprocess.run(spacing_command, check=True, capture_output=True)
        spacing = subprocess.run([args.vvp, str(spacing_exe)], check=True, capture_output=True,
                                 text=True, timeout=30)
        if "T104_SPACING_PASS cases=163" not in spacing.stdout:
            raise AssertionError("incomplete real-core spacing regression")
        print(spacing.stdout.strip())
        original_core = str(HERE/"rtl/executor_core.sv")
        core_text = Path(original_core).read_text(encoding="utf-8")
        marker = "offer_overflow<=incoming[223:160]>64'hffffffffffffea7b;"
        if core_text.count(marker) != 1:
            raise AssertionError("overflow mutation target drifted")
        mutant_core = temp/"no_spacing_overflow.sv"
        mutant_core.write_text(core_text.replace(marker, "offer_overflow<=1'b0;"), encoding="utf-8")
        mutant_command = [str(mutant_core) if x == original_core else x for x in spacing_command]
        subprocess.run(mutant_command, check=True, capture_output=True)
        bad_spacing = subprocess.run([args.vvp, str(spacing_exe)], capture_output=True, text=True, timeout=30)
        if not bad_spacing.returncode or "spacing previous=" not in bad_spacing.stdout:
            raise AssertionError("discarded-overflow mutant survived")
        print("MUTATION_REJECTED: discarded spacing overflow")
        # Mechanical mutation in a temporary copy, never the committed source.
        source = (HERE/"rtl/e_backend.sv").read_text(encoding="utf-8")
        target = "op != READ32 && captured_err"
        assert source.count(target) == 2
        mutant = temp/"lost_app_ERR.sv"
        mutant.write_text(source.replace(target, "op == CONTROL && captured_err"), encoding="utf-8")
        bad = simulate(args.iverilog, args.vvp, temp, "backend", mutant, v)
        if not bad.returncode or "want" not in bad.stdout:
            raise AssertionError("lost-ERR mutation was not rejected for a trace mismatch")
        print("MUTATION_REJECTED: observed-write ERR deliberately dropped")
    summary = {"tools": versions, "backend_cases": n, "backend_edges": rows, "calendar_edges": calendar_rows,
               "permission_edges": permission_rows,
               "directed_guard_testbench_passed": True,
               "gray_carry_boundary_cases": 185,
               "actual_core_spacing_boundary_cases": 163,
               "spacing_overflow_mutation_rejected": True,
               "calendar_word_count": 8, "backend_vector_sha256": hashlib.sha256(v.encode()).hexdigest(),
               "calendar_vector_sha256": hashlib.sha256(c.encode()).hexdigest(),
               "permission_vector_sha256": hashlib.sha256(commands.encode()).hexdigest(),
               "lost_app_ERR_mutation_rejected": True,
               "scope": "component trace comparisons, not integrated full-W RTL proof/STA"}
    if args.write:
        (HERE/"outputs/rtl.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
