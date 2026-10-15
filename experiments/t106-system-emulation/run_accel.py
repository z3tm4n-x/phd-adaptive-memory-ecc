"""Actual accepted startup+firmware ELF linked to the full vendor-XPM RTL.

The host executes ARM ISA, not ARM cycles. Explicit model delay is introduced
at completed driver visits; measured cut-to-cut in HDL is reported separately.
No accepted experiment output is overwritten by this runner.
"""
import argparse
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
ARM=HERE.parent/'t105-arm-rule'
sys.path.insert(0,str(ARM))
# Reuse installed pinned wheels if explicitly provided, never system writes.
if os.environ.get('T106_ANALYSIS'):
    sys.path.insert(0,os.environ['T106_ANALYSIS'])
else:
    sys.path.insert(0,str(HERE/'.tools/analysis'))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ,UC_MEM_WRITE
from unicorn.arm_const import UC_CPU_ARM_CORTEX_A9,UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_R0,UC_ARM_REG_CPSR
from elftools.elf.elffile import ELFFile
# Accepted functional CP15/GIC/table harness, NOT a new independent PS7 model.
from startup_check import EXPECT,SCT,ACT,TTB,TTC,DAC,translate,page_audit,word
from gicv1_model import GicV1Controls

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_config():return json.loads((HERE/'config.json').read_text())

