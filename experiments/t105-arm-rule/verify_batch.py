"""Raw-event oracle vs batch C, plus Cortex-A9 execution of batch/decision."""
import ctypes as C
import hashlib
import json
import random
import struct
import subprocess
import zlib
from pathlib import Path
from batch_model import collect, NAMES
from setup_tools import environment
from verify import State

HERE=Path(__file__).resolve().parent
class Batch(C.Structure):
    _fields_=[(x,C.c_uint64 if i<10 else C.c_uint32) for i,x in enumerate(NAMES)]
class BatchState(C.Structure):
    _fields_=[("rule",State),("sequence",C.c_uint64),("start_tick",C.c_uint64)]
class Decision(C.Structure):
    _fields_=[("sequence",C.c_uint64),("generation",C.c_uint64),
              ("not_before",C.c_uint64),("flags",C.c_uint32),("crc",C.c_uint32)]

def scenarios():
    pair=22500225010; nr=9015504896
    # Last recovery is in the middle, with a healthy ERR after it.
    yield collect(0,[(10,[(1,5,0,1),(2,10,0,0),(3,15,1,0)]),
                     (nr+2,[]),(nr+3,[])])
    for delta in (pair-1,pair,pair+1):
        t=(5+delta+4)//5+10
        yield collect(0,[(2,[(1,5,1,0)]),(t,[(t,5+delta,1,0)]),
                         (t+9015504896,[])])
    yield collect(7,[(10,[]),(12,[(11,50,0,1),(12,55,1,0)]),
                     (13,[(13,60,1,0)]),(20000000000,[])])
    # Single packet represents all 1000 loss/recovery pairs, not only end state.
    yield collect(0,[(2001,[(i+1,5*(i+1),0,i%2==0) for i in range(2000)]),
                     (nr+2000,[]),(nr+2001,[])])
    rng=random.Random(10520261014)
    for _ in range(160):
        t=0; lost=False; groups=[]
        for __ in range(125):
            t+=rng.choice((1,2,50,4500045002,9015504896))
            events=[]
            for ___ in range(rng.randrange(10)):
                t+=rng.randrange(1,6)
                if rng.randrange(3)==0: lost=not lost
                events.append((t,5*t-1,rng.randrange(2),lost))
            t+=rng.randrange(3)
            groups.append((t,events))
        yield collect(0,groups)

def native_library():
    build=HERE/".build";build.mkdir(exist_ok=True)
    so=build/"batch.so"
    subprocess.run(["gcc","-shared","-fPIC","-O2","-std=c11","-Wall","-Wextra","-Werror",
      str(HERE/"rule.c"),str(HERE/"batch.c"),str(HERE/"crc32.c"),"-o",str(so)],check=True)
    lib=C.CDLL(str(so))
    lib.t105_batch_init.argtypes=[C.POINTER(BatchState)]
    lib.t105_batch_init.restype=None
    lib.t105_batch_apply.argtypes=[C.POINTER(BatchState),C.POINTER(Batch)]
    lib.t105_batch_apply.restype=C.c_int
    lib.t105_decide.argtypes=[C.POINTER(BatchState),C.POINTER(Decision)]
    lib.t105_decide.restype=C.c_int
    return lib

def decision_expected(seq,state):
    now,gen,last,short,long,rec,flags,res=state
    allow=(flags&3)==3 and not flags&8
    wait=max(short,long,rec,int(bool(flags&16)))
    d=(seq,gen,now+wait if allow else 0,1 if allow else 0)
    return (*d,zlib.crc32(struct.pack("<QQQI",*d)))

