"""Directed implementation checks, not an independent scientific review."""
from copy import deepcopy
from fractions import Fraction
import importlib.util
import random
from pathlib import Path
import sys
from model import Grid, Rule, run, resource_checks


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate(cfg, repo):
    checks = []
    def ok(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    ref = load_module("t186_accepted_service", repo/"experiments/t104-rtl-resume/reference.py")
    mem = load_module("t186_accepted_memory", repo/"experiments/t104-rtl-resume/memory_oracle.py")
    oracle = load_module("t186_accepted_rule", repo/"experiments/t105-arm-rule/oracle.py")
    grid = Grid(cfg["words"])
    accepted_grid = ref.ServiceConfig().validate()
    slots = [0,1,7,8,23,24,524287,524288,524289,2000000000]
    ok("absolute calendar and permutation match accepted B",
       all(grid.start(j)==accepted_grid.start(j) and grid.address(j)==accepted_grid.address(j)
           and grid.eligible(j, True)==accepted_grid.mandatory(j) for j in slots))
    rng = random.Random(186)
    for k in range(80):
        a = rng.choice([0,524280,2000000000])+rng.randrange(30)
        b = a+rng.randrange(1,120)
        low = bool(k%2)
        t = grid.start(a)+rng.randrange((b-a)*196+150)
        expected = sum(max(0,min(92,t-grid.start(j))) for j in range(a,b) if grid.eligible(j,low))
        if grid.work(a,b,low,t)!=expected:
            raise AssertionError(("integral",a,b,t,low,expected,grid.work(a,b,low,t)))
        if grid.count(a,b,low)!=sum(grid.eligible(j,low) for j in range(a,b)):
            raise AssertionError("eligible count")
    ok("80 pulse integrals and counts match literal sums including warmup/partial",True)
    ok("first-slot inversion brackets exact starts", all(
        grid.first(grid.start(j))==j and grid.first(grid.start(j)+1)==j+1 for j in slots))

    rule = Rule(cfg["policy"])
    accepted = oracle.Oracle()
    accepted.apply((0,0,0,1,0))
    tick=cfg["policy"]["timer_tick_ns"]
    initial_deadline=cfg["policy"]["NR"]*tick
    ok("startup full recovery hold and equality FAST",
       not rule.low(initial_deadline) and rule.low(initial_deadline+tick))
    # Each source/processing time is aligned to the source/timer clocks.
    for generation,(source,processing) in enumerate([
        (181000000064,181000100000),
        (181020000064,181020100000),
        (390000000064,390000100000)
    ],1):
        rule.publish()
        ok(f"local unprocessed veto {generation}",not rule.low(processing))
        rule.process(processing,source)
        snap=accepted.apply((processing//20,generation,source//4,2|4,0))
        ok(f"two-stage deadlines agree with independent accepted Oracle {generation}",
           max(0,rule.short-processing)==snap[3]*20 and
           max(0,rule.long-processing)==snap[4]*20 and
           rule.last_source==snap[2]*4)
    ok("pair extends long hold",rule.long>0)
    ok("different words use permutation without phase reset",
       grid.address(524288)==grid.address(0) and grid.address(3)==1)

    # Small stand tests scale timers ONLY for addressed code checks. These are
    # not pilot/comparison rows, nor another run of accepted U/E probability.
    small=deepcopy(cfg)
    small["words"]=8
    small["horizon_ns"]=25000
    small["application_reads"]=[dict(arrival_ns=8000,word=4)]
    small["policy"].update(NW=10,NH=20,NR=10,cut_ns=80,pair_source_ticks=100)
    small["injections"]=[
        dict(t=1,word=0,bit=0),   # during operation; retained at E commit
        dict(t=70,word=0,bit=1),  # after snapshot, before commit => first hit
        dict(t=90,word=0,bit=1),  # XOR cancellation cannot erase A_T
        dict(t=2000,word=1,bit=2),
        dict(t=2100,word=2,bit=3)]
    for method in cfg["methods"]:
        sparse=run(small,method)
        literal=run(small,method,literal=True)
        ok(method+": sparse and literal equality",
           {k:v for k,v in sparse.items() if k!="simulator_work"}==
           {k:v for k,v in literal.items() if k!="simulator_work"})
        ok(method+": first exceedance survives XOR and repair",
           sparse["first_exceedance"]["t"]==70 and sparse["bus_after_first_exceedance"]["total_ns"]>0)
    p=run(small,"our_err_r4")
    ok("post-start residual remains on first E commit",
       next(x for x in p["trace"] if x["event"]=="commit")["remaining"]==[0])

    # Independent birth-labelled accepted memory directly sees the same E.
    mo=mem.MemoryOracle(8)
    mo.begin(1,0,0,"control")
    mo.words[0].toggle(0,1)
    mo.observe(60)
    mo.words[0].toggle(1,70)
    mo.words[0].toggle(1,90)
    mo.write(132,0,0,transaction_id=1)
    mo.release(148)
    ok("post-start preserving E agrees with accepted memory oracle",
       mo.words[0].errors=={0:1} and mo.words[0].first_exceedance==70)
    tx=ref.ETransaction(ref.Request(ref.CONTROL,0),0)
    pins=[]
    for t in range(0,149,4):
        pins.append((t,tx.step(t,dq=0,err=t==60)))
    ok("sample/ERR/commit/release agree with accepted E pin schedule",
       [t for t,v in pins if v["sample"]]==[60] and
       [t for t,v in pins if v["flag"]]==[64] and
       [t for t,v in pins if v["commit"]]==[132] and
       [t for t,v in pins if v["done"]]==[148])
    clean=deepcopy(small)
    clean["injections"]=[dict(t=70,word=0,bit=5)]
    clean["horizon_ns"]=100
    clean["application_reads"]=[]
    c=run(clean,"constant_fast")
    ok("clean latch causes no write; late error survives",
       c["residual_errors"]=={"0":{"5":70}} and not c["err_events"])
    clean["injections"]=[dict(t=50,word=0,bit=5)]
    c=run(clean,"constant_fast")
    ok("partial corrective operation charges only in-horizon tail",
       c["bus"]["control_base_ns"]==92 and c["bus"]["correction_extra_ns"]==8 and
       c["unfinished_operations"][0]["end_ns"]==148)
    tail=deepcopy(clean)
    tail["injections"]=[]
    tail["horizon_ns"]=46
    t=run(tail,"constant_fast")
    ok("clean partial final operation is charged",
       t["bus"]["total_ns"]==46 and t["completed_control_operations"]==0 and
       t["unfinished_operations"][0]["end_ns"] is None)
    final=deepcopy(small)
    final["injections"]=[]
    final["application_reads"]=[]
    final["horizon_ns"]=164
    f=run(final,"constant_fast")
    ok("zero-time start at T is not charged",f["started_control_operations"]==1 and f["bus"]["total_ns"]==92)

    a=deepcopy(small)
    a["horizon_ns"]=20000
    b=deepcopy(a)
    b["injections"].append(dict(t=21000,word=7,bit=7))
    ok("future suffix cannot alter prefix decisions or prices",
       {k:v for k,v in run(a,"our_err_r4").items() if k!="simulator_work"}==
       {k:v for k,v in run(b,"our_err_r4").items() if k!="simulator_work"})
    b=deepcopy(a)
    b["injections"].append(dict(t=19000,word=7,bit=7))
    ra,rb=run(a,"our_err_r4"),run(b,"our_err_r4")
    ok("new later mark preserves earlier observed trace",
       [x for x in ra["trace"] if x["t"]<19000]==
       [x for x in rb["trace"] if x["t"]<19000])

    # Explicit freeze-boundary difference from illegal start-time scheduling.
    # Early timers permit LOW by 480ns; slot 3 starts492 but freezes172.
    edge=deepcopy(small)
    edge["injections"]=[]
    edge["application_reads"]=[]
    edge["horizon_ns"]=8000
    edge["policy"].update(NR=1,NW=1,NH=2,cut_ns=80)
    r=run(edge,"our_err_r4")
    mode=r["mode_history"][1]["t_ns"]
    first_effective=Grid(8).first(mode+320)
    ok("new LOW begins only at the first freeze-qualified slot",
       r["effective_segments"][0]["end_slot"]==first_effective)
    ok("freeze lead is not silently dropped",first_effective>Grid(8).first(mode))
    edge["injections"]=[dict(t=1700,word=3,bit=1)]
    edge["policy"].update(NW=100,NH=200)
    r=run(edge,"our_err_r4")
    veto=next(x["t_ns"] for x in r["mode_history"] if x["t_ns"]>80 and not x["low"])
    ok("ERR after freeze preserves already committed skip",
       veto==1796 and any(s["low"] and s["first_slot"]<=11<s["end_slot"] for s in r["effective_segments"]))
    ok("ERR veto forces next unfrozen optional slot FAST",
       any(not s["low"] and s["first_slot"]<=13<s["end_slot"] for s in r["effective_segments"]))
    partial=deepcopy(small)
    partial["injections"]=[]
    partial["application_reads"]=[dict(arrival_ns=0,word=4)]
    partial["horizon_ns"]=1342
    result=run(partial,"constant_fast")
    ok("application partial before snapshot is charged",result["bus"]["application_read_ns"]==30)
    partial["horizon_ns"]=1312
    result=run(partial,"constant_fast")
    ok("application starting at T is excluded",result["started_application_operations"]==0)
    res=resource_checks(cfg)
    for flag in ("pass_peak","pass_service_reserve","pass_response","pass_app_envelope"):
        ok(flag,res[flag])
    return dict(status="PASS",checks=len(checks),items=checks,
                scope="directed implementation checks; accepted code reused read-only; not new scientific review")


def check_pilot_results(cfg, results, repo):
    """Independent accepted 24-residue integral, not model.Grid.work."""
    accepted=load_module("t186_accepted_integral",repo/"experiments/t106-system-emulation/check_accel.py")
    rows=[]
    for r in results:
        total=0
        for s in r["effective_segments"]:
            a=(s["first_slot"]//8)*1568+(s["first_slot"]%8)*164
            b=min(r["horizon_ns"],(s["end_slot"]//8)*1568+(s["end_slot"]%8)*164)
            assert not s["low"] or s["first_slot"]>=cfg["words"]
            total+=accepted.clean_work(b,s["low"])-accepted.clean_work(a,s["low"])
        assert total==r["bus"]["control_base_ns"],("independent price",r["method"])
        assert r["bus"]["correction_extra_ns"]==sum(
            max(0,min(r["horizon_ns"],x["t"]+84)-(x["t"]+28)) for x in r["err_events"])
        assert r["bus"]["application_read_ns"]==sum(
            max(0,min(r["horizon_ns"],x["grant_ns"]+184)-x["grant_ns"]) for x in r["application"])
        assert r["bus_after_first_exceedance"]["total_ns"]>0
        assert sum(r["bus"][k] for k in ("control_base_ns","correction_extra_ns","application_read_ns"))==r["bus"]["total_ns"]
        rows.append(dict(method=r["method"],status="PASS",independent_base_work_ns=total))
    assert results[0]["err_events"]!=results[1]["err_events"],"own endogenous observations"
    assert all(r["Q"] is None for r in results)
    return dict(status="PASS",rows=rows,own_observation_streams_differ=True,
                scope="numeric cross-check of pilot price, not independent scientific review")
