"""Actual startup ELF + independent short-descriptor/permission decoder.

CP15 and PS registers are explicitly emulated. NOT a PS7 timing/MMU/clock model.
No hardware connection, no fabricated readback and no physical qualification.
"""
import hashlib,json,struct,subprocess
from pathlib import Path
from analysis_tools import activate
from setup_tools import environment
activate()
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_CPSR
HERE=Path(__file__).resolve().parent
PROFILE=json.loads((HERE/'startup_profile.json').read_text())
SCT=(0,1,0,0);ACT=(0,1,0,1);TTB=(0,2,0,0);TTC=(0,2,0,2);DAC=(0,3,0,0)
EXPECT={0xf8000100:(0x7f01f,0x24000),0xf800010c:(1,1),0xf8000120:(0x1f003f30,0x1f000200),
 0xf80001c4:(1,1),0xf8000244:(0x133,0x22),0xf800020c:(1,1),0xf8000210:(3,3),
 0xf8000214:(0xf3,0xf3),0xf8000218:(0x33,0x33),0xf800012c:(0x1ffcccd,0),
 0xf8000910:(15,15),0xf8f00000:(3,3),0xf8f00040:(0xfff00000,0),
 0xf8f00044:(0xfff00000,0xffe00000),0xf8f02100:(1,0),
 0xf8007014:(0xc0000000,0x40000000),0xf8007080:(0xf0000000,0x20000000)}

def build():
    env=environment();out=HERE/'outputs'
    flags=json.loads((HERE/'config.json').read_text())['compiler_flags']
    cmd=['arm-none-eabi-gcc',*flags,'-Wall','-Wextra','-Werror','-nostdlib',
         '-fstack-usage','-Wl,--build-id=none','-Wl,-z,noexecstack','-T',str(HERE/'startup.ld'),
         str(HERE/'startup.S'),str(HERE/'startup.c'),'-o',str(out/'startup.elf')]
    subprocess.run(cmd,env=env,check=True)
    dis=subprocess.check_output(['arm-none-eabi-objdump','-d',str(out/'startup.elf')],env=env,text=True)
    (out/'startup-disassembly.txt').write_text(dis)
    return hashlib.sha256((out/'startup.elf').read_bytes()).hexdigest()

def word(uc,a): return struct.unpack('<I',uc.mem_read(a,4))[0]

def translate(uc,cp,a,access):
    """ARMv7 short descriptor, domain CLIENT, AP[2:0], XN, TEX/C/B.
    Independent of production page-builder constants/loops. Faults are errors
    of the harness: no claim Unicorn implements SCU/PS physical translations.
    """
    assert cp[TTC]==0,'TTBCR'
    first=word(uc,(cp[TTB]&0xffffc000)+4*(a>>20))
    if first&3!=1: raise ValueError('unmapped L1')
    domain=(first>>5)&15
    assert (cp[DAC]>>(2*domain))&3==1,'domain must check permissions'
    pte=word(uc,(first&0xfffffc00)+4*((a>>12)&255))
    if pte&2==0: raise ValueError('unmapped page')
    ap=((pte>>4)&3)|((pte>>7)&4)
    assert ap in (1,5),'privileged only'
    if access=='write': assert ap==1,'RO write'
    if access=='execute': assert not pte&1,'XN fetch'
    tex=(pte>>6)&7;c=(pte>>3)&1;b=(pte>>2)&1
    attr=(tex,c,b)
    assert attr in ((1,0,0),(0,0,1)),'unexpected cacheability/type'
    assert pte&(1<<10),'shareability'
    return (pte&0xfffff000)|(a&4095), {'kind':'normal-nc' if tex==1 else 'device-shared',
      'access':'privileged-RW' if ap==1 else 'privileged-RO','execute':not bool(pte&1)}

