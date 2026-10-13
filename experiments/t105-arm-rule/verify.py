"""Native differential test + bare-metal ARM execution. NOT a WCET tool."""
import ctypes as C, hashlib, json, random, re, subprocess, time
from pathlib import Path
from oracle import Oracle
from setup_tools import environment
HERE=Path(__file__).resolve().parent

class Input(C.Structure):
    _fields_=[('now',C.c_uint64),('generation',C.c_uint64),('timestamp',C.c_uint64),
              ('flags',C.c_uint32),('reserved',C.c_uint32)]
class State(C.Structure):
    _fields_=[(k,C.c_uint64) for k in ['now','generation','last_err','short_left','long_left','recovery_left']]+[('flags',C.c_uint32),('reserved',C.c_uint32)]

def cases(cfg):
    nw,nh,nr,pair=(cfg[k] for k in ('NW','NH','NR','PAIR_WINDOW'))
    pair_t=(10+pair+4)//5+10
    traces=[[(0,0,0,1,0),(nr-1,0,0,0,0),(nr,0,0,0,0)],
      [(0,0,0,1,0),(12,1,10,6,0),(pair_t,2,10+pair,6,0),
       (pair_t+nh-1,0,0,0,0),(pair_t+nh,0,0,0,0)],
      [(0,0,0,1,0),(12,1,10,6,0),(pair_t,2,11+pair,6,0),
       (pair_t+nw,0,0,0,0),(pair_t+nr,0,0,0,0)],
      [(0,0,0,1,0),(nr,1,10,10,0),(nr+1,2,15,2,0),(2*nr,0,0,0,0),(2*nr+1,0,0,0,0)],
      [(0,0,0,1,0),(1,1,10,6,0),(2,1,10,6,0),(nr+nh,0,0,0,0)],
      [(0,0,0,1,0),(1,2,10,6,0),(2,1,9,2,0)],
      [(0,0,0,1,0),(1,(1<<64)-1,(1<<64)-1,6,0),(2,0,0,6,0)],
      [(0,0,0,1,0),(1,0,0,16,0),(nr+1,0,0,0,0)],
      [(0,0,0,1,0),(nr,0,0,0,0),(nr-1,0,0,0,0)],
      [(0,0,0,1,0),(0,0,0,0,0)],
      [(0,0,0,1,0),(nr,0,0,0,1)],
      [(0,0,0,1,0),((1<<64)-1,0,0,0,0)]]
    rng=random.Random(cfg['seed']); left=cfg['functional_random_steps']
    while left:
        count=min(left,160);left-=count
        trace=[(0,0,0,1,0)];t=src=gen=0
        for _ in range(count):
            src+=rng.choice([1,5,pair-1,pair,pair+1])
            t=max(t+rng.choice([1,2,50,nw-1,nw,nw+1,nh,nr]),(src+4)//5+10)
            flags=rng.choice([0,2,6,10,14])
            if flags&2:gen+=1
            trace.append((t,gen,src,flags,0))
        traces.append(trace)
    return traces

def run(cmd,**kw):
    return subprocess.check_output(cmd,text=True,**kw)

def main():
    start=time.monotonic();cfg=json.loads((HERE/'config.json').read_text())
    build=HERE/'.build';build.mkdir(exist_ok=True);out=HERE/'outputs';out.mkdir(exist_ok=True)
    env=environment();vectors=[];tests=0;rejected=False
    tool_manifest=json.loads((out/'tools.json').read_text())
    for tool,version in tool_manifest['versions'].items():
        assert run([tool,'--version'],env=env).splitlines()[0]==version,('tool version',tool)
    for mutant in (False,True):
        so=build/('mutant.so' if mutant else 'rule.so')
        run(['gcc','-shared','-fPIC','-O2','-std=c11','-Wall','-Wextra','-Werror',
             *(['-DT105_MUTATE_OPEN_PAIR'] if mutant else []),str(HERE/'rule.c'),'-o',str(so)])
        lib=C.CDLL(str(so));lib.t105_apply.argtypes=[C.POINTER(State),C.POINTER(Input)]
        lib.t105_init.argtypes=[C.POINTER(State)];lib.t105_low.argtypes=[C.POINTER(State)]
        lib.t105_apply.restype=None;lib.t105_init.restype=None
        lib.t105_low.restype=C.c_uint32
        for trace in cases(cfg):
            s=State();lib.t105_init(C.byref(s));ref=Oracle()
            for i,v in enumerate(trace):
                inp=Input(*v);lib.t105_apply(C.byref(s),C.byref(inp));expected=ref.apply(v)
                actual=tuple(getattr(s,k) for k,_ in State._fields_)
                same=actual==expected and lib.t105_low(C.byref(s))==ref.low()
                if mutant and not same:rejected=True;break
                if not same:raise AssertionError((v,actual,expected))
                if not mutant:
                    tests+=1
                    if len(vectors)<512:vectors.append((v,expected,ref.low(),int(i==0)))
            if mutant and rejected:break
    assert rejected,'boundary mutant not detected'
    assert any(x[2] for x in vectors),'LOW vacuous'
    entries=[]
    def numbers(v):return ','.join(str(x)+'ULL' for x in v)
    for v,e,low,reset in vectors:
        entries.append('{{'+numbers(v)+'},{'+numbers(e)+'},'+str(low)+','+str(reset)+'}')
    (build/'vectors.h').write_text('static const vector vectors[]={\n'+',\n'.join(entries)+'\n};\n')
    flags=cfg['compiler_flags']+['-Wall','-Wextra','-Werror','-Wa,--noexecstack']
    elf=out/'rule-test.elf'
    run(['arm-none-eabi-gcc',*flags,'-nostdlib','-Wl,--build-id=none','-Wl,-z,noexecstack',
         '-I'+str(build),'-I'+str(HERE),'-T',str(HERE/'link.ld'),
         str(HERE/'start.S'),str(HERE/'rule.c'),str(HERE/'arm_test.c'),
         '-Wl,-Map='+str(build/'rule.map'),'-o',str(elf)],env=env)
    disasm=run(['arm-none-eabi-objdump','-d',str(elf)],env=env).replace(str(elf),elf.name)
    (out/'arm-disassembly.txt').write_text(disasm)
    static_instructions={};current=None
    for line in disasm.splitlines():
        match=re.match(r'^[0-9a-f]+ <([^>]+)>:',line)
        if match:
            current=match[1] if match[1].startswith('t105_') else None
            if current:static_instructions[current]=0
        elif current:
            insn=re.match(r'^\s*[0-9a-f]+:\s+[0-9a-f]{8}\s+(\S+)',line)
            if insn and not insn[1].startswith('.'):static_instructions[current]+=1
    size=run(['arm-none-eabi-size',str(elf)],env=env)
    symbols=run(['arm-none-eabi-nm','-S','--size-sort',str(elf)],env=env)
    rule_symbols={}
    for line in symbols.splitlines():
        parts=line.split()
        if len(parts)==4 and parts[-1].startswith('t105_'):
            rule_symbols[parts[-1]]=int(parts[1],16)
    readelf=run(['arm-none-eabi-readelf','-h','-A',str(elf)],env=env)
    (out/'arm-attributes.txt').write_text(readelf)
    assert 'ARM' in readelf and 'little endian' in readelf
    qemu=['qemu-system-arm','-M','xilinx-zynq-a9','-cpu','cortex-a9','-smp','1',
          '-m','128M','-display','none','-serial','none','-monitor','none',
          '-L',str(HERE/'.tools/root/usr/share/qemu'),
          '-semihosting-config','enable=on,target=native','-icount','shift=0,sleep=off',
          '-device','loader,file='+str(elf)+',cpu-num=0']
    trial=subprocess.run(qemu,env=env,text=True,capture_output=True,timeout=60)
    log=trial.stdout+trial.stderr
    (out/'arm-execution.txt').write_text(log)
    assert trial.returncode==0 and 'ARM_RULE_OK' in log,(trial.returncode,log)
    result={'status':'functional only; no Cortex-A9 WCET', 'native_comparisons':tests,
      'arm_comparisons':len(vectors),'pair_boundary_mutant_rejected':rejected,
      'sizeof_state':C.sizeof(State),'sizeof_input':C.sizeof(Input),'compiler_flags':flags,
      'rule_symbol_bytes':rule_symbols,'rule_text_bytes':sum(rule_symbols.values()),
      'static_rule_ARM_words':sum(rule_symbols.values())//4,
      'static_instruction_locations':static_instructions,
      'size_output':size,'symbol_sizes':symbols,'emulator_command':qemu,
      'emulator_exit':trial.returncode,'cpu_cycles':None,'cpu_wcet_ns':None,
      'dynamic_instruction_count':None,'model_clock_claim':'icount shift=0 is NOT CPU cycles',
      'host_reproduction_seconds':time.monotonic()-start,
      'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'rule.c',HERE/'rule.h',HERE/'oracle.py',elf,out/'arm-disassembly.txt']}}
    (out/'functional.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
