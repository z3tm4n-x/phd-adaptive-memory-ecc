"""Recheck/publish one named full route, never select a favorable STA run."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'t104-rtl-resume/physical'
sys.path.insert(0,str(OLD))
from collect import timing,resources
from check_io import evaluate
from check_pins import plan,validate
from bounds import encode
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('build',type=Path);a=ap.parse_args()
    b=a.build.resolve();meta=json.loads((b/'manifest.json').read_text());assert meta['returncode']==0
    log=(b/'vivado.log').read_text();assert 'T105_FULL_ROUTE_COMPLETE' in log
    compiled=[x for x in meta['source_hashes'] if x.startswith('t105-arm-rule/') and Path(x).suffix in ('.sv','.tcl')]
    for x in compiled:assert digest(HERE.parent/x)==meta['source_hashes'][x],x
    io=b/'io'
    if not io.exists():
        with (b/'inspect-io.log').open('w') as f:
            run=subprocess.run([os.environ.get('VIVADO','/home/z3tm4n/bin/vivado-wsl'),'-mode','batch',
              '-nojournal','-nolog','-source',str(OLD/'inspect_io.tcl'),'-tclargs',str(b/'run/routed.dcp'),str(io)],
              cwd=b,stdout=f,stderr=subprocess.STDOUT,timeout=180)
        assert run.returncode==0,(b/'inspect-io.log').read_text()[-3000:]
    assert 'PHYSICAL_IO_INSPECTION_COMPLETE' in (b/'inspect-io.log').read_text()
    route=b/'run';t=timing(route/'timing.rpt');r=resources(route/'utilization.rpt')
    checks={k:int(v) for k,v in re.findall(r'checking (\w+) \((\d+)\)',(route/'check_timing.rpt').read_text())}
    assert len(checks)==12 and not any(checks.values())
    assert not re.search(r'\b(Critical|Warning)\b',(route/'cdc.rpt').read_text())
    assert not re.search(r'\|\s*Error\s*\|',(route/'drc.rpt').read_text())
    composition=evaluate(io);composition['late_memory_sentinel_rejected']=not evaluate(io,80)['all_met']
    assert composition['late_memory_sentinel_rejected']
    validate(plan(),(OLD/'board_pins.xdc').read_text(),(route/'io.rpt').read_text())
    out=HERE/'outputs';(out/'io.json').write_text(json.dumps(encode(composition),indent=2)+'\n')
    for folder,files in [('sta',list(route.glob('*.rpt'))+[route/'effective.xdc',route/'ps7-address-and-clocks.txt']),
                         ('io',list(io.glob('clocked_*.rpt')))]:
        dest=out/folder;dest.mkdir(exist_ok=True)
        for src in files:shutil.copyfile(src,dest/src.name)
    result={'raw_build':str(b),'top':'arm_board_top','part':'xc7z020clg484-1',
      'PL_MHz':[250,50],'PS_nominal_MHz':600,'uncertainty_ns':{'setup':.5,'hold':.1},
      'timing':t,'resources':r,'check_timing':checks,'CDC':'informational CDC-3 only',
      'DRC':'no errors; WRITE_FIRST advisories retained',
      'setup_margin_target_ns':.1,'STA_margin_target_met':t['setup_ns']>=.1 and t['hold_ns']>0,
      'external_io_all_met':composition['all_met'],
      'external_io_min_margin_ns':float(min(x['margin_ns'] for x in composition['checks'])),
      'pins':'same conditional FMC map checked; no new manufactured-board claim',
      'source_hashes':{x:meta['source_hashes'][x] for x in compiled},
      'checkpoint_sha256':digest(route/'routed.dcp'),'run_log_sha256':digest(b/'vivado.log'),
      'elapsed_s':meta['elapsed_s'],'peak_memory_MB':max(map(float,re.findall(r'Memory \(MB\): peak = ([\d.]+)',log))),
      'not_established':['ARM WCET','PS7 boot/BSP','full end-to-end10us','mean CPU/interface price'],
      'application_timing_shell':'unchanged B dynamic endpoints, NOT application software or mean R0-A workload'}
    (out/'full-top.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_hashes'},indent=2))
if __name__=='__main__':main()