def main():
    lib=native_library(); rows=[]; count=0; native_raw=0
    for trace in scenarios():
        s=BatchState(); lib.t105_batch_init(C.byref(s))
        for i,(vals,expected) in enumerate(trace):
            b=Batch(*vals)
            assert lib.t105_batch_apply(C.byref(s),C.byref(b)),vals
            actual=tuple(getattr(s.rule,k) for k,_ in State._fields_)
            assert actual==expected,(vals,actual,expected)
            d=Decision(); assert lib.t105_decide(C.byref(s),C.byref(d))
            de=decision_expected(vals[0],expected)
            assert tuple(getattr(d,k) for k,_ in Decision._fields_)==de
            count+=1; native_raw+=vals[10]
            if len(rows)<512: rows.append((vals,expected,de,int(i==0)))
    # Corrupting away an INTERNAL recovery must fail or disagree, even though
    # final health and generation are unchanged.
    original,expected=next(scenarios())[0]
    mutated=list(original);mutated[9]=0;mutated[12]&=~4
    s=BatchState();lib.t105_batch_init(C.byref(s))
    accepted=lib.t105_batch_apply(C.byref(s),C.byref(Batch(*mutated)))
    differs=tuple(getattr(s.rule,k) for k,_ in State._fields_)!=expected
    assert not accepted or differs
    negative=0
    for index,value in ((0,2),(1,1),(2,8),(3,0),(10,0),(11,99),(13,1)):
        bad=list(original);bad[index]=value
        s=BatchState();lib.t105_batch_init(C.byref(s))
        assert not lib.t105_batch_apply(C.byref(s),C.byref(Batch(*bad)))
        d=Decision();assert not lib.t105_decide(C.byref(s),C.byref(d))
        assert d.flags==2;negative+=1
    # An unbounded multi-ERR history is not silently summarized.
    bad=list(original);bad[11]=2;bad[5]=0;bad[6]=22500225011;bad[7]=1;bad[8]=3
    s=BatchState();lib.t105_batch_init(C.byref(s))
    assert not lib.t105_batch_apply(C.byref(s),C.byref(Batch(*bad)));negative+=1
    build=HERE/".build";out=HERE/"outputs"
    nums=lambda xs:",".join(str(x)+"ULL" for x in xs)
    entries=["{{"+nums(b)+"},{"+nums(s)+"},{"+nums(d)+"},"+str(reset)+"}"
             for b,s,d,reset in rows]
    (build/"batch_vectors.h").write_text("static const vector vectors[]={\n"+
                                      ",\n".join(entries)+"\n};\n")
    env=environment(); elf=out/"batch-test.elf"
    flags=json.loads((HERE/"config.json").read_text())["compiler_flags"]
    subprocess.run(["arm-none-eabi-gcc",*flags,"-Wall","-Wextra","-Werror",
      "-Wa,--noexecstack","-nostdlib","-Wl,--build-id=none","-Wl,-z,noexecstack",
      "-I"+str(build),"-I"+str(HERE),"-T",str(HERE/"link.ld"),
      *[str(HERE/x) for x in ("start.S","rule.c","batch.c","crc32.c","arm_batch_test.c")],
      "-o",str(elf)],env=env,check=True)
    run=subprocess.run(["qemu-system-arm","-M","xilinx-zynq-a9","-cpu","cortex-a9",
      "-smp","1","-m","128M","-display","none","-serial","none","-monitor","none",
      "-L",str(HERE/".tools/root/usr/share/qemu"),
      "-semihosting-config","enable=on,target=native","-icount","shift=0,sleep=off",
      "-device","loader,file="+str(elf)+",cpu-num=0"],env=env,text=True,capture_output=True,timeout=60)
    assert run.returncode==0 and "ARM_BATCH_OK" in run.stdout+run.stderr
    (out/"batch-arm-execution.txt").write_text(run.stdout+run.stderr)
    sizes=subprocess.check_output(["arm-none-eabi-nm","-S","--size-sort",str(elf)],env=env,text=True)
    (out/"batch-symbols.txt").write_text(sizes)
    result={"status":"functional packet/interval computation; no ARM WCET",
      "native_packets":count,"represented_raw_events":native_raw,"ARM_packets":len(rows),
      "internal_recovery_mutant_rejected":True,"invalid_packets_rejected":negative,
      "packet_bytes":C.sizeof(Batch),"state_bytes":C.sizeof(BatchState),
      "decision_bytes":C.sizeof(Decision),"cpu_wcet_ns":None,
      "ELF_sha256":hashlib.sha256(elf.read_bytes()).hexdigest()}
    (out/"batch-functional.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
