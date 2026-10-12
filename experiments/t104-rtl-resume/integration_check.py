"""Multi-clock RTL against Python E and a separate full38 word oracle.

No RTL helpers are imported by the oracle. It sees actual pin writes, not a
simulator's requested final image. CSV-sized summaries only; raw traces in
ignored temporary storage. This is bounded verification, not hardware WCET.
"""
import argparse
import hashlib
import json
import random
import subprocess
import tempfile
import zlib
from pathlib import Path

from memory_oracle import MemoryOracle
from reference import ETransaction, Request, ServiceConfig
from rtl_check import packed

HERE = Path(__file__).resolve().parent
MODULES = ["e_backend", "absolute_calendar", "permission_gate", "service_config",
           "rpc_cdc", "app_frontend", "command_receiver", "executor_core", "executor"]


def command(sequence, issued, not_before, deadline, expires, corrupt=False):
    data = (104).to_bytes(4, "little") + (0x00104114).to_bytes(4, "little")
    for value in (sequence, issued, not_before, deadline, expires):
        data += value.to_bytes(8, "little")
    crc = zlib.crc32(data) ^ int(corrupt)
    return int.from_bytes(data + crc.to_bytes(4, "little"), "little")


def fixtures(scenario, words=8):
    rng = random.Random(104 + scenario)
    count = 64 if scenario == 0 else 12
    lines = []
    for j in range(count):
        time = 400+j*6000
        if scenario in (2, 3, 4) and j < (3 if scenario == 4 else 2):
            time = 400+j*100
        port = 0 if scenario == 4 and j < 3 else j%2
        lines.append(f"{time} {port} {1 if j%4==3 else 2} {rng.randrange(words)} "
                     f"{rng.randrange(1<<32):08x} {1+j%15} {j+1}")
    commands = []
    if scenario == 1:
        commands = [(2200, command(1, 2000, 2200, 2400, 12000)),
                    (9000, command(2, 8900, 9000, 9200, 14000, True)),
                    (15000, command(3, 14000, 17000, 17004, 21000)),
                    (25000, command(3, 24000, 25000, 25300, 29000)),  # replay
                    (32000, command(4, 31900, 32000, 32000, 35000))]  # late
    return "\n".join(lines)+"\n", "".join(f"{t} {c:x}\n" for t, c in commands), count


def core_error_vectors():
    def packet(kind=2, mask=15, word=0, identity=1, first=0, corrupt=False):
        raw = ((kind | mask<<4).to_bytes(4, "little") + word.to_bytes(4, "little")
               + (0xdeadbeef).to_bytes(4, "little") + identity.to_bytes(8, "little")
               + first.to_bytes(8, "little"))
        return int.from_bytes(raw + (zlib.crc32(raw)^int(corrupt)).to_bytes(4, "little"), "little")
    cases = [(1576, packet(identity=999, corrupt=True), 1),
             (2000, packet(identity=1, first=1800), 0),
             (9000, packet(identity=2, first=8900), 0),
             (13000, packet(identity=1, first=12900), 1),
             (14000, packet(identity=3, word=8, first=13900), 1),
             (15000, packet(identity=3, kind=0, first=14900), 1),
             (16000, packet(identity=3, mask=0, first=15900), 1)]
    return "".join(f"{t} {packet:x} {bad}\n" for t, packet, bad in cases)


