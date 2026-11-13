"""Run registered native8 register deposits in Icarus and score external SRAM pins."""
import argparse
import hashlib
import json
from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor
from itertools import pairwise
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "native-example-20261111"
CFG = json.loads((HERE / "config.json").read_bytes())
L = CFG["round_ns"]
TARGET = CFG["target_round"]
READS = CFG["read_offsets_ns"]
CLASSES = ("masked", "fast_return", "dangerous")
IDLE = (0, 0, 1, 1, 0, 0)


def expected_half(address):
    value = 0xA5BC3410 + 0x10001 * (address % 4)
    return (value >> (16 * (address // 4))) & 0xffff


def score(case, raw):
    buses, control, samples, writes, fault, mem = [], [], [], [], [], []
    origin = end = None
    observed = []
    for line in raw.splitlines():
        part = line.split()
        if not part or part[0] not in {"BUS","CTL","SAMPLE","WRITE","FAULT","MEM","ORIGIN","END"}:
            continue
        kind = part[0]
        observed.append(line)
        if kind == "FAULT":
            fault.append((int(part[1]), part[2], *map(int,part[3:])))
            continue
        row = tuple(map(int, part[1:]))
        if kind == "ORIGIN":
            origin, = row
        elif kind == "END":
            end = row
        else:
            {"BUS":buses,"CTL":control,"WRITE":writes,"SAMPLE":samples,"MEM":mem}[kind].append(row)
    t_end, successors, terminal_mask = end
    dirty = case["memory"] == "dirty"
    if origin != TARGET*L or mem != ([(2101,3,37)] if dirty else []):
        raise ValueError("missing physical origin or initial memory stimulus")
    before = case["expected_before"]
    bit = case["bit"]
    expect_fault = [] if case["register"] == "none" else [
        (case["offset_ns"],case["register"],bit,before,before ^ (1<<bit))]
    if fault != expect_fault:
        raise ValueError(f"wrong single deposit: {fault}")

    def value_at(rows, times, ns):
        return rows[bisect_right(times,ns)-1][1:]

    bus_times = [r[0] for r in buses]
    ctl_times = [r[0] for r in control]
    if not (bus_times[0] == ctl_times[0] == 0 and len(set(bus_times)) == len(buses)
            and bus_times == sorted(bus_times) and ctl_times == sorted(ctl_times)):
        raise ValueError("incomplete or unordered observations")
    starts = []
    old_read = None
    for ns, address, select, oe_n, we_n, drive, data in buses:
        addr = address if select and not oe_n and we_n and not drive else None
        if addr is not None and addr != old_read:
            starts.append((ns,addr))
        old_read = addr
    scans = [ns for ns,addr in starts if addr == 0]
    focus = (case["look_after_round"]-TARGET)*L
    next_two = [t for t in scans if t>focus][:2]
    if successors != len([t for t in scans if t>focus]) or len(next_two)<2:
        raise ValueError(f"censored successors at {t_end}: {next_two}")
    if not dirty and writes:
        raise ValueError("write without memory stimulus")
    # The independent service builds nominal edges from the external contract.
    # It never reads DUT.phase, hit, count, step, gap, or the injection target.
    nominal = {}
    for addr, launch in enumerate(READS):
        repair = dirty and addr == 7
        dq = expected_half(addr)
        nominal[launch] = (addr,1,0,1,0,0)
        nominal[launch+70] = (addr,1,1,1,0,0)
        if repair:
            for delay,we,drive in ((100,1,1),(110,0,1),(160,1,1),(180,1,0)):
                nominal[launch+delay] = (addr,1,1,we,drive,dq if drive else 0)
        nominal[launch+(200 if repair else 100)] = IDLE
    base_edges = sorted(nominal)
    first_service = None
    for ns in sorted(set(base_edges) | {x for x in bus_times if x < L}):
        want = nominal[base_edges[bisect_right(base_edges,ns)-1]]
        got = value_at(buses,bus_times,ns)
        if want != got:
            first_service = [ns,list(want),list(got)]
            break
    last_sample = next((r for r in samples if r[:2] == (2220,7)), None)
    if case["register"] == "none" and samples != [
            (ns+60, addr, int(dirty and addr==7), int(dirty and addr==7),
             expected_half(addr), expected_half(addr)) for addr, ns in enumerate(READS)]:
        raise ValueError("nominal sampled memory readback")
    first_writes = [list(row) for row in writes if row[0]<L]
    required_w = [[2320,7,expected_half(7),1<<37]] if dirty else []
    missed_repair = dirty and first_writes != required_w
    nominal_step = 1 if dirty else 2
    # Fast service can add scans. Promoting while still following the two-round
    # clean lattice is allowed only at the next threshold, outside this window.
    # Rebase each deadline on the most recent real scan and require the original
    # grid itself. A legitimate two-round gap must also retain the even phase.
    first_missed = None
    for cur,nxt in pairwise(scans):
        deadline = cur+nominal_step*L
        off_grid = cur % L != 0 or nxt % L != 0
        if nxt>deadline or off_grid or (nxt-cur==2*L and (cur//L)%2):
            first_missed = dict(due_ns=deadline, observed_ns=nxt, preceding_ns=cur, off_grid=off_grid)
            break
    if not first_missed and t_end>scans[-1]+nominal_step*L:
        first_missed = dict(due_ns=scans[-1]+nominal_step*L, observed_ns=None,
                            preceding_ns=scans[-1], off_grid=False)
    command_times = []
    for time_ns in scans:
        if time_ns+2700 <= t_end:
            installed = value_at(control,ctl_times,time_ns+2700)[-1]
            command_times.append((time_ns,installed))
    # A step change is counted as real service only once the SRAM is selected.
    fast_used = not dirty and any(b-a==L for a,b in pairwise(scans))
    if first_service or missed_repair or first_missed:
        label = "dangerous"
    elif fast_used:
        label = "fast_return"
    else:
        label = "masked"
    if case["register"] == "none":
        if first_service or first_missed or missed_repair or next_two != [nominal_step*L,2*nominal_step*L]:
            raise ValueError("invalid no-deposit twin")
        label = "control"

    port_read = port_write = 0
    horizon = CFG["price_window_rounds"]*L
    read_launch = None
    last_read = None
    for row,following in zip(buses,buses[1:]+[(t_end, *IDLE)]):
        ns, addr, sel, oe_n, we_n, drive, data = row
        if ns>=horizon:
            break
        current = addr if sel and not oe_n and we_n and not drive else None
        if current is not None and current!=last_read:
            read_launch=ns
        last_read=current
        if sel:
            duration=min(horizon, following[0])-ns
            read_len=min(duration,max(0,read_launch+100-ns))
            port_read+=read_len
            port_write+=duration-read_len
    pubs = [[t,row[1]] for (t,*row),prev in zip(control,[(0,0,0,0,0,0)]+control[:-1])
            if row[0] and not prev[1] and t<L]
    result = dict(outcome=label, deposit=fault[0] if fault else None, cut=list(value_at(control,ctl_times,2500)),
                  install=list(value_at(control,ctl_times,2700)), publications=pubs,
                  last_sample=list(last_sample) if last_sample else None,
                  repair_missed_by_2320_ns=missed_repair, writes_in_target=first_writes,
                  first_actual_repair=list(writes[0]) if writes else None,
                  memory_dirty_at_2320=bool(dirty and not any(w[0]<=2320 and w[3] for w in writes)),
                  first_service_difference=first_service, first_missed_scan=first_missed,
                  first_two_reads_ns=scans[1:3], first_two_after_focus_ns=next_two,
                  port_first_4_rounds_ns={"read":port_read,"write":port_write},
                  terminal_word3_mask=terminal_mask, end_ns=t_end,
                  trace_sha256=hashlib.sha256(("\n".join(observed)+"\n").encode()).hexdigest())
    if case["id"] in ("quiet_after","step_zero","hit_lost","timer_skip"):
        result["commands_near_decision"] = [list(pair) for pair in command_times
                                           if abs(pair[0]-focus)<=4*L or pair[0]<3*L]
    return result


def build(work):
    native = SOURCE / "native8.sv"
    src = native.read_bytes().replace(b"\r\n",b"\n")
    if hashlib.sha1(b"blob "+str(len(src)).encode()+b"\0"+src).hexdigest()!=CFG["rtl_blob"]:
        raise ValueError("RTL differs from the accepted source")
    for variant in CFG["check_local"]:
        subprocess.run(["iverilog","-g2012","-s","fault_tb",f"-Pfault_tb.CHECK_LOCAL={variant}",
                        "-o",work/f"sim{variant}",native,HERE/"fault_tb.sv"],check=True)


def run_one(work, variant, case):
    args = {"reg":case["register"],"bit":case["bit"],"at":case["offset_ns"],
            "before":case["expected_before"],"dirty":int(case["memory"]=="dirty"),
            "look":case["look_after_round"],"max_rounds":CFG["max_rounds"]}
    proc=subprocess.run(["vvp",work/f"sim{variant}",*(f"+{k}={v}" for k,v in args.items())],
                        capture_output=True,text=True)
    path=work/f"{variant}-{case['id']}.log"
    path.write_text(proc.stdout+proc.stderr)
    if proc.returncode:
        raise RuntimeError(f"{path}: {proc.stdout.splitlines()[-3:]} {proc.stderr}")
    return variant,case["id"],score(case,proc.stdout)


def execute(work,jobs):
    work.mkdir(parents=True,exist_ok=True)
    build(work)
    result={str(v):{} for v in CFG["check_local"]}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        tasks=[pool.submit(run_one,work,v,c) for v in CFG["check_local"] for c in CFG["cases"]]
        for job in tasks:
            variant,case,stat=job.result()
            result[str(variant)][case]=stat
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work",type=Path,required=True)
    parser.add_argument("--jobs",type=int,default=4)
    parser.add_argument("--check",action="store_true")
    args=parser.parse_args()
    result=execute(args.work.resolve(),args.jobs)
    path=args.work/"results.json"
    encoded=json.dumps(result,indent=2,sort_keys=True)+"\n"
    path.write_text(encoded)
    if args.check and encoded!=(HERE/"results.json").read_text():
        raise ValueError("replay differs")
    for variant,rows in result.items():
        print("CHECK_LOCAL",variant,*(f"{c}={sum(row['outcome']==c for row in rows.values())}"
              for c in (*CLASSES,"control")))
    print(path)


if __name__=="__main__":
    main()
