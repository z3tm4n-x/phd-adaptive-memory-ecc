"""One-time registration of epsilon-only inputs and unchanged repository sources."""
import hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
INPUT='experiments/hybrid-p-r-20261026/inputs.json'
def sha(raw): return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()
def encode(x): return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

if __name__=='__main__':
    if (HERE/'manifest.json').exists(): raise SystemExit('Already frozen; do not silently regenerate')
    paths=[INPUT,'experiments/t186-method-comparison/code-strength/common-input.json',
      'experiments/t186-method-comparison/code-strength/SERVICE.md',
      'theory/hybrid-p-r-20261026.md','theory/hybrid-p-r-accumulated-reserve-20261026.md',
      'experiments/hybrid-p-r-20261026/interface-price/price.py',
      'experiments/hybrid-p-r-20261026/interface-price/PRICE.md',
      'experiments/hybrid-p-r-20261026/interface-price/result.json',
      'experiments/t114-two-stage-err/intervals.py',
      'experiments/regime-map-methodology-20261019/epsilon-slice-20261027/PLAN.md']
    paths += [str((HERE/n).relative_to(ROOT)).replace('\\','/') for n in ('PLAN.md','SETTINGS.md')]
    original=(ROOT/INPUT).read_bytes()
    assert hashlib.sha256(original).hexdigest()=='cc72a44914b0aa5547fe1e2b5a2a654c84573ab1c5fe6e35a4f4122831ec86c6'
    cases={}
    for i in range(1,5):
        data=json.loads(original); data['fixed']['epsilon']='1/'+str(10**i)
        name='input-1e-'+str(i)+'.json'; raw=encode(data); (HERE/name).write_bytes(raw)
        cases[name]=hashlib.sha256(raw).hexdigest()
    manifest=dict(base_main='430ebe46c4be584e402bf64bcd98836d62bcfb08',
        plan_commit='d7f1a9a71b6c6ddc921a56b0549a2eedd6c4a502',settings_commit='a6f55d0',
        canonical_input=INPUT,canonical_raw_sha256=hashlib.sha256(original).hexdigest(),
        source_sha256={path:sha((ROOT/path).read_bytes()) for path in paths},inputs_sha256=cases,
        only_scientific_change='fixed.epsilon',theory_coordination='https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/196#issuecomment-6434316712')
    (HERE/'manifest.json').write_bytes(encode(manifest))
    print('Frozen',len(paths),'sources and',len(cases),'epsilon-only inputs')
