"""Actual firmware ELF + actual mailbox RTL. ISA correctness, NOT PS7 timing.

No production C update function runs on the host. Every ARM MMIO operation
crosses the VPI bridge to the peripheral. CPU instructions cost zero simulated
time; RTL edge times measure this declared test harness only.
"""
import collections,hashlib,json,random,struct,subprocess
from pathlib import Path
from analysis_tools import activate
activate()
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ
from unicorn.arm_const import UC_CPU_ARM_CORTEX_A9, UC_ARM_REG_LR
from elftools.elf.elffile import ELFFile
from batch_model import collect
from verify_batch import decision_expected
HERE=Path(__file__).resolve().parent

def execute(build,stall=0,mutation='none',variant='optimized'):
    folder=build/f'{variant}-{stall}-{mutation}';folder.mkdir(exist_ok=True)
    child=subprocess.Popen(['vvp','-M',str(build),'-m','isa_vpi',str(build/'tb.vvp')],
        cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    uc=Uc(UC_ARCH_ARM,UC_MODE_ARM);uc.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_A9)
    uc.mem_map(0xfffc0000,0x40000);uc.mem_map(0x40000000,0x1000)
    elfpath=HERE/'outputs'/('firmware-reference.elf' if variant=='reference' else 'firmware.elf')
    with elfpath.open('rb') as f:
        elf=ELFFile(f);entry=elf.header['e_entry']
        for seg in elf.iter_segments():
            if seg.header['p_type']=='PT_LOAD':uc.mem_write(seg.header['p_vaddr'],seg.data())
        sym={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
    n=0;calls=0;mmio=[];log=[];counts=collections.Counter();last_cut=0;rounds=[]
    pcs=collections.Counter();rng=random.Random(10520261015);failure=0;finished=False
    visit_start=None;visit_return=None;visit_lengths=[]
    def rpc(op,addr=0,value=0,delay=0):
        child.stdin.write(f'{op} {addr:x} {value:x} {delay}\n');child.stdin.flush()
        while True:
            line=child.stdout.readline()
            if not line:raise RuntimeError('RTL ended: '+''.join(log[-20:]))
            log.append(line)
            if line.startswith('ISA_REPLY '):
                _,resp,data,tick=line.split();return int(resp),int(data,16),int(tick)
    def instruction(u,pc,size,_):
        nonlocal n,calls,failure,finished,visit_start,visit_return
        n+=1;pcs[pc]+=1
        if visit_start is not None and pc==visit_return:
            visit_lengths.append(n-visit_start);visit_start=None
        if pc==sym['t105_driver_step']:
            calls+=1
            seq=struct.unpack('<Q',u.mem_read(sym['controller']+56,8))[0]
            phase,failure=struct.unpack('<II',u.mem_read(sym['controller']+200,8))
            if seq>=32 and phase in (0,1):finished=True;u.emu_stop()
            else:
                visit_start=n;visit_return=u.reg_read(UC_ARM_REG_LR)
        if bytes(u.mem_read(pc,4))==bytes.fromhex('03f020e3'): # ARM WFI on explicit fault
            failure=struct.unpack('<I',u.mem_read(sym['controller']+204,4))[0]
            u.emu_stop()
        if n>1000000:raise RuntimeError('firmware progress limit, not a timed upper')
    def access(u,kind,address,size,value,_):
        nonlocal last_cut
        assert size==4
        addr=address-0x40000000;isread=kind==UC_MEM_READ
        changed=value
        if mutation=='bad-crc' and not isread and addr==0x21c:changed^=1
        resp,data,tick=rpc(0 if isread else 1,addr,changed,rng.randrange(stall+1))
        if isread:
            if mutation=='bad-sequence' and addr==0x100:data^=1
            u.mem_write(address,struct.pack('<I',data))
        # A bus error is an observation of hardware rejection, not an ARM
        # exception model. Driver must subsequently see the sticky fault.
        counts['reads' if isread else 'writes']+=1
        if resp:counts['SLVERR']+=1
        mmio.append((n,int(isread),addr,value if not isread else data,resp,tick))
        if not isread and addr==4:
            if last_cut:rounds.append(tick-last_cut)
            last_cut=tick
    uc.hook_add(UC_HOOK_CODE,instruction)
    uc.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,access,begin=0x40000000,end=0x40000fff)
    try:
        uc.emu_start(entry,0)
        _,packets,tick=rpc(2);child.stdin.close();child.wait(timeout=5)
    finally:
        if child.poll() is None:child.kill();child.wait()
    (folder/'bridge.log').write_text(''.join(log))
    (folder/'mmio.json').write_text(json.dumps(mmio)+'\n')
    if mutation=='none':assert finished and not failure and packets==32
    else:assert failure and not finished,(mutation,failure,packets)
    raw=[]
    for line in (folder/'raw.txt').read_text().splitlines():
        t,e=line.split();e=int(e,16);raw.append((int(t),(e>>2)&((1<<64)-1),e&1,(e>>1)&1))
    records=[];groups=[];previous=4
    for line in (folder/'packets.txt').read_text().splitlines():
        b,d=line.split();b=struct.unpack('<10Q4I',int(b,16).to_bytes(96,'little'))
        d=struct.unpack('<QQQII',int(d,16).to_bytes(32,'little'))
        groups.append((b[3],[e for e in raw if previous<e[0]<=b[3]]));previous=b[3];records.append((b,d))
    for (b,d),(eb,state) in zip(records,collect(4,groups)):
        assert b==eb,(b,eb)
        assert d==decision_expected(b[0],state),(d,state)
    cuts=[int(x) for x in (folder/'cuts.txt').read_text().split()]
    assert [b[3]+1 for b,d in records]==cuts[:len(records)]
    ranges={}
    for name in ('t105_batch_apply','t105_decide','t105_driver_step','t105_crc32'):
        ranges[name]=sum(v for pc,v in pcs.items() if sym[name]<=pc<min(x for x in sym.values() if x>sym[name]))
    structural=None
    if variant=='optimized':
        from service_work import analyze, parse
        i,f=parse((HERE/'outputs/firmware-disassembly.txt').read_text(),
                  (HERE/'outputs/firmware-symbols.txt').read_text())
        structural=analyze(i,f)['t105_driver_step']['upper']['instructions']
        assert visit_lengths and max(visit_lengths)<=structural
    return {'variant':variant,'stall_max_slow_ticks':stall,'mutation':mutation,'firmware_completed_rounds':packets,
      'driver_calls':calls,'ARM_instructions':n,'function_instruction_counts':ranges,
      'MMIO':dict(counts),'peripheral_model_ticks':tick,'round_peripheral_ticks':rounds,
      'actual_cut_ticks':cuts,'cut_to_cut_peripheral_ticks':[y-x for x,y in zip(cuts,cuts[1:])],
      'driver_fault':failure,'raw_events':len(raw),'independent_packet_matches':len(records),
      'ELF_sha256':hashlib.sha256(elfpath.read_bytes()).hexdigest(),
      'mmio_sha256':hashlib.sha256((folder/'mmio.json').read_bytes()).hexdigest(),
      'completed_driver_visits':len(visit_lengths),'observed_max_instructions_per_visit':max(visit_lengths),
      'structural_instructions_per_visit_upper':structural,
      'CPU_cycles':None,'CPU_WCET_ns':None,'PS7_latency_ns':None,
      'qualification':'zero instruction time, direct mailbox, no GP0/SmartConnect model'}

def main():
    build=HERE/'.build/isa';build.mkdir(parents=True,exist_ok=True)
    subprocess.run(['gcc','-O2','-std=c11','-Wall','-Wextra','-Werror','-fPIC','-shared',
      '-I/usr/include/iverilog',str(HERE/'isa_vpi.c'),'-lveriuser','-lvpi','-o',str(build/'isa_vpi.vpi')],check=True)
    subprocess.run(['iverilog','-g2012','-s','tb_isa','-o',str(build/'tb.vvp'),
      *[str(HERE/x) for x in ('history_batch.sv','rule_mailbox.sv','tb_isa.sv')]],check=True)
    cases=[execute(build,0,'none','reference')]+[execute(build,stall,mut)
      for stall,mut in ((0,'none'),(7,'none'),(0,'bad-crc'),(0,'bad-sequence'))]
    out={'kind':'actual ARM firmware ISA + RTL MMIO, NOT a cycle-accurate ARM platform',
      'cases':cases,'shared_dependencies':['declared ABI/constants','Unicorn ARM ISA','Icarus RTL'],
      'oracle':'raw events expanded by independent absolute-deadline Oracle'}
    (HERE/'outputs/isa-rtl.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
