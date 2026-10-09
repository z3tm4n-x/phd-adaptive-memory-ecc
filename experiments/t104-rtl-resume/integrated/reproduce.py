"""One bounded reproduction. STA failure is a reported result, NOT a PASS.

Writes new local build artifacts; --collect publishes one already completed
run into this task's own outputs after checking all tested-source hashes.
No historical package, scientific result, branch or Git state is modified.
"""
import argparse,hashlib,json,os,platform,re,subprocess,sys,time,zipfile
from pathlib import Path
from bounds import calculate,encode
from physical_audit import calculate as physical
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
VIVADO=os.environ.get('VIVADO','/home/z3tm4n/bin/vivado-wsl')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():
    files=list(HERE.glob('*.py'))+list(HERE.glob('*.sv'))+list(HERE.glob('*.tcl'))
    files += [BASE/'reference.py',BASE/'pdr_check.py',BASE/'split/component_input.xdc',
       BASE/'split/clock_250_50.sv',BASE/'split/async_queue.sv',BASE/'split/slow_queue.sv',
       BASE/'registered/e_backend_registered.sv',BASE/'registered/handshake_channel.sv']
    return {p.relative_to(BASE).as_posix():sha(p) for p in sorted(files)}
def write(p,data):p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def sta_result(folder):
    setup=(folder/'internal_setup.rpt').read_text();hold=(folder/'internal_hold.rpt').read_text()
    whole=(folder/'timing.rpt').read_text();util=(folder/'utilization.rpt').read_text()
    slack=lambda text:float(re.search(r'Slack\s*\([^)]*\)\s*:\s*(-?[\d.]+)ns',text)[1])
    row=re.search(r'^\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+\d+\s+\d+\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+\d+',whole,re.M)
    value=lambda name:float(re.search(r'\|\s*'+re.escape(name)+r'\s*\|\s*([\d.]+)',util)[1])
    return {'part':'xc7z020clg484-1','scope':'complete functional clocked_integrated; virtual I/O, NOT a physical pad top',
       'internal_setup_ns':slack(setup),'internal_hold_ns':slack(hold),
       'WNS_ns':float(row[1]),'TNS_ns':float(row[2]),'WHS_ns':float(row[3]),'THS_ns':float(row[4]),
       'LUT':value('Slice LUTs'),'FF':value('Slice Registers'),'BRAM36_equivalent':value('Block RAM Tile'),
       'DSP':value('DSPs'),'BUFG':value('BUFGCTRL'),'MMCM':value('MMCME2_ADV'),
       'setup_uncertainty_ns':.5,'hold_uncertainty_ns':.1,
       'internal_target_met':slack(setup)>=.1 and slack(hold)>=0,
       'physical_acceptance_established':False,
       'reports_sha256':{p.name:sha(p) for p in sorted(folder.glob('*.rpt'))},'raw_directory':str(folder)}
def run(build,label,command,timeout=900):
    print('RUN',label,flush=True);begin=time.monotonic()
    r=subprocess.run(command,cwd=BASE.parents[1],text=True,capture_output=True,timeout=timeout)
    log=r.stdout+r.stderr;(build/(label+'.log')).write_text(log)
    if r.returncode:raise RuntimeError(label+' failed:\n'+log[-6000:])
    print('DONE',label,round(time.monotonic()-begin,3),flush=True)
    return log
