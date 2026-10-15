"""Full holds: literal native C, compressed C, raw Oracle, accepted ARM ELF.

No inherited output is regenerated. ELF direct function calls validate the
replacement arithmetic, not startup/MMIO/CDC timing (separate cold witness).
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import time
import zlib
from empty_rule import ARM,HERE,State,Batch,Decision,apply,library,empty_packet,advance_empty
sys.path.insert(0,str(ARM))
from batch_model import collect
from oracle import Oracle

NR=9015504896
STEP=49999


def vals(x):
    return tuple(getattr(x,k) for k,_ in x._fields_)


def check_elf(vectors):
    sys.path.insert(0,os.environ.get('T106_ANALYSIS',str(HERE/'.tools/analysis')))
    from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
    from unicorn.arm_const import UC_CPU_ARM_CORTEX_A9,UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_SP
    from elftools.elf.elffile import ELFFile
    path=ARM/'outputs/firmware.elf'
    assert hashlib.sha256(path.read_bytes()).hexdigest()=='2daf3308d167b71f2c65f21dfd5b9acde00e93fe5f1cc3ada8581d50d254fb09'
    uc=Uc(UC_ARCH_ARM,UC_MODE_ARM);uc.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
    uc.mem_map(0xfffc0000,0x40000)
    with path.open('rb') as f:
        elf=ELFFile(f)
        for s in elf.iter_segments():
            if s['p_type']=='PT_LOAD':uc.mem_write(s['p_vaddr'],s.data())
        sym={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
    state_addr,packet_addr,decision_addr,stop=0xfffd0000,0xfffd0100,0xfffd0200,0xfffd1000
    instructions=0;per_vector=[]
    def count(*_):
        nonlocal instructions
        instructions+=1
    uc.hook_add(UC_HOOK_CODE,count)
    def call(name,a,b):
        uc.reg_write(UC_ARM_REG_SP,0xfffdc000);uc.reg_write(UC_ARM_REG_LR,stop)
        uc.reg_write(UC_ARM_REG_R0,a);uc.reg_write(UC_ARM_REG_R1,b)
        uc.emu_start(sym[name],stop,count=10000)
        assert uc.reg_read(UC_ARM_REG_PC)==stop and uc.reg_read(UC_ARM_REG_R0)==1
    for v in vectors:
        before=instructions
        uc.mem_write(state_addr,bytes.fromhex(v['before']));uc.mem_write(packet_addr,bytes.fromhex(v['packet']))
        call('t105_batch_apply',state_addr,packet_addr)
        assert bytes(uc.mem_read(state_addr,C.sizeof(State))).hex()==v['after'],v['label']
        call('t105_decide',state_addr,decision_addr)
        assert bytes(uc.mem_read(decision_addr,C.sizeof(Decision))).hex()==v['decision'],v['label']
        per_vector.append(instructions-before)
    return {'vectors':len(vectors),'executed_ISA':instructions,'max_function_pair_ISA':max(per_vector),
            'firmware_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'scope':'actual accepted ELF functions; not driver, cold startup, MMIO or ARM time'}


def cases():
    yield 'full_initial_NR',[(1,[])],(NR+STEP-1)//STEP+2
    yield 'single_ERR_NW',[(100,[(10,50,1,0)])],(4500045002+STEP-1)//STEP+2
    yield 'paired_ERR_NH',[(100,[(10,50,1,0),(11,55,1,0)])],(9000090002+STEP-1)//STEP+2
    yield 'loss_still_present',[(100,[(10,50,0,1)])],500
    yield 'recovery_NR',[(100,[(10,50,0,1),(11,55,0,0)])],(NR+STEP-1)//STEP+2
    yield 'ERR_on_cut',[(100,[(100,500,1,0)])],64


def verify(execute_elf=False):
    lib=library();rows=[];vectors=[];before=time.monotonic();mutants=[]
    for name,groups,n in cases():
        s=State();lib.t105_batch_init(C.byref(s))
        oracle=Oracle();oracle.apply((0,0,0,1,0));generation=0
        for end,events in groups:
            for tick,source,err,loss in events:
                generation+=1;oracle.apply((tick,generation,source,2|4*err|8*loss,0))
            if end>oracle.now:oracle.apply((end,0,0,0,0))
        for b,expected in collect(0,groups):
            old=bytes(s);packet=Batch(*b);d=apply(lib,s,packet)
            assert vals(s.rule)==expected
            vectors.append({'label':name+'/seed','before':old.hex(),'packet':bytes(packet).hex(),
                            'after':bytes(s).hex(),'decision':bytes(d).hex()})
        origin=s.rule.now;initial=bytes(s)
        checkpoints={1,2,n-1,n}
        for timer in (s.rule.short_left,s.rule.long_left,s.rule.recovery_left):
            near=(timer+STEP-1)//STEP
            checkpoints.update(k for k in (near-1,near,near+1) if 1<=k<=n)
        for k in range(1,n+1):
            old=bytes(s);packet=empty_packet(s,origin+k*STEP);d=apply(lib,s,packet)
            expected=oracle.apply((origin+k*STEP,0,0,0,0))
            assert vals(s.rule)==expected,(name,k,'literal native/raw state')
            now,g,last,short,long,rec,flags,_=expected
            allowed=(flags&3)==3 and not flags&8
            de=(s.sequence,g,now+max(short,long,rec) if allowed else 0,int(allowed))
            assert vals(d)==(*de,zlib.crc32(struct.pack('<QQQI',*de))),(name,k,'decision')
            if k in checkpoints:
                # Independent full raw-history oracle, absolute deadlines.
                expected=collect(0,groups+[(origin+k*STEP,[])])[-1][1]
                assert vals(s.rule)==expected,(name,k)
                now,g,last,short,long,rec,flags,_=expected
                allowed=(flags&3)==3 and not flags&8
                de=(s.sequence,g,now+max(short,long,rec) if allowed else 0,int(allowed))
                assert vals(d)==(*de,zlib.crc32(struct.pack('<QQQI',*de)))
                vectors.append({'label':name+f'/{k}','before':old.hex(),'packet':bytes(packet).hex(),
                                'after':bytes(s).hex(),'decision':bytes(d).hex()})
        compressed=State.from_buffer_copy(initial)
        macro=advance_empty(lib,compressed,n,STEP)
        assert bytes(compressed)==bytes(s) and macro['decision']==bytes(d).hex(),name
        # Detect a sequence that silently forgets the represented packets.
        bad=State.from_buffer_copy(initial);apply(lib,bad,empty_packet(bad,origin+n*STEP))
        assert bad.sequence!=s.sequence and bytes(bad)!=bytes(s)
        mutants.append(name+'/lost-sequence')
        rows.append({'case':name,'literal_packets':n,'last_rule':vals(s.rule),
                     'last_decision':vals(d),'macro':macro})
        print(name,n,'packets: equal',flush=True)
    # A forbidden budget/hold reset is visible BEFORE expiry, not only after
    # both wrong and correct states have decayed to zero.
    initial=State.from_buffer_copy(bytes.fromhex(rows[0]['macro']['before']))
    good=State.from_buffer_copy(bytes(initial));advance_empty(lib,good,1,STEP)
    bad=State.from_buffer_copy(bytes(initial));bad.rule.recovery_left=0;advance_empty(lib,bad,1,STEP)
    assert bytes(good)!=bytes(bad);mutants.append('cleared-startup-hold')
    # Source mutation bounds: reject overflow/nonpositive counts explicitly.
    for n,step in ((0,1),(1,0),((1<<64),1),(1,(1<<64))):
        try:advance_empty(lib,State.from_buffer_copy(bytes(initial)),n,step)
        except ValueError:pass
        else:raise AssertionError('invalid empty jump accepted')
    out=HERE/'outputs'
    result={'scope':'empty rule transition only; no claim of complete accelerated arm_executor',
        'full_timers':{'NW':4500045002,'NH':9000090002,'NR':NR},
        'literal_packets':sum(r['literal_packets'] for r in rows),'cases':rows,
        'literal_prefixes_checked_against_raw_oracle':sum(r['literal_packets'] for r in rows),
        'compressed_endpoint_comparisons':len(rows),
        'mutants_rejected':mutants,'ARM_time_ns':None,'full_service_upper_ns':None,
        'source_sha256':{str(p.relative_to(HERE.parents[1])):hashlib.sha256(p.read_bytes()).hexdigest()
          for p in [HERE/'empty_rule.py',HERE/'verify_empty_rule.py',ARM/'rule.c',ARM/'batch.c',ARM/'crc32.c',
                    ARM/'rule.h',ARM/'batch.h',ARM/'batch_model.py',ARM/'oracle.py']},
        'vector_sha256':hashlib.sha256(json.dumps(vectors,sort_keys=True).encode()).hexdigest()}
    if execute_elf:
        result['ELF']=check_elf(vectors)
    else:
        # Keep the published ELF witness only if both vectors and source
        # provenance still match; a replay is not a fresh ISA execution.
        old=json.loads((out/'empty-rule.json').read_text())
        assert old['source_sha256']==result['source_sha256'] and old['vector_sha256']==result['vector_sha256']
        result['ELF']=old['ELF']
    (out/'empty-rule-vectors.json').write_text(json.dumps(vectors,indent=2)+'\n')
    (out/'empty-rule.json').write_text(json.dumps(result,indent=2)+'\n')
    print('empty-rule verified',result['literal_packets'],'host elapsed',round(time.monotonic()-before,3),'s')
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--execute-elf',action='store_true');args=ap.parse_args()
    verify(args.execute_elf)
