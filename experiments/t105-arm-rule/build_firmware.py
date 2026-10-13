"""Compile concrete MMIO firmware; native driver tests are NOT CPU WCET."""
import hashlib,json,re,subprocess
from pathlib import Path
from setup_tools import environment
HERE=Path(__file__).resolve().parent
def main():
    build=HERE/'.build';build.mkdir(exist_ok=True);out=HERE/'outputs'
    core=['rule.c','batch.c','crc32.c','driver.c']
    subprocess.run(['gcc','-O2','-std=c11','-Wall','-Wextra','-Werror',
        *[str(HERE/x) for x in core+['test_driver.c']],'-o',str(build/'driver-test')],check=True)
    subprocess.run([str(build/'driver-test')],check=True)
    env=environment();elf=out/'firmware.elf'
    flags=json.loads((HERE/'config.json').read_text())['compiler_flags']
    subprocess.run(['arm-none-eabi-gcc',*flags,'-Wall','-Wextra','-Werror',
      '-ffunction-sections','-fdata-sections','-fstack-usage','-Wa,--noexecstack','-nostdlib',
      '-Wl,--gc-sections','-Wl,--build-id=none','-Wl,-z,noexecstack',
      '-T',str(HERE/'link.ld'),*[str(HERE/x) for x in ['start.S']+core+['firmware.c']],
      '-o',str(elf)],env=env,check=True)
    subprocess.run(['arm-none-eabi-gcc',*flags,'-Wall','-Wextra','-Werror',
      '-ffunction-sections','-fdata-sections','-Wa,--noexecstack','-nostdlib',
      '-Wl,--gc-sections','-Wl,--build-id=none','-Wl,-z,noexecstack',
      '-T',str(HERE/'link.ld'),*[str(HERE/x) for x in
          ['start.S','rule.c','batch.c','crc32.c','driver_reference.c','firmware.c']],
      '-o',str(out/'firmware-reference.elf')],env=env,check=True)
    symbols=subprocess.check_output(['arm-none-eabi-nm','-S','--size-sort',str(elf)],env=env,text=True)
    assembly=subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],env=env,text=True)
    (out/'firmware-symbols.txt').write_text(symbols);(out/'firmware-disassembly.txt').write_text(assembly)
    rows=[]
    for line in symbols.splitlines():
        f=line.split()
        if len(f)==4 and not f[3].startswith('_'):rows.append({'name':f[3],'bytes':int(f[1],16),'kind':f[2]})
    stack={}
    for su in out.glob('firmware.elf-*.su'):
        for line in su.read_text().splitlines():
            name,size,kind=line.split('\t');assert kind=='static'
            stack[name.rsplit(':',1)[1]]=int(size)
    # No recursion/indirect calls in these production paths. The simple
    # sum over ALL reachable functions overestimates any actual call chain.
    assert stack
    result={'kind':'compiled Cortex-A9 OCM/MMIO firmware, not booted PS7/BSP or WCET',
      'ELF_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),'symbols':rows,
      'linked_code_and_rodata_bytes':sum(x['bytes'] for x in rows if x['kind'].lower()=='t')+56,
      'working_static_bytes':sum(x['bytes'] for x in rows if x['kind'].lower()=='b'),
      'static_function_frames':stack,'program_stack_conservative_bytes':sum(stack.values()),
      'stack_scope':'compiler static frames only; no exception/BSP stack or CPU cycles',
      'BSP_qualification':False,'CPU_WCET':None,
      'driver_native_assertions_passed':True,'ARM_barrier_instructions':len(re.findall(r'\bdmb\b',assembly))}
    (out/'firmware.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