def inputs(folder,c):
    case=next(s for s in c['scenarios'] if s['id']==4)
    rows=sorted(case['injections'],key=lambda r:(r['at_ns'],r['parent']))
    (folder/'injections.txt').write_text(''.join(f"{r['at_ns']} {r['word']} {r['bit']} {r['parent']}\n" for r in rows))
    a=case['application'];lines=[]
    for i in range(a['count']):
        kind=2 if i%2==0 else 1
        mask=a['write_masks_cycle'][(i//2)%len(a['write_masks_cycle'])]
        packet=(i<<57)|(mask<<53)|((0x12340000|i)<<21)|((a['word_base']+i//2)<<2)|kind
        lines.append(f"{a['first_offer_ns']+i*a['interval_ns']} {i%2} {packet:x}\n")
    (folder/'application.txt').write_text(''.join(lines))
    return {p.name:digest(p) for p in (folder/'injections.txt',folder/'application.txt')}

def execute(mode,c,case_name='short',accelerate=True):
    folder=HERE/'.build'/f'accel-{case_name}-{mode}-{int(accelerate)}-{time.time_ns()}'
    folder.mkdir(parents=True)
    source_hashes={str(p.relative_to(REPO)):digest(p) for p in
        [HERE/'run_accel.py',HERE/'bridge.c',HERE/'tb_accel.sv',HERE/'accel.tcl',HERE/'ACCELERATION.md',
         ARM/'outputs/startup.elf',ARM/'outputs/firmware.elf']}
    from empty_rule import State,Batch,Decision,advance_empty,library
    from empty_time import integrate,first_slot,slot
    lib=library()
    horizon={'short':1200000,'quiet':272000000000,'loss':362000000000}[case_name]
    j=first_slot(181000000000);j+=(-j)%3
    fb=slot(j)+58 if case_name=='quiet' else 0
    fe=fb+4 if fb else 0
    lb,le=(181000000000,181002000000) if case_name=='loss' else (0,0)
    (folder/'accel.txt').write_text(f'{horizon} {fb} {fe} {lb} {le} {int(mode=="fixed")}\n')
    for filename in ('injections.txt','application.txt'):(folder/filename).write_text('')
    input_hashes={p.name:digest(p) for p in [folder/'accel.txt',folder/'injections.txt',folder/'application.txt']}
    macros=[];offset_ticks=0;t0=0
    STEP=9408
    external=[x for x in (fb,fe,lb,le,horizon) if x]
    def state(u):return State.from_buffer_copy(bytes(u.mem_read(symbols['controller'],72)))
    subprocess.run(['gcc','-shared','-fPIC','-O2','-std=c11','-D_POSIX_C_SOURCE=200809L',
        '-Wall','-Wextra','-Werror',str(HERE/'bridge.c'),'-o',str(folder/'bridge.so')],check=True)
    uc=Uc(UC_ARCH_ARM,UC_MODE_ARM);uc.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
    for a,n in [(0xfffc0000,0x40000),(0x40000000,4096),(0xf8000000,0x10000),(0xf8f00000,0x4000)]:uc.mem_map(a,n)
    symbols={}
    case=next(s for s in c['scenarios'] if s['id']==4)
    for name in ('startup','firmware'):
        path=ARM/f'outputs/{name}.elf';assert digest(path)==case[f'{name}_sha256']
        with path.open('rb') as f:
            e=ELFFile(f)
            for s in e.iter_segments():
                if s['p_type']=='PT_LOAD':uc.mem_write(s['p_vaddr'],s.data())
            symbols.update({s.name:s['st_value'] for s in e.get_section_by_name('.symtab').iter_symbols()})
    cp={SCT:0x08c50078,ACT:0,TTB:0,TTC:0,DAC:0,(0,2,0,1):0,
        (0,0,0,0):0x413fc090,(0,0,0,5):0x80000000,(0,1,1,0):0,(0,12,0,0):0}
    regs={a:v for a,(mask,v) in EXPECT.items()};regs[0xf8f02f60]=0x30000000
    for a,v in regs.items():uc.mem_write(a,struct.pack('<I',v))
    gic=GicV1Controls();uc.reg_write(UC_ARM_REG_CPSR,0x13)
    n=0;calls=0;visits=0;visit_return=None;mission=False;done=False;entered=False
    startup_insns=None;mission_insns=0;mmio=collections.Counter();boot_accesses=[]
    last_tick=0;driver_instructions=[];visit_start=0;ready_pages=None
    before=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='t106-') as tmp:
        sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);sock.bind(tmp+'/rpc');sock.listen(1);sock.settimeout(180)
        env=dict(os.environ,T106_SOCKET=tmp+'/rpc',T106_RUN=str(folder))
        log=(folder/'vendor.log').open('w')
        command=[os.environ.get('VIVADO','/home/z3tm4n/bin/vivado-wsl'),'-mode','batch','-nolog','-nojournal',
            '-source',str(HERE/'accel.tcl'),'-tclargs',str(folder)]
        child=subprocess.Popen(command,cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT)
        stream=None
        def rpc(op,addr=0,value=0,delay=0):
            nonlocal stream,last_tick,done
            if stream is None:
                conn,_=sock.accept();conn.settimeout(240);stream=conn.makefile('rwb',buffering=0)
            stream.write(f'{op} {addr:x} {value&0xffffffff:x} {delay}\n'.encode())
            line=stream.readline().decode().split()
            if len(line)!=3:raise RuntimeError('RTL ended or bridge failed; '+str(folder))
            resp,data,tick=int(line[0]),int(line[1],16),int(line[2]);last_tick=tick
            if op==4 and data:done=True
            return resp,data,tick
        def code(u,pc,size,_):
            nonlocal n,calls,visits,visit_return,mission,entered,startup_insns,mission_insns,visit_start,ready_pages,t0,offset_ticks
            n+=1
            if mission:mission_insns+=1
            if pc==symbols['startup_trap']:raise AssertionError('cold-start trap')
            if cp[SCT]&1:assert translate(u,cp,pc,'execute')[0]==pc
            if pc==0xfffc0000:
                # Entry hook precedes the first firmware instruction.
                entered=True;startup_insns=n-1;ready_pages=page_audit(u,cp)
            if visit_return is not None and pc==visit_return:
                driver_instructions.append(n-visit_start);visits+=1;visit_return=None
                if mission:
                    phase=word(u,symbols['controller']+200)
                    if phase==2:
                        rpc(4,delay=200)
                        if not t0:t0=rpc(7)[1]
                        maybe_jump(u)
                        st=state(u)
                        target=st.rule.now+1+STEP-6
                        delay=target-(last_tick+offset_ticks)
                        if delay<0:raise AssertionError(('service overrun',delay,folder))
                        rpc(4,delay=delay)
                    else:rpc(4,delay=4000)
                    if done:
                        # Stop before this caller instruction executes.
                        n-=1;mission_insns-=1;u.emu_stop();return
            if pc==symbols['t105_driver_step']:
                calls+=1
                if not mission and calls==4:
                    assert entered and word(u,0xfffed000)==0x43305244
                    assert word(u,symbols['controller']+200)==0
                    assert all(gic.read(a)==0 for a in gic.FIELDS)
                    assert ready_pages==15
                    mission=True;rpc(3)
                    if mode=='fixed':
                        # The fourth phase0 entry is a stop marker, not work.
                        n-=1;u.emu_stop();return
                    mission_insns+=1  # this first runtime instruction WILL execute
                visit_start=n;visit_return=u.reg_read(UC_ARM_REG_LR)
            bits=word(u,pc)
            if bits==0xe320f003:raise AssertionError('firmware WFI/fault')
            if bits&0x0f000010==0x0e000010 and ((bits>>8)&15)==15:
                key=((bits>>21)&7,(bits>>16)&15,bits&15,(bits>>5)&7);rd=(bits>>12)&15
                assert rd<15
                if bits&(1<<20):
                    assert key in cp;u.reg_write(UC_ARM_REG_R0+rd,cp[key])
                else:cp[key]=u.reg_read(UC_ARM_REG_R0+rd)
                u.reg_write(UC_ARM_REG_PC,pc+4)
            if n>10000000:raise RuntimeError('functional instruction guard, not WCET')
        def access(u,kind,a,size,value,_):
            if cp[SCT]&1:
                assert size in (1,2,4,8) and a%size==0
                for x in (a,a+size-1):assert translate(u,cp,x,'read' if kind==UC_MEM_READ else 'write')[0]==x
            if 0x40000000<=a<0x40001000:
                assert size==4;read=kind==UC_MEM_READ
                resp,data,tick=rpc(0 if read else 1,a-0x40000000,value)
                assert resp==0,('AXI response',a,resp)
                if read:u.mem_write(a,struct.pack('<I',data))
                mmio[('runtime_' if mission else 'boot_')+('read' if read else 'write')]+=1
            elif a in gic.FIELDS:
                if kind==UC_MEM_WRITE:gic.write(a,value)
                else:u.mem_write(a,struct.pack('<I',gic.read(a)))
                boot_accesses.append((kind,a,value if kind==UC_MEM_WRITE else gic.read(a)))
        def maybe_jump(u=None):
            nonlocal offset_ticks
            if not accelerate or not t0:return
            for _ in range(200):
                flags=rpc(6)[1]
                if flags&1:break
                rpc(4,delay=1)
            else:return
            flags=rpc(6)[1]
            low=bool(flags&2)
            if bool(flags&4)!=low and mode!='fixed':return
            now=(last_tick+offset_ticks)*20
            limit=t0+horizon
            for rel in external:
                if t0+rel>now:limit=min(limit,t0+rel)
            st=state(u) if u is not None else None
            if st is not None:
                d=Decision.from_buffer_copy(bytes(u.mem_read(symbols['controller']+168,32)))
                if d.flags==1 and d.not_before*20>now:limit=min(limit,d.not_before*20)
            n=max(0,(limit-now-10000)//376320)*2
            if n==0:return
            end=now+n*188160
            price=integrate(now-t0,end-t0,low=low)
            assert not price['partial_begin'] and not price['partial_end'],price
            if st is not None:
                macro=advance_empty(lib,st,n,STEP)
                packet=Batch(st.sequence,st.rule.generation,st.rule.generation,st.rule.now,st.start_tick,
                             0,0,0,0,0,0,0,1+2*bool(st.rule.flags&1),0)
                decision=bytes.fromhex(macro['decision'])
            else:
                macro={};packet=Batch();decision=bytes(32)
            (folder/'jump.txt').write_text(f"{price['completed']} {bytes(packet)[::-1].hex()} {decision[::-1].hex()}\n")
            rpc(5,delay=n)
            offset_ticks+=n*STEP
            if st is not None:
                u.mem_write(symbols['controller'],bytes(st))
                u.mem_write(symbols['controller']+72,bytes(packet))
                u.mem_write(symbols['controller']+168,decision)
            macros.append(dict(begin_ns=now-t0,end_ns=end-t0,empty_services=n,low=low,price=price,**macro))
        uc.hook_add(UC_HOOK_CODE,code);uc.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,access)
        try:
            uc.emu_start(0xfffe0000,0)
            if mode=='fixed':
                while not done:
                    rpc(4,delay=4000)
                    if not t0:t0=rpc(7)[1]
                    maybe_jump()
            assert done and mission
            rpc(2)
            stream.close();child.wait(timeout=45)
            assert child.returncode==0
        finally:
            if child.poll() is None:child.kill();child.wait()
            sock.close();log.close()
    text=(folder/'vendor.log').read_text(errors='replace')
    assert not any(x in text for x in ('Fatal:', 'FATAL:', 'ERROR:')),text[-3000:]
    meta={'mode':mode,'scenario':case_name,'accelerated':accelerate,'macros':macros,'host_elapsed_s':time.monotonic()-before,
        'startup_instructions':startup_insns,'ARM_instructions_including_boot':n,
        'ARM_instructions_runtime':mission_insns,'driver_calls':calls,'completed_driver_visits':visits,
        'max_observed_instructions_per_driver_visit':max(driver_instructions),
        'MMIO':dict(mmio),'startup_report':hex(word(uc,0xfffed000)),
        'boot_uses_corrected_ELF':True,'page_mappings_checked':ready_pages,'gic_accesses':boot_accesses,
        'model_full_service_target_slow_ticks':STEP,
        'actual_ARM_time_ns':None,'ARM_WCET_ns':None,'CPU_utilization_measured':None,
        'source_sha256':source_hashes,'input_sha256':input_hashes,'build':str(folder),
        'scope':'actual ARM ISA + functional CP15/GIC + vendor-XPM/production RTL; not physical PS7 or WCET'}
    (folder/'run.json').write_text(json.dumps(meta,indent=2)+'\n')
    out=HERE/'outputs';out.mkdir(exist_ok=True)
    stem=f'accel-{case_name}-{mode}-{"skip" if accelerate else "literal"}'
    meta['trace_sha256']=digest(folder/'trace.txt')
    (out/f'{stem}.json').write_text(json.dumps(meta,indent=2)+'\n')
    with (out/f'{stem}.trace.gz').open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,filename='') as gz:
            with (folder/'trace.txt').open('rb') as src:shutil.copyfileobj(src,gz)
    print(json.dumps({'mode':mode,'case':case_name,'macros':len(macros),
                     'host_elapsed_s':meta['host_elapsed_s'],'build':str(folder)},indent=2))
    return meta

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['adaptive','fixed','both'],default='adaptive')
    ap.add_argument('--case',choices=['short','quiet','loss'],default='short')
    ap.add_argument('--literal',action='store_true')
    args=ap.parse_args();c=read_config()
    for mode in (['adaptive','fixed'] if args.mode=='both' else [args.mode]):
        print('START',args.case,mode,flush=True);execute(mode,c,args.case,not args.literal)
if __name__=='__main__':main()
