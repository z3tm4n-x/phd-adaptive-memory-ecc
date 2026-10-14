"""Compare reconstructed MMIO fields to raw-event and full-bank references."""
import ctypes as C
import hashlib,json,subprocess
from pathlib import Path
from verify_batch import Batch,BatchState,Decision,scenarios,decision_expected
from verify import State
HERE=Path(__file__).resolve().parent
class Input(C.Union):_fields_=[('batch',Batch),('words',C.c_uint32*24)]
class Output(C.Union):_fields_=[('decision',Decision),('words',C.c_uint32*8)]
class Driver(C.Structure):
    _fields_=[('rule',BatchState),('input',Input),('output',Output),('phase',C.c_uint32),('failure',C.c_uint32)]
def values(s):return tuple(getattr(s,n) for n,_ in s._fields_)
def library(source):
    so=HERE/'.build'/('driver-'+source+'.so')
    subprocess.run(['gcc','-shared','-fPIC','-std=c11','-O2','-Wall','-Wextra','-Werror',
      *[str(HERE/p) for p in (source+'.c','rule.c','batch.c','crc32.c')],'-o',str(so)],check=True)
    lib=C.CDLL(str(so));lib.t105_driver_init.argtypes=[C.POINTER(Driver)]
    lib.t105_driver_step.argtypes=[C.POINTER(Driver),C.POINTER(C.c_uint32)]
    return lib
def main():
    lib,ref=library('driver'),library('driver_reference');count=0
    for trace in scenarios():
        d,r=Driver(),Driver();lib.t105_driver_init(C.byref(d));ref.t105_driver_init(C.byref(r))
        m=(C.c_uint32*160)();mr=(C.c_uint32*160)();m[0]=mr[0]=8
        assert lib.t105_driver_step(C.byref(d),m)==ref.t105_driver_step(C.byref(r),mr)==0
        for vals,expected in trace:
            b=Batch(*vals)
            for bank in (m,mr):C.memmove(C.addressof(bank)+256,C.byref(b),96);bank[0]=9
            assert lib.t105_driver_step(C.byref(d),m)==ref.t105_driver_step(C.byref(r),mr)==0
            assert bytes(d.input.batch)==bytes(b)==bytes(r.input.batch)
            assert values(d.rule.rule)==values(r.rule.rule)==expected
            assert values(d.output.decision)==values(r.output.decision)==decision_expected(vals[0],expected)
            m[0]=mr[0]=8;mr[4]=vals[0]&0xffffffff;mr[5]=vals[0]>>32
            assert lib.t105_driver_step(C.byref(d),m)==ref.t105_driver_step(C.byref(r),mr)==1
            assert ref.t105_driver_step(C.byref(r),mr)==0
            count+=1
    boundary=0
    # Conditional warm states attack 32-bit truncation; no runtime reset.
    for g in (2**32-2,2**63-2,2**64-3):
        d=Driver();lib.t105_driver_init(C.byref(d));d.phase=1
        d.rule.sequence=2**32-1;d.rule.rule.now=100;d.rule.rule.generation=g
        d.rule.rule.flags=3;d.rule.start_tick=1
        b=Batch(2**32,g,g+2,104,1,0,0,0,0,0,2,0,3,0)
        m=(C.c_uint32*160)();m[0]=9;C.memmove(C.addressof(m)+256,C.byref(b),96)
        assert lib.t105_driver_step(C.byref(d),m)==0
        assert d.output.decision.generation==g+2 and d.output.decision.sequence==2**32
        assert bytes(d.input.batch)==bytes(b);boundary+=1
    faults=0
    for kind in ('replay','underflow','count-overflow','fault','wrong-first-bank'):
        d=Driver();lib.t105_driver_init(C.byref(d));d.phase=1
        d.rule.rule.generation=3 if kind=='underflow' else 0
        b=Batch(2 if kind=='replay' else 1,0,0,100,1,0,0,0,0,0,0,3,0)
        if kind=='count-overflow':b.end_generation=2**32
        if kind=='fault':b.flags|=16
        m=(C.c_uint32*160)();m[0]=9;C.memmove(C.addressof(m)+256,C.byref(b),96)
        if kind=='wrong-first-bank':d.phase=0
        assert lib.t105_driver_step(C.byref(d),m)==-1;assert d.failure;faults+=1
    result={'raw_oracle_packets':count,'full_bank_baseline_matches':count,'wide_carry_vectors':boundary,
      'explicit_faults':faults,'driver_size_bytes':C.sizeof(Driver),
      'source_sha256':{p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in ('driver.c','driver_reference.c')},
      'scope':'software semantics; collector identities separately proved; not timing or corrupt-memory coverage'}
    (HERE/'outputs/driver-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