def page_audit(uc,cp):
    wanted={}
    for row in PROFILE['runtime_pages']:
        for n in range(row['count']):
            a=int(row['start'],16)+4096*n
            assert a not in wanted
            wanted[a]={k:row[k] for k in ('kind','access','execute')}
    # All L1 entries, every L2 descriptor in both populated coarse tables:
    # together these cover the entire 32-bit virtual domain, not sampled probes.
    actual={}
    for i in range(4096):
        p=word(uc,0xfffd0000+i*4)
        if p==0:continue
        assert i in (0x400,0xfff),'extra mapping'
        for j in range(256):
            if word(uc,(p&0xfffffc00)+4*j)==0:continue
            a=(i<<20)+(j<<12);pa,attributes=translate(uc,cp,a,'read')
            assert pa==a,'physical alias';actual[a]=attributes
    assert actual==wanted,(actual,wanted)
    for a in (0,0x100000,0xf8000000,0x40001000,0xfffff000):
        try:translate(uc,cp,a,'read')
        except ValueError:pass
        else:raise AssertionError('forbidden aperture open')
    return len(actual)

def execute(mutation=None,host_regs=None):
    uc=Uc(UC_ARCH_ARM,UC_MODE_ARM)
    uc.mem_map(0xfffc0000,0x40000);uc.mem_map(0x40000000,4096)
    uc.mem_map(0xf8000000,0x10000);uc.mem_map(0xf8f00000,0x4000)
    symbols={}
    for file in ('startup.elf','firmware.elf'):
        with (HERE/'outputs'/file).open('rb') as f:
            e=ELFFile(f)
            for seg in e.iter_segments():
                if seg['p_type']=='PT_LOAD':uc.mem_write(seg['p_vaddr'],seg.data())
            symbols.update({s.name:s['st_value'] for s in e.get_section_by_name('.symtab').iter_symbols()})
    cp={SCT:0x08c50078,ACT:0,TTB:0,TTC:0,DAC:0,(0,2,0,1):0,
        (0,0,0,0):0x413fc090,(0,0,0,5):0x80000000,(0,1,1,0):0,(0,12,0,0):0}
    regs={a:v for a,(mask,v) in EXPECT.items()};regs.update({0xf8f01000:1,0xf8f00100:1,0xf8f02f60:0x30000000})
    if host_regs is not None:
        for a in EXPECT:
            if a not in (0xf8007014,0xf8007080,0xf8f02100):regs[a]=host_regs[a]
    if mutation=='wrong-core':cp[(0,0,0,5)]|=1
    if mutation=='wrong-midr':cp[(0,0,0,0)]^=1
    if mutation=='nonsecure':cp[(0,1,1,0)]=1
    for name,bit in [('mmu-on',1),('dcache-on',4),('icache-on',4096)]:
        if mutation==name:cp[SCT]|=bit
    if isinstance(mutation,int):regs[mutation]^=EXPECT[mutation][0]&-EXPECT[mutation][0]
    for a,v in regs.items():uc.mem_write(a,struct.pack('<I',v))
    if mutation=='early-start':uc.mem_write(0x40000000,struct.pack('<I',8))
    uc.reg_write(UC_ARM_REG_CPSR,0x13 if mutation!='wrong-mode' else 0x1f)
    trace=[];calls=0;entered=False;trapped=False;insns=0;translation_on=False
    def code(u,pc,size,_):
        nonlocal calls,entered,trapped,insns,translation_on
        insns+=1
        if pc==symbols['startup_trap']:trapped=True;u.emu_stop();return
        if translation_on: assert translate(u,cp,pc,'execute')[0]==pc
        if pc==0xfffc0000:entered=True;page_audit(u,cp)
        if pc==symbols['t105_driver_step']:
            calls+=1
            if calls==4:u.emu_stop();return
        bits=word(u,pc)
        if bits&0x0f000010==0x0e000010 and ((bits>>8)&15)==15:
            key=((bits>>21)&7,(bits>>16)&15,bits&15,(bits>>5)&7);rd=(bits>>12)&15
            assert rd<15
            if bits&(1<<20):
                assert key in cp,('unknown MRC',key)
                u.reg_write(UC_ARM_REG_R0+rd,cp[key]);trace.append(['mrc',list(key),cp[key]])
            else:
                value=u.reg_read(UC_ARM_REG_R0+rd);trace.append(['mcr',list(key),value])
                if not (mutation=='ignore-ttbr' and key==TTB):cp[key]=value
                if key==SCT and value&1:
                    translation_on=True
                    if mutation=='cached-mmio':
                        u.mem_write(0xfffd4400,struct.pack('<I',word(u,0xfffd4400)|8))
                    if mutation=='alias-ocm':
                        a=0xfffd4000+0xc1*4;u.mem_write(a,struct.pack('<I',0xfffc0452))
                    if mutation=='domain-manager':cp[DAC]=3
            u.reg_write(UC_ARM_REG_PC,pc+4)
    def access(u,kind,a,size,value,_):
        if translation_on:
            assert size in (1,2,4,8) and a%size==0,'unaligned access with SCTLR.A'
            for x in (a,a+size-1):assert translate(u,cp,x,'write' if kind==UC_MEM_WRITE else 'read')[0]==x
        if 0xf8000000<=a<0xfffc0000 and a!=0x40000000:
            if kind==17: # UC_MEM_WRITE, not the HOOK bitmask
                trace.append(['write',hex(a),value])
            elif kind==16:
                if mutation=='gic-readback' and a==0xf8f00100:u.mem_write(a,struct.pack('<I',0))
                trace.append(['read',hex(a),word(u,a)])
    uc.hook_add(UC_HOOK_CODE,code)
    uc.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,access)
    uc.emu_start(0xfffe0000,0,count=100000)
    report=list(struct.unpack('<8I',uc.mem_read(0xfffed000,32)))
    if mutation is None:
        assert entered and not trapped and calls==4 and report[0]==0x43305244
        # NMFI-specific FIQ masking is not a Unicorn CP15 claim. Hardware
        # contract excludes FIQ via GIC/bypass/routing, not CPSR.F alone.
        assert (uc.reg_read(UC_ARM_REG_CPSR)&0x180)==0x180
        assert word(uc,symbols['controller']+200)==0
        assert page_audit(uc,cp)==15
        # Entry invalidation and barriers are decoded instructions; they are
        # NOT a proof that a PS7 pipeline/cache performs them in bounded time.
        assert all(k in cp for k in [(0,8,7,0),(0,7,5,0),(0,7,5,6)])
    else:assert trapped and not entered,mutation
    return {'case':str(mutation),'policy_entered':entered,'trapped':trapped,
      'report':[hex(x) for x in report],'prestart_driver_visits':calls,'trace':trace,
      'observed_ISA_instructions_not_cycles':insns}