def collect(build):
    v=json.loads((build/'verification.json').read_text())
    assert v['tested_sources_sha256']==sources(),'tested source changed; do not attach stale evidence'
    out=HERE/'outputs';out.mkdir(exist_ok=True)
    for name in ('verification.json','bounds.json','physical.json'):
        (out/name).write_bytes((build/name).read_bytes())
    archive=HERE/'evidence.zip';members={}
    # Small, compressed textual evidence only: no DCP/XSim binaries, raw
    # vendor PDFs or unrelated datasets. The complete three traces are~26MB
    # text, compressed for direct independent replay without Vivado.
    for p in sorted(build.glob('*.log')):members['run/'+p.name]=p
    for n,r in enumerate(v['simulations']):members[f'simulation/{n}.log']=Path(r['log'])
    for n,r in enumerate(v['mutations']):members[f'mutation/{n}.log']=Path(r['log'])
    for name,r in [('formal',v['formal']),('guard',v['guard']),('admission',v['admission'])]:
        for p in sorted(Path(r['build']).iterdir()):
            if p.suffix in ('.log','.sv','.json'):members[name+'/'+p.name]=p
    if v['sta']:
        for p in sorted(Path(v['sta']['raw_directory']).iterdir()):
            if p.suffix in ('.rpt','.xdc'):members['sta/'+p.name]=p
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,p in sorted(members.items()):
            entry=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(entry,p.read_bytes(),compresslevel=9)
    assert archive.stat().st_size<10_000_000,'unexpectedly large evidence package'
    manifest={'parent_commit':'eab470df3c4a33b101aaa4eeab64c426b9f10aeb',
        'instructions_commit':'68982b44ea7b1eb52c7b608b4a16a86c05a2f347',
        'theory_initial':'b3bbc5f2171c66ac4b975060111aab704ab3734b',
        'theory_confirmation':'5147d0d360e7483fb421c9b5d11ff96ac216ef78',
        'delivery_commit':'the containing commit, pinned in PR134 and the user handoff; avoids self-hash recursion',
        'raw_run':str(build),'environment':v['environment'],
        'tested_sources_sha256':v['tested_sources_sha256'],
        'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),
        'archive_members_sha256':{name:sha(p) for name,p in sorted(members.items())},
        'files_sha256':{p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*'))
                       if p.is_file() and '.pyc'!=p.suffix and '__pycache__' not in p.parts
                       and p.name not in ('manifest.json','evidence.zip')},
        'limits':'only own integrated/ package; no scientific acceptance, physical top or complete STA PASS'}
    write(HERE/'manifest.json',manifest);print('PUBLISHED_LOCAL',archive,archive.stat().st_size,sha(archive))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sta',action='store_true');ap.add_argument('--collect',type=Path)
    a=ap.parse_args()
    if a.collect:collect(a.collect.resolve());return
    begin=time.monotonic();build=BASE/'.build'/('integrated-reproduce-'+str(time.time_ns()));build.mkdir(parents=True)
    initial_sources=sources()
    run(build,'unit_legacy',[sys.executable,'-B','-m','unittest','discover','-s',str(BASE),'-p','test_*.py'])
    run(build,'unit_integrated',[sys.executable,'-B','-m','unittest','discover','-s',str(HERE),'-p','test_*.py'])
    run(build,'compileall',[sys.executable,'-m','compileall','-q',str(HERE)])
    write(build/'bounds.json',encode(calculate()));write(build/'physical.json',physical())
    sims=[];mutants=[]
    for label,arguments in [('phase0',['--phase','0','--stress','0']),('phase1-burst',['--phase','1','--stress','1']),
        ('phase3-loss',['--phase','3','--stress','2']),('clocked',['--clocked']),
        ('stale-low',['--mutant','stale-low']),('third-credit',['--mutant','third-credit','--stress','1']),
        ('revoke-frozen',['--mutant','revoke-frozen'])]:
        log=run(build,label,[sys.executable,'-B',str(HERE/'check.py'),*arguments])
        path=Path(re.search(r'^LOG (.+)$',log,re.M)[1]).parent/'summary.json'
        result=json.loads(path.read_text());(mutants if '--mutant' in arguments else sims).append(result)
    log=run(build,'formal',[sys.executable,'-B',str(HERE/'prove.py')])
    formal=json.loads((Path(re.search(r'^BUILD (.+)$',log,re.M)[1])/'summary.json').read_text())
    for r in formal['cases']:
        if not r['case'].endswith('mutant'):assert r['status']=='proved',r
    guard=json.loads(run(build,'guard',[sys.executable,'-B',str(HERE/'guard_proof.py')]))
    admission=json.loads(run(build,'admission',[sys.executable,'-B',str(HERE/'admission_proof.py')]))
    assert guard['status']==admission['status']=='proved'
    sta=None
    if a.sta:
        run(build,'sta',[VIVADO,'-mode','batch','-nojournal','-nolog','-source',str(HERE/'sta.tcl'),
                 '-tclargs','xc7z020clg484-1',str(build/'sta'),'fast-floorplan'],timeout=1200)
        run(build,'sta-inspect',[VIVADO,'-mode','batch','-nojournal','-nolog','-source',str(HERE/'inspect_sta.tcl'),
                 '-tclargs',str(build/'sta/routed.dcp'),str(build/'sta/diagnostic')],timeout=180)
        sta=sta_result(build/'sta')
    environment={'python':sys.version,'platform':platform.platform(),
       'Vivado':run(build,'version-vivado',[VIVADO,'-version'],timeout=60).strip(),
       'Yosys':run(build,'version-yosys',['yosys','-V']).strip(),
       'Icarus':run(build,'version-iverilog',['iverilog','-V']).strip()}
    assert initial_sources==sources(),'sources changed during verification'
    result={'status':'functional integration checked; B NOT COMPLETE',
      'simulations':sims,'mutations':mutants,'formal':formal,'guard':guard,'admission':admission,
      'sta':sta,'environment':environment,'elapsed_s':time.monotonic()-begin,
      'tested_sources_sha256':initial_sources,'raw_build':str(build),
      'limits':['production top clock simulation and reduced-parameter long traces are distinct',
        'stress1 violates the T135 traffic/backpressure envelope; no3us assertion there',
        'network bounds conditional on vendor digital transport semantics and clock/startup contract',
        'not a complete unbounded proof of every payload/CDC liveness/pad behavior']}
    write(build/'verification.json',result);print('REPRODUCED',build,flush=True)
if __name__=='__main__':main()