def check_trace(path, scenario, expected_requests, words=8):
    mem = MemoryOracle(words)
    for i, word in enumerate(mem.words):
        word.data = 0x10000000+i
    mem.words[0].errors[32] = -1
    cfg = ServiceConfig(words=words)
    offered, accepted, captured, completed, consumed = {}, {}, {}, {}, set()
    queued = {}
    transaction = None
    transaction_number = 0
    flags = 0
    expected_slot = 0
    grants, intervals, response_times, request_cdc, command_cdc = [], [], [], [], []
    command_sent = {}
    cmd_results = []
    pending_write = None
    rows = 0
    final = None
    last_time = -4
    skipped = 0
    for line in path.read_text().splitlines():
        f = line.split()
        tag = f[0]
        if tag == "O":
            t, source, kind, word = float(f[1]), int(f[2]), int(f[3]), int(f[4])
            data, mask, identity = int(f[5], 16), int(f[6]), int(f[7])
            assert identity not in offered
            offered[identity] = (t, source, Request(kind, word, data, mask, identity))
        elif tag == "A":
            t, source, identity = float(f[1]), int(f[2]), int(f[3])
            assert identity in offered and identity not in accepted
            assert source == offered[identity][1] and t >= offered[identity][0]
            accepted[identity] = t
        elif tag == "D":
            t, source, payload = int(f[1]), int(f[2]), int(f[3], 16)
            raw = payload.to_bytes(32, "little")
            assert zlib.crc32(raw[:28]) == int.from_bytes(raw[28:], "little"), "app CRC"
            meta, word, data = (int.from_bytes(raw[i:i+4], "little") for i in (0, 4, 8))
            identity, first = int.from_bytes(raw[12:20], "little"), int.from_bytes(raw[20:28], "little")
            request = offered[identity][2]
            assert (meta, word, data) == (request.kind | request.byte_enable<<4, request.word, request.data)
            assert source not in queued and identity not in captured
            assert first <= offered[identity][0], "first VALID was timestamped late"
            assert offered[identity][0]-first <= 44, "unbounded Gray timestamp staleness"
            assert 0 <= t-accepted[identity] <= 16, "request CDC >4 core edges"
            request_cdc.append(t-accepted[identity])
            captured[identity] = (t, first)
            queued[source] = request
        elif tag == "I":
            t, word, bit = map(int, f[1:])
            mem.words[word].toggle(bit, t)
        elif tag == "W":
            t, word, alias = map(int, f[1:4])
            data, mask, resulting = int(f[4], 16), int(f[5]), int(f[6], 16)
            assert transaction is not None and word == transaction.request.word
            mem.write(t, alias, data, mask, transaction_number)
            assert mem.words[word].data == resulting
            pending_write = (t, alias, data, mask)
        elif tag == "C":
            t, payload = float(f[1]), int(f[2], 16)
            command_sent[payload & ((1<<384)-1)] = (t, payload)
        elif tag == "V":
            t, integrity, accepted_command = map(int, f[1:])
            cmd_results.append((t, integrity, accepted_command))
        elif tag == "K":
            pass  # Matching command-result checks below; not a memory completion.
        elif tag == "R":
            t, source, payload, take = float(f[1]), int(f[2]), int(f[3], 16), int(f[4])
            identity = payload & ((1<<64)-1)
            assert identity in completed and identity not in consumed
            end, data = completed[identity]
            assert payload>>96 == 0 and (payload>>64)&0xffffffff == data
            assert source == offered[identity][1] and t >= end
            if take:
                consumed.add(identity)
                response_times.append(t-offered[identity][0])
                if scenario != 3:
                    assert t-end <= 40, "response CDC >4 source edges"
        elif tag == "P":
            t, go, kind, owner, word = map(int, f[1:6])
            data, mask, dq, err = int(f[6], 16), int(f[7]), int(f[8], 16), int(f[9])
            pins, read_data, err_count = int(f[10], 16), int(f[11], 16), int(f[12])
            state, fault = int(f[13], 16), int(f[14])
            slot, sj, skip, reset, loss, cmd = map(int, f[15:21])
            cmd_data = int(f[21], 16)
            assert t == last_time+4
            last_time = t
            if cmd:
                sent, payload = command_sent[cmd_data]
                assert 0 <= t-sent <= 32, "complete command >8 memory edges"
                command_cdc.append(t-sent)
            if slot:
                assert sj == expected_slot and t == cfg.start(sj), "calendar shifted"
                assert not cfg.mandatory(sj) or not skip, "mandatory skipped"
                expected_slot += 1
                skipped += skip
                assert bool(go) == (not skip), "slot not dispatched at its own edge"
                if go:
                    assert kind == 0 and word == cfg.address(sj)
            if go:
                assert transaction is None, "overlapping global lock"
                if kind:
                    assert t % 1568 == 1312 and owner in queued
                    request = queued.pop(owner)
                    assert (kind, word, data, mask) == (request.kind, request.word, request.data, request.byte_enable)
                else:
                    assert slot and not skip
                    request = Request(0, word, 0, 15)
                transaction_number += 1
                transaction = ETransaction(request, t)
                mem.begin(transaction_number, word, t, ("control", "read32", "write32")[kind])
                grants.append((t, kind, word))
            if transaction is not None:
                age = t-transaction.start
                if age == 60:
                    oracle_data, oracle_err = mem.observe(t)
                    assert dq == oracle_data & 0xffff and bool(err) == oracle_err
                if age == 152 and transaction.request.kind == 1:
                    assert dq == mem.words[transaction.request.word].data >> 16
                expected = transaction.step(t, dq, err)
                expected_pins = packed(expected, int(bool(go)),
                    int(age == 60 and transaction.request.kind != 1 and bool(err)))
                assert pins == expected_pins, f"E mismatch at {t}: {pins:x}!={expected_pins:x}"
                assert read_data == expected["data"]
                flags += expected["flag"]
                if expected["commit"]:
                    assert pending_write is not None and pending_write[0] == t
                    pending_write = None
                if expected["done"]:
                    mem.release(t)
                    intervals.append((transaction.start, t))
                    if transaction.request.kind:
                        completed[transaction.request.request_id] = (t, read_data)
                    transaction = None
            else:
                assert pins & (0x1f | (0x1f << 24) | (1 << 30)) == 0, "activity without grant"
            assert err_count == flags, "lost or duplicate logical ERR"
            assert sum(((state>>s)&3)==2 for s in (0, 2)) <= 1
            rows += 1
        elif tag == "END":
            final = tuple(int(x, 16 if i >= 2 else 10) for i, x in enumerate(f[1:]))
        else:
            raise AssertionError(f"unknown trace tag {tag}")
    assert len(consumed) == len(offered) == expected_requests
    assert final is not None and final[2] == 0
    assert final[0] == transaction_number
    assert final[1] == (scenario in (2, 3, 4)), f"unexpected fault {final}"
    assert flags == len(mem.flags)
    if scenario == 1:
        assert [r[1:] for r in cmd_results] == [(1, 1), (0, 0), (1, 1), (1, 0), (1, 0)]
        assert skipped > 0
    if scenario in (0, 1):
        assert max(response_times)*1.00001*1.1 <= 3000
    return {"scenario": scenario, "word_count": words, "trace_edges": rows,
            "operations": transaction_number, "application_requests": len(consumed),
            "ERR_events": flags, "skips": skipped, "expected_fault": bool(final[1]),
            "request_CDC_ticks_max": max(request_cdc),
            "command_CDC_ticks_max": max(command_cdc, default=None),
            "first_VALID_to_consumption_ns_nominal_max": max(response_times),
            "traffic_inside_declared_envelope": scenario in (0, 1),
            "trace_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    build = HERE/".build"
    build.mkdir(exist_ok=True)
    results = []
    mutations = []
    with tempfile.TemporaryDirectory(prefix="integration-", dir=build) as td:
        temp = Path(td)
        sources = [str(HERE/"rtl"/(m+".sv")) for m in MODULES]
        subprocess.run(["iverilog", "-g2012", "-s", "tb_interfaces", "-o", str(temp/"interfaces.vvp"),
                        *sources, str(HERE/"rtl/tb_interfaces.sv")], check=True, capture_output=True, text=True)
        interfaces = subprocess.run(["vvp", str(temp/"interfaces.vvp")], capture_output=True, text=True, check=True)
        print(interfaces.stdout.strip(), flush=True)
        (temp/"core-errors.txt").write_text(core_error_vectors(), encoding="ascii")
        subprocess.run(["iverilog", "-g2012", "-s", "tb_core_errors", "-o", str(temp/"core-errors.vvp"),
                        *sources, str(HERE/"rtl/tb_core_errors.sv")], check=True, capture_output=True, text=True)
        core_errors = subprocess.run(["vvp", str(temp/"core-errors.vvp"), "+input=core-errors.txt"],
                                    cwd=temp, capture_output=True, text=True)
        if core_errors.returncode:
            raise RuntimeError(core_errors.stdout+core_errors.stderr)
        print(core_errors.stdout.strip(), flush=True)
        for clock_index, (cpu_half, x_half, phase) in enumerate([(5, 4, 1), (4, 5, 3)]):
            if args.quick and clock_index:
                break
            exe = temp/f"integrated-{clock_index}.vvp"
            subprocess.run(["iverilog", "-g2012", "-s", "tb_executor", "-o", str(exe),
                            f"-Ptb_executor.CPU_HALF={cpu_half}", f"-Ptb_executor.X_HALF={x_half}",
                            f"-Ptb_executor.CMD_PHASE={phase}", *sources,
                            str(HERE/"rtl/tb_executor.sv")], check=True, capture_output=True, text=True)
            for scenario in range(5):
                offers, commands, n = fixtures(scenario)
                (temp/"requests.txt").write_text(offers, encoding="ascii")
                (temp/"commands.txt").write_text(commands, encoding="ascii")
                duration = 400000 if scenario == 0 else 76000
                run = subprocess.run(["vvp", str(exe), "+input=requests.txt", "+commands=commands.txt",
                    "+output=trace.txt", f"+scenario={scenario}", f"+duration={duration}"],
                    cwd=temp, capture_output=True, text=True, timeout=90)
                if run.returncode:
                    raise RuntimeError(run.stdout+run.stderr)
                try:
                    result = check_trace(temp/"trace.txt", scenario, n)
                except Exception:
                    import shutil
                    shutil.copyfile(temp/"trace.txt", build/"last_integration_failure.txt")
                    raise
                result["clocks_ns"] = [4, 2*cpu_half, 2*x_half]
                results.append(result)
                print(json.dumps(result), flush=True)
        if not args.quick:
            for module, before, after, scenario, name in [
                ("e_backend", "if (soft_reset || cold_init) fault <= 1;",
                 "if (soft_reset) busy <= 0; if (soft_reset || cold_init) fault <= 1;", 2, "reset_cancels_pending"),
                ("rpc_cdc", "assign src_ready = request==credit_sync[2];",
                 "assign src_ready = 1'b1;", 4, "credit_released_before_reply")]:
                source = (HERE/"rtl"/(module+".sv")).read_text()
                assert source.count(before) == 1
                mutant = temp/(module+"_mutant.sv")
                mutant.write_text(source.replace(before, after))
                altered = [str(mutant) if Path(s).stem==module else s for s in sources]
                exe = temp/"mutant.vvp"
                subprocess.run(["iverilog", "-g2012", "-s", "tb_executor", "-o", str(exe),
                                *altered, str(HERE/"rtl/tb_executor.sv")], check=True, capture_output=True, text=True)
                offers, commands, n = fixtures(scenario)
                (temp/"requests.txt").write_text(offers)
                (temp/"commands.txt").write_text(commands)
                run = subprocess.run(["vvp", str(exe), "+input=requests.txt", "+commands=commands.txt",
                    "+output=mutant.txt", f"+scenario={scenario}", "+duration=76000"],
                    cwd=temp, capture_output=True, text=True, timeout=90)
                rejected = False
                reason = ""
                if run.returncode:
                    # A deliberate mutation can deadlock the bounded driver;
                    # never confuse compilation/tool failure with detection.
                    rejected = "driver still pending" in run.stdout
                    reason = "bounded driver still pending after deliberately cancelled operation"
                else:
                    try:
                        check_trace(temp/"mutant.txt", scenario, n)
                    except AssertionError as error:
                        rejected, reason = True, str(error) or "independent offer/operation/reply invariant mismatch"
                assert rejected, f"mutation survived: {name} {run.stdout} {run.stderr}"
                mutations.append({"mutation": name, "rejected": True, "reason": reason})
                print(f"MUTATION_REJECTED {name}: {reason}", flush=True)
    report = {"integrated_runs": results, "interface_guards": "passed", "core_error_guards": "passed",
              "mutations": mutations,
              "scope": "bounded multi-clock traces; conditional E; no physical CDC/STA proof"}
    if args.write:
        (HERE/"outputs/integration.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
