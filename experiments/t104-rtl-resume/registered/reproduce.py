"""Repeat or collect this checkpoint; never overwrites historical result files."""
import argparse,hashlib,json,os,platform,re,subprocess,sys,time,zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def slack(p):
    return float(re.search(r'Slack \((?:MET|VIOLATED)\)\s*:\s*([-\d.]+)ns',p.read_text()).group(1))
def timing(path):
    text=(path/'timing.rpt').read_text()
    row=re.search(r'WNS\(ns\)[^\n]*\n[^\n]*\n([^\n]+)',text).group(1).split()
    util=(path/'utilization.rpt').read_text()
    def resource(label): return float(re.search(r'\|\s*'+re.escape(label)+r'\s*\|\s*([\d.]+)',util).group(1))
    return {'all_ports_WNS_ns':float(row[0]),'all_ports_TNS_ns':float(row[1]),
      'all_ports_WHS_ns':float(row[4]),'all_ports_THS_ns':float(row[5]),
      'fast_register_setup_ns':slack(path/'fast_setup.rpt'),
      'fast_register_hold_ns':slack(path/'fast_hold.rpt'),
      'all_register_setup_ns':slack(path/'all_internal_setup.rpt'),
      'all_register_hold_ns':slack(path/'all_internal_hold.rpt'),
      'LUT':resource('Slice LUTs'),'FF':resource('Slice Registers'),'BRAM36_tiles':resource('Block RAM Tile'),
      'DSP':resource('DSPs'),
      'check_timing':re.findall(r'checking (\w+) \((\d+)\)',(path/'check_timing.rpt').read_text()),
      'ignored_exceptions': 'No ignored timing exceptions found.' not in (path/'ignored.rpt').read_text()}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--run',action='store_true',help='execute all tests and both routed grades before collecting')
    ap.add_argument('--vivado',default='/home/z3tm4n/bin/vivado-wsl')
    ap.add_argument('--minus1',type=Path)
    ap.add_argument('--minus2',type=Path)
    ap.add_argument('--baseline',type=Path)
    args=ap.parse_args()
    source_paths=[p for p in HERE.iterdir() if p.suffix in ('.py','.sv','.tcl')]
    initial_sources={p.name:sha(p) for p in source_paths}
    build=BASE/'.build'/('registered-delivery-'+str(time.time_ns()));build.mkdir(parents=True)
    def run(cmd,name,timeout=900):
        start=time.monotonic()
        with (build/(name+'.log')).open('w') as f:
            r=subprocess.run([str(x) for x in cmd],cwd=BASE.parents[1],stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        assert r.returncode==0,f'{name} failed: {build}/{name}.log'
        return {'elapsed_s':time.monotonic()-start,'log':str(build/(name+'.log'))}
    runs={}
    if args.run:
        runs['compileall']=run([sys.executable,'-X',f'pycache_prefix={build}/pycache','-m','compileall','-q',HERE],'compileall')
        for name in ('contract_check','prove_equivalence','prove_lane','prove_guard'):
            runs[name]=run([sys.executable,'-B',HERE/(name+'.py')],name)
        runs['simulation']=run([sys.executable,'-B',HERE/'verify.py','--vendor','--vivado',args.vivado],'simulation')
        runs['baseline']=run([sys.executable,'-B',BASE/'run.py','--rtl','--formal','--regression-A'],'baseline')
        args.baseline=build/'baseline.log'
        for grade in (1,2):
            out=build/f'grade-{grade}'
            runs[f'sta-{grade}']=run([args.vivado,'-mode','batch','-nojournal','-nolog','-source',HERE/'lane_sta.tcl',
                '-tclargs',f'xc7z020clg484-{grade}',out],f'sta-{grade}')
            runs[f'inspect-{grade}']=run([args.vivado,'-mode','batch','-nojournal','-nolog','-source',HERE/'inspect_routed.tcl',
                '-tclargs',out],f'inspect-{grade}')
            setattr(args,f'minus{grade}',out)
    assert args.minus1 and args.minus2 and args.baseline,'--run or all three existing evidence paths required'
    for arg in ('minus1','minus2','baseline'): setattr(args,arg,getattr(args,arg).resolve())
    checks=json.loads((HERE/'checks.json').read_text())
    eq=json.loads((HERE/'equivalence.json').read_text())
    lp=json.loads((HERE/'lane_proof.json').read_text())
    gp=json.loads((HERE/'guard_proof.json').read_text())
    # Bind each computed result to the implementation it really exercised.
    assert eq['source_sha256']==sha(HERE/'e_backend_registered.sv')
    assert lp['source_sha256']==sha(HERE/'operation_lane.sv')
    assert gp['source_sha256']==sha(HERE/'generation_guard.sv')
    for p in HERE.glob('*.sv'):
        if p.name in checks['sources']: assert checks['sources'][p.name]==sha(p),p
    assert all(x['status']=='proved' for x in eq['cases'][:2]) and eq['cases'][2]['status']=='disproved'
    assert lp['cases'][0]['status']=='proved' and lp['cases'][1]['status']=='disproved'
    assert gp['cases'][0]['status']=='proved' and gp['cases'][1]['status']=='disproved'
    assert len(checks['vendor'])==6 and sum(x['packets'] for x in checks['vendor'])==2160
    baseline=args.baseline.read_text()
    assert 'Ran 82 tests' in baseline and 'Ran 49 tests' in baseline and 'Elapsed:' in baseline
    metrics={'minus1':timing(args.minus1),'minus2':timing(args.minus2)}
    for m in metrics.values():
        assert all(int(n)==0 for _,n in m['check_timing']) and not m['ignored_exceptions']
    assert metrics['minus1']['fast_register_setup_ns']>=.1 and metrics['minus1']['fast_register_hold_ns']>=0
    # These failed port-level results are deliberately retained, not made PASS.
    metrics['status']='FAST_INTERNAL_CHECKPOINT_ONLY_FULL_B_OPEN'
    (HERE/'sta.json').write_text(json.dumps(metrics,indent=2)+'\n')
    shared=['split/async_queue.sv','split/slow_queue.sv','split/clock_250_50.sv',
      'split/clocked_lane.sv','split/component_input.xdc','split/tb_lane.sv','split/check.py',
      'split/formal_vendor_boundary.sv','rtl/e_backend.sv','reference.py','pdr_check.py']
    sources={p.relative_to(BASE).as_posix():sha(p) for p in HERE.iterdir() if p.suffix in ('.py','.sv','.tcl')}
    sources.update({p:sha(BASE/p) for p in shared})
    evidence={}
    for label,path in [('minus1',args.minus1),('minus2',args.minus2)]:
        for p in path.iterdir():
            if p.suffix in ('.rpt','.xdc') or p.name=='internal_slack.txt': evidence[f'{label}/{p.name}']=p
    evidence['baseline.log']=args.baseline
    for label,record in [('equivalence',eq),('lane',lp),('guard',gp),('simulation',checks)]:
        for p in Path(record['build']).glob('*.log'): evidence[f'{label}/{p.name}']=p
    output_names=['checks.json','equivalence.json','lane_proof.json','guard_proof.json','contract.json','sta.json']
    manifest={'base_sha':'5498bf5790cc8f90a26cc3a556e64768d31cbdbf',
      'instructions_sha':'68982b44ea7b1eb52c7b608b4a16a86c05a2f347',
      'theory_sha':'71fa4680d1e737bb1fb3b0cce31ee24cec410f4a',
      'sources_sha256':sources,'outputs_sha256':{p:sha(HERE/p) for p in output_names},
      'evidence_sha256':{name:sha(p) for name,p in evidence.items()},
      'environment':{'python':sys.version,'platform':platform.platform(),
        'yosys':subprocess.check_output(['yosys','-V'],text=True).strip(),
        'vivado':'2025.2, SW 6299465, IP 6300035 (full version in evidence logs)'},
      'runs':runs,'baseline_elapsed_s':float(re.search(r'Elapsed: ([\d.]+)s',baseline).group(1)),
      'scope':'registered lane; not whole executor, pad timing, LOW composition, or qualification'}
    with zipfile.ZipFile(HERE/'evidence.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,p in sorted(evidence.items()):
            item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(item,p.read_bytes())
    manifest['evidence_archive_sha256']=sha(HERE/'evidence.zip')
    manifest['evidence_archive_bytes']=(HERE/'evidence.zip').stat().st_size
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert initial_sources=={p.name:sha(p) for p in source_paths},'source changed during delivery'
    print(json.dumps({'metrics':metrics,'archive_bytes':manifest['evidence_archive_bytes'],'build':str(build)},indent=2))

if __name__=='__main__': main()
