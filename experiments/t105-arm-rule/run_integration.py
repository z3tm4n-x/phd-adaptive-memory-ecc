"""Vendor XPM + actual native rule C + AXI BFM. Not PS7/CPU execution time."""
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',type=int,default=0)
    ap.add_argument('--stress',type=int,default=0);args=ap.parse_args()
    build=HERE/'.build'/('integration-'+str(time.time_ns()));build.mkdir(parents=True)
    stage=build/'source';stage.mkdir()
    hashes={}
    for root in (HERE,HERE.parent/'t104-rtl-resume'):
        for source in root.rglob('*'):
            if any(p.startswith('.') or p=='outputs' for p in source.relative_to(root).parts):continue
            if source.suffix not in ('.sv','.tcl','.c','.h'):continue
            dest=stage/root.name/source.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(source.read_bytes());hashes[str(source.relative_to(HERE.parent))]=hashlib.sha256(source.read_bytes()).hexdigest()
    c=stage/'t105-arm-rule'
    # Explicit diagnostic acceleration, IN BUILD ONLY. Production header,
    # emitted ARM binary and tests of full-size boundaries are unchanged.
    header=(c/'rule.h').read_text()
    for old,new in [('4500045002','40'),('9000090002','80'),('9015504896','130')]:
        assert header.count(old)==1;header=header.replace(old,new)
    (c/'rule.h').write_text(header)
    subprocess.run(['gcc','-shared','-fPIC','-O2','-std=c11','-Wall','-Wextra','-Werror',
       *[str(c/f) for f in ('rule.c','batch.c','crc32.c','mailbox_dpi.c')],'-o',str(build/'dpi.so')],check=True)
    command=[os.environ.get('VIVADO','/home/z3tm4n/bin/vivado-wsl'),'-mode','batch','-nojournal','-nolog',
      '-source',str(c/'integration_sim.tcl'),'-tclargs',str(build/'xsim'),str(args.phase),str(args.stress),str(build)]
    print('BUILD',build,flush=True);before=time.monotonic()
    with (build/'vivado.log').open('w') as f:
        run=subprocess.run(command,cwd=build,stdout=f,stderr=subprocess.STDOUT,timeout=600)
    meta={'kind':'vendor-XPM/native-C functional composition; NOT CPU/PS7 timing',
          'build':str(build),'phase_ns':args.phase,'stress':args.stress,'elapsed_s':time.monotonic()-before,
          'source_hashes':hashes,'diagnostic_timers':{'NW':40,'NH':80,'NR':130,'PAIR':22500225010},
          'returncode':run.returncode}
    (build/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    log=(build/'vivado.log').read_text()
    assert run.returncode==0 and 'PASS ARM integrated' in log and 'Fatal:' not in log,log[-6000:]
    from check_integration import check
    result=check(build/'vivado.log');meta['check']=result
    (build/'summary.json').write_text(json.dumps(meta,indent=2)+'\n')
    (HERE/'outputs'/f'integration-{args.phase}-{args.stress}.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
