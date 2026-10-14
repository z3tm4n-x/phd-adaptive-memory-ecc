"""One-command T105 functional/formal checkpoint; optional vendor runs."""
import argparse, hashlib, json, platform, py_compile, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--bootstrap',action='store_true')
    p.add_argument('--ps7',action='store_true');p.add_argument('--repeat-binary',action='store_true')
    p.add_argument('--integration',action='store_true');p.add_argument('--full',action='store_true')
    p.add_argument('--advance',action='store_true');a=p.parse_args()
    if a.bootstrap:
        for name in ('setup_tools.py','analysis_tools.py'):
            subprocess.run([sys.executable,str(HERE/name)],check=True)
    for name in ('verify.py','budget.py','verify_batch.py','verify_batch_rtl.py','verify_mailbox.py',
                 'prove_interval.py','prove_join.py','prove_compact.py','verify_driver.py',
                 'build_firmware.py','service_work.py','verify_isa.py','batch_budget.py','timing_residual.py','check_route_reuse.py',
                 'advance_budget.py','verify_advance.py','service_progress.py','service_budget.py',
                 'startup_check.py','startup_host_check.py'):
        subprocess.run([sys.executable,str(HERE/name)],check=True)
    if a.repeat_binary:
        before=hashlib.sha256((HERE/'outputs/rule-test.elf').read_bytes()).hexdigest()
        subprocess.run([sys.executable,str(HERE/'verify.py')],check=True)
        after=hashlib.sha256((HERE/'outputs/rule-test.elf').read_bytes()).hexdigest()
        if before!=after:raise RuntimeError('ARM ELF not reproducible across identical local builds')
        (HERE/'outputs/binary-repeat.json').write_text(json.dumps({'before':before,'after':after,'equal':True},indent=2)+'\n')
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),
                           '-p','test_*.py'],text=True,capture_output=True)
    (HERE/'outputs/tests.txt').write_text(tests.stdout+tests.stderr)
    if tests.returncode:raise RuntimeError(tests.stdout+tests.stderr)
    for path in HERE.glob('*.py'):py_compile.compile(str(path),doraise=True)
    if a.advance:
        subprocess.run([sys.executable,str(HERE/'run_advance.py')],check=True)
    subprocess.run([sys.executable,str(HERE/'run_advance.py'),'--check-published'],check=True)
    if a.integration:
        for phase,stress in ((0,0),(3,1),(11,2)):
            subprocess.run([sys.executable,str(HERE/'run_integration.py'),
                            '--phase',str(phase),'--stress',str(stress)],check=True)
        for stress in (3,4):
            subprocess.run([sys.executable,str(HERE/'run_integration.py'),
                            '--stress',str(stress),'--cycles','1000000'],check=True)
    for name in ('check_price.py','package_checks.py'):
        subprocess.run([sys.executable,str(HERE/name)],check=True)
    if a.full:
        from run_full import main as route
        build=route()
        subprocess.run([sys.executable,str(HERE/'collect_full.py'),str(build)],check=True)
    if a.ps7:
        out=HERE/'.build/ps7-probe'
        run=subprocess.run(['/home/z3tm4n/bin/vivado-wsl','-mode','batch','-nojournal','-nolog',
          '-source',str(HERE/'probe_ps7.tcl'),'-tclargs',str(out)],text=True,capture_output=True,cwd=ROOT)
        (HERE/'outputs/ps7-probe.txt').write_text(run.stdout+run.stderr)
        if run.returncode:raise RuntimeError('PS7 probe failed')
        (HERE/'outputs/ps7-configuration.txt').write_bytes((out/'configuration.txt').read_bytes())
    sources=['experiments/t104-rtl-resume/integrated/slow_rule.sv',
      'experiments/t104-rtl-resume/reference.py','experiments/t104-rtl-resume/physical/CONTRACT.md',
      'experiments/t104-rtl-resume/physical/VALIDATION.md','experiments/t104-rtl-resume/physical/bounds.py',
      'experiments/t104-rtl-resume/physical/outputs/bounds.json','experiments/t135-demo-operating-point/common-contract.json',
      'theory/t135-final-engineer-check.md','AGENTS.md','agents/00_RULES.md','agents/02_ENGINEER.md']
    manifest={'base':'3a8720ac389ffb9666eecedf7060f398d466b34e',
      'environment':{'python':sys.version,'platform':platform.platform(),
        'distribution':platform.freedesktop_os_release(),
        'native_gcc':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0]},
      'input_sha256':{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources},
      'task_sha256':{path.relative_to(HERE).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sorted(HERE.rglob('*')) if path.is_file() and
                    not any(part.startswith('.') or part=='__pycache__' for part in path.relative_to(HERE).parts)
                    and path.name!='manifest.json'}}
    (HERE/'outputs/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('T105 checkpoint reproduced: C0 startup/isolated address map checked; PS/OCM/GP completion upper remains OPEN.')

if __name__=='__main__':main()
