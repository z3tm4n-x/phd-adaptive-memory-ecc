"""Publish bounded evidence from explicitly named runs, never choose best STA.

Raw traces, checkpoints and vendor sources remain in ignored .build. This is
packaging, not a proof engine. verify.py recomputes the independent checks.
"""
import argparse, hashlib, json, platform, re, shutil, subprocess, zipfile
from pathlib import Path
from bounds import calculate, encode
from check_io import evaluate
from check_pins import plan, validate

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
REPO=BASE.parents[1]
COMPILED=[
 'split/async_queue.sv','split/slow_queue.sv','split/clock_250_50.sv',
 'registered/handshake_channel.sv','integrated/event_fifo.sv','integrated/slow_rule.sv',
 *['physical/'+x for x in ['e_backend_registered.sv','segmented_counter.sv',
 'candidate_link.sv','frame_engine.sv','executor.sv','address_map.sv','top.sv','board_top.sv',
 'board_sta.tcl','board_pins.xdc']], 'split/component_input.xdc']

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def git_command():
 # A Git-for-Windows worktree may contain a C:/... gitdir while this
 # read-only collector runs in WSL. Do not rewrite its metadata.
 args=['git'];marker=REPO/'.git'
 if marker.is_file():
  target=marker.read_text().removeprefix('gitdir: ').strip().replace('\\','/')
  if platform.system()=='Linux' and re.match(r'^[A-Za-z]:/',target):
   target='/mnt/'+target[0].lower()+target[2:]
   args+=['--git-dir',target,'--work-tree',str(REPO)]
 return args
