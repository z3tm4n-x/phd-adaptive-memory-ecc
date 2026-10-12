"""Fast reproducible verification of the published evidence and regressions.

Does not impersonate a new Vivado/formal run. See REPRODUCE for those commands.
"""
import argparse, compileall, hashlib, json, re, subprocess, sys, time, zipfile
from pathlib import Path
from bounds import calculate, encode
from check_io import evaluate
from check_pins import plan, validate
from collect import COMPILED, digest, read, timing, resources, write
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
REPO=BASE.parents[1]

def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,default=HERE/'outputs');a=p.parse_args()
 out=a.evidence;started=time.monotonic();record=BASE/'.build'/('physical-verify-'+str(time.time_ns()))
 record.mkdir(parents=True)
 hashes=read(out/'SHA256.json')
 for name,value in hashes.items():assert digest(out/name)==value,name
 with zipfile.ZipFile(out/'proof_logs.zip') as z:
  members=read(out/'proof_archive.json');assert set(z.namelist())==set(members)
  for name,value in members.items():assert hashlib.sha256(z.read(name)).hexdigest()==value,name
 sta=read(out/'sta.json')
 for name in COMPILED:assert digest(BASE/name)==sta['compiled_inputs'][name],name
 for name,value in read(out/'provenance.json')['inherited_byte_identical'].items():
  assert digest(REPO/name)==value,name
 assert timing(out/'sta/timing.rpt')==sta['timing']
 assert resources(out/'sta/utilization.rpt')==sta['resources']
 assert sta['timing']['setup_ns']>=.1 and sta['timing']['hold_ns']>0
 # Compare every independently recomputed rational, not just a PASS flag.
 io=evaluate(out/'io');io['late_memory_sentinel_rejected']=not evaluate(out/'io',80)['all_met']
 assert encode(io)==read(out/'io.json') and io['all_met']
 assert io['late_memory_sentinel_rejected']
 assert encode(calculate())==read(out/'bounds.json')
 validate(plan(),(HERE/'board_pins.xdc').read_text(),(out/'sta/io.rpt').read_text())
 good_cases={'actual','normal','prevalidated','counter','frame','warmup','rule','slow-fast','fast-slow'}
 proof_count=0
 known_hashes=set(sta['compiled_inputs'].values())
 for f in (out/'proofs').glob('*.json'):
  data=read(f);cases=data.get('cases',[data]);proof_count+=1
  if 'source_sha256' in data:assert data['source_sha256'] in known_hashes,(f,data['source_sha256'])
  for row in cases:
   if row.get('case') in good_cases or 'case' not in row:
    assert row.get('proved') is True or row.get('status')=='proved' or row.get('passed') is True,(f,row)
   else:
    assert row.get('counterexample') is True or row.get('status')=='disproved' or row.get('passed') is False,(f,row)
  for sentinel in data.get('sentinels',[]):assert sentinel['counterexample']
  def check_logs(x):
   if isinstance(x,dict):
    for key,value in x.items():
     if key.endswith('log_sha256'):assert value in members.values(),(f,key,value)
     else:check_logs(value)
   elif isinstance(x,list):
    for item in x:check_logs(item)
  check_logs(data)
 tests=[]
 for folder in [BASE,BASE/'integrated',HERE]:
  command=[sys.executable,'-m','unittest','discover','-s',str(folder),'-p','test_*.py']
  r=subprocess.run(command,cwd=REPO,capture_output=True,text=True)
  log=r.stdout+r.stderr;(record/(folder.name+'-tests.log')).write_text(log)
  assert r.returncode==0,log
  count=int(re.search(r'Ran (\d+) tests',log)[1])
  tests.append({'directory':str(folder.relative_to(REPO)),'tests':count,'returncode':r.returncode,
                'log_sha256':hashlib.sha256(log.encode()).hexdigest()})
 # Do not recurse through many historical raw .build snapshots.
 compiled=0
 for f in BASE.rglob('*.py'):
  if '.build' not in f.parts:
   assert compileall.compile_file(str(f),quiet=1);compiled+=1
 result={'scope':'saved-evidence verification + fresh unit tests/compileall; no new STA or formal proof',
  'evidence_files_checked':len(hashes),'proof_summaries_checked':proof_count,
  'tests':tests,'unit_tests_total':sum(x['tests'] for x in tests),'compiled_python_files':compiled,
  'elapsed_s':time.monotonic()-started,'status':'completed'}
 write(record/'summary.json',result);print(json.dumps(result,indent=2));print(record)
if __name__=='__main__':main()
