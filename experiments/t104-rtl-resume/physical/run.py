"""Snapshot all source dependencies before a routed or vendor-XPM run."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('mode',choices=['sta','sim','pads'])
    ap.add_argument('--phase',type=int,default=0)
    ap.add_argument('--stress',type=int,default=0)
    a=ap.parse_args()
    out=BASE/'.build'/('physical-'+a.mode+'-'+str(time.time_ns()))
    out.mkdir(parents=True)
    stage=out/'source'
    hashes={}
    for folder in ['physical','integrated','registered','split']:
        (stage/folder).mkdir(parents=True)
        for source in (BASE/folder).iterdir():
            if source.suffix in ['.sv','.xdc','.tcl']:
                data=source.read_bytes()
                target=stage/folder/source.name
                target.write_bytes(data)
                hashes[str(source.relative_to(BASE))]=hashlib.sha256(data).hexdigest()
    log=out/'vivado.log'
    script={'sta':'board_sta.tcl','sim':'sim.tcl','pads':'pad_sim.tcl'}[a.mode]
    args=[os.environ.get('VIVADO','/home/z3tm4n/bin/vivado-wsl'),'-mode','batch','-nojournal','-nolog',
          '-source',str(stage/'physical'/script),'-tclargs',str(out/'run')]
    if a.mode=='sim':args +=[str(a.phase),str(a.stress)]
    before=time.monotonic()
    print('BUILD',out,flush=True)
    with log.open('w') as f:
        r=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,cwd=out,timeout=2400)
    result={'source_hashes':hashes,'mode':a.mode,'phase':a.phase,'stress':a.stress,
            'command':args,'returncode':r.returncode,'elapsed_s':time.monotonic()-before,
            'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'build':str(out)}
    assert r.returncode==0,log.read_text()[-5000:]
    if a.mode=='sim':
        sys.path.insert(0,str(BASE))
        from integrated.check import check
        result['trace']=check(log)
    elif a.mode=='pads':
        import re
        m=re.search(r'PHYSICAL_PADS_COMPLETE requests=(\d+) max_response_ns=([\d.]+)',log.read_text())
        assert m,log.read_text()[-5000:]
        result['pad_test']={'requests':int(m[1]),'max_response_ns':float(m[2])}
    else:
        result['completed']='PHYSICAL_ROUTE_COMPLETE' in log.read_text()
        assert result['completed']
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['source_hashes','command']},indent=2),flush=True)
if __name__=='__main__':main()