def write(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def timing(p):
 text=p.read_text()
 m=re.search(r'(?m)^\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+(\d+)\s*$',text)
 assert m,p
 return {'setup_ns':float(m[1]),'hold_ns':float(m[5]),'pulse_width_ns':float(m[9]),
         'setup_failing_endpoints':int(m[3]),'hold_failing_endpoints':int(m[7]),
         'pulse_failing_endpoints':int(m[11])}
def resources(p):
 text=p.read_text()
 def val(name):return float(re.search(r'\|\s*'+re.escape(name)+r'\s*\|\s*([\d.]+)',text)[1])
 return {k:val(n) for k,n in [('LUT','Slice LUTs'),('slice_FF','Slice Registers'),
 ('IOB_FF','IOB Flip Flops'),('ILOGIC','ILOGIC'),('OLOGIC','OLOGIC'),
 ('BRAM36_equiv','Block RAM Tile'),('BUFG','BUFGCTRL'),('MMCM','MMCME2_ADV'),('DSP','DSPs')]}

def main():
 p=argparse.ArgumentParser();p.add_argument('--runs',type=Path,default=HERE/'evidence_runs.json')
 p.add_argument('--output',type=Path,default=HERE/'outputs');a=p.parse_args()
 config=read(a.runs);build=BASE/'.build';out=a.output
 selected=build/config['sta'];raw=read(selected/'summary.json');route=selected/'run'
 assert raw['returncode']==0 and raw['completed']
 for name in COMPILED:assert digest(BASE/name)==raw['source_hashes'][name],name
 sta=timing(route/'timing.rpt')
 assert sta['setup_ns']>=.1 and sta['hold_ns']>0
 assert all(sta[k]==0 for k in ['setup_failing_endpoints','hold_failing_endpoints','pulse_failing_endpoints'])
 checks={k:int(v) for k,v in re.findall(r'checking (\w+) \((\d+)\)',(route/'check_timing.rpt').read_text())}
 assert len(checks)==12 and not any(checks.values())
 assert not re.search(r'\b(Critical|Warning)\b',(route/'cdc.rpt').read_text())
 drc=(route/'drc.rpt').read_text();assert not re.search(r'\|\s*Error\s*\|',drc)
 summary={'part':'xc7z020clg484-1','top':'board_top','frequency_MHz':[250,50],
 'uncertainty_ns':{'setup':.5,'hold':.1},'timing':sta,'resources':resources(route/'utilization.rpt'),
 'check_timing':checks,'elapsed_s':raw['elapsed_s'],'log_sha256':raw['log_sha256'],
 'peak_memory_MB':max(map(float,re.findall(r'Memory \(MB\): peak = ([\d.]+)',(selected/'vivado.log').read_text()))),
 'compiled_inputs':{x:raw['source_hashes'][x] for x in COMPILED},
 'DRC':'2 warnings PLBUFGOPT-1/ZPS7-1 and3 WRITE_FIRST advisories; no errors; see report dispositions',
 'CDC':'16 informational CDC-3; standard XPM exceptions, no warning/critical',
 'raw_run':str(selected),'checkpoint_sha256':digest(route/'routed.dcp')}
 write(out/'sta.json',summary)
 # Bounded complete reports, not only favorable paths or rewritten excerpts.
 for source in [*route.glob('*.rpt'),route/'effective.xdc']:
  target=out/'sta'/source.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
 io=build/config['io'];composition=evaluate(io)
 assert composition['all_met'] and not evaluate(io,80)['all_met']
 composition['late_memory_sentinel_rejected']=True
 write(out/'io.json',encode(composition))
 for source in io.glob('clocked_*.rpt'):
  target=out/'io'/source.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
 pins=read(build/'final-pins.json');validate(plan(),(HERE/'board_pins.xdc').read_text(),(route/'io.rpt').read_text())
 assert pins['io_report_SHA256']==digest(route/'io.rpt')
 write(out/'pins.json',pins);write(out/'bounds.json',encode(calculate()))
 proof_folders={label:build/folder for label,folder in config['proofs'].items()}
 for label,folder in proof_folders.items():write(out/'proofs'/(label+'.json'),read(folder/'summary.json'))
 for label,prefix in [('components','integrated-proof-'),('guard','integrated-guard-'),('admission','integrated-admission-')]:
  dirs=list((build/config['components']/'.build').glob(prefix+'*'));assert len(dirs)==1
  proof_folders[label]=dirs[0]
  write(out/'proofs'/(label+'.json'),read(dirs[0]/'summary.json'))
 archive_hashes={}
 with zipfile.ZipFile(out/'proof_logs.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for label,folder in sorted(proof_folders.items()):
   for f in sorted(folder.iterdir()):
    if f.is_file() and f.suffix in ['.log','.sv','.json','.ys']:
     name=label+'/'+f.name;data=f.read_bytes();archive_hashes[name]=hashlib.sha256(data).hexdigest()
     zi=zipfile.ZipInfo(name,date_time=(2026,10,12,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED
     z.writestr(zi,data)
 write(out/'proof_archive.json',archive_hashes)
 if 'verification' in config:
  folder=build/config['verification'];v=read(folder/'summary.json')
  write(out/'tests.json',{k:v[k] for k in ['tests','unit_tests_total','compiled_python_files','elapsed_s','status']})
  for f in folder.glob('*-tests.log'):
   target=out/'tests'/f.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
 sims=[]
 for folder in config['simulations']:
  s=read(build/folder/'summary.json')
  for name in COMPILED:
   # board_sta is not executed by simulations, but all chosen inputs match.
   assert s['source_hashes'][name]==raw['source_hashes'][name],(folder,name)
  sims.append({k:v for k,v in s.items() if k not in ['source_hashes','command']})
 write(out/'simulations.json',sims)
 diagnostics=[]
 for folder in config.get('diagnostic_routes',[]):
  f=build/folder
  diagnostics.append({'run':folder,**timing(f/'run/timing.rpt'),
    'log_sha256':digest(f/'vivado.log'),'not_selected_by_collector':folder!=config['sta']})
 write(out/'route_history.json',diagnostics)
 # SHA-lock all actual inherited files and reference material, not mutable main.
 inherited=[x for x in COMPILED if not x.startswith('physical/')]
 references=['experiments/t68-v21-inputs/contracts.md',
 'experiments/t68-v21-inputs/inputs/article-cy62167-v21.docx',
 'experiments/RE-CY62167-ADDRESS-MAPPING-01/REPORT.md',
 'experiments/RE-CY62167-ADDRESS-MAPPING-01/w32seq_scenario.json']
 baseline={}
 for name in [str((BASE/x).relative_to(REPO)).replace('\\','/') for x in inherited]+references:
  original=subprocess.check_output(git_command()+['show',config['base_commit']+':'+name],cwd=REPO)
  actual=(REPO/name).read_bytes();assert original==actual,name
  baseline[name]=hashlib.sha256(actual).hexdigest()
 write(out/'provenance.json',{'commits':{k:config[k] for k in ['base_commit','instructions','read_main','theory_r4']},
  'environment':{'python':platform.python_version(),'platform':platform.platform(),
   'yosys':subprocess.check_output(['yosys','-V'],text=True).strip(),
   'iverilog':subprocess.run(['iverilog','-V'],text=True,capture_output=True).stdout.splitlines()[0],
   'Vivado':'2025.2 Build6299465, production -1 speedfile1.12 (2019-11-22)'},
  'inherited_byte_identical':baseline,'checkpoint_in_git':False,
  'raw_location':str(build),'packaging_does_not_rerun_proofs':True})
 # Documentation and source code are Git-versioned; avoid a circular hash of
 # this manifest. Evidence hash verification works without Vivado or raw runs.
 hashes={str(x.relative_to(out)).replace('\\','/'):digest(x) for x in sorted(out.rglob('*'))
         if x.is_file() and x.name!='SHA256.json'}
 write(out/'SHA256.json',hashes)
 print(json.dumps({'out':str(out),'files':len(hashes),'timing':sta,'resources':summary['resources']},indent=2))
if __name__=='__main__':main()