def main():
    assert hashlib.sha256((HERE/'outputs/firmware.elf').read_bytes()).hexdigest()==PROFILE['firmware_sha256']
    digest=build();assert digest==build(),'startup ELF not reproducible'
    cases=[execute()]
    for m in ['wrong-core','wrong-midr','nonsecure','mmu-on','dcache-on','icache-on','wrong-mode',
              'early-start','ignore-ttbr','gic-readback',*EXPECT]:cases.append(execute(m))
    caught=[]
    for m in ['cached-mmio','alias-ocm','domain-manager']:
        try:execute(m)
        except (AssertionError,ValueError):caught.append(m)
        else:raise AssertionError('sentinel not rejected: '+m)
    resource={}
    with (HERE/'outputs/startup.elf').open('rb') as f:
        e=ELFFile(f);resource['startup_load_bytes']=sum(s['p_filesz'] for s in e.iter_segments() if s['p_type']=='PT_LOAD')
    frames=[]
    for p in (HERE/'outputs').glob('startup.elf-*.su'):
        for l in p.read_text().splitlines():frames.append(int(l.split('\t')[1]))
    resource.update(table_bytes=18432,table_reserved_pages_bytes=20480,report_reserved_bytes=4096,
      startup_stack_reserved_bytes=8192,firmware_stack_reserved_bytes=8192,
      startup_stack_static_frames_sum=max(sum(frames),0))
    result={'kind':'compiled startup + emulated registers + independent full page table audit',
      'startup_sha256':digest,'firmware_sha256':PROFILE['firmware_sha256'],'repeat_equal':True,
      'physical_launch':False,'CP15_PS7_hardware_model':False,'full_service_upper_ns':None,
      'resources':resource,'cases':cases,'independent_mutations_rejected':caught,
      'scope':'ISA functional; CP15 reads/writes intercepted, not hardware behavior or elapsed time'}
    (HERE/'outputs/startup-check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))

if __name__=='__main__':main()
