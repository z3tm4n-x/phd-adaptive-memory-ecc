"""One-time repository snapshots; no numerical campaign or accepted-file writes."""
from pathlib import Path
import hashlib, json, subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
norm=lambda b:b.replace(b'\r\n',b'\n')
sha=lambda b:hashlib.sha256(norm(b)).hexdigest()
assert not (HERE/'SOURCES.json').exists(), 'Do not silently refreeze inputs'
paths=[
 'experiments/hybrid-p-r-20261026/inputs.json',
 'experiments/hybrid-p-r-20261026/SERVICE.md',
 'experiments/hybrid-p-r-20261026/interface-price/INTERFACE.md',
 'experiments/hybrid-p-r-20261026/interface-price/interface.py',
 'experiments/t186-method-comparison/code-strength/common-input.json',
 'experiments/t186-method-comparison/code-strength/SERVICE.md',
 'experiments/t186-method-comparison/code-strength/comparison.py',
 'experiments/regime-map-methodology-20261019/epsilon-slice-20261027/theory/result.json',
 'experiments/regime-map-methodology-20261019/epsilon-slice-20261027/theory/check.py',
 'experiments/regime-map-methodology-20261019/epsilon-slice-20261027/theory/HANDOFF.md',
 'experiments/regime-map-methodology-20261019/epsilon-slice-20261027/REVIEW_20261027.md',
 'theory/hybrid-epsilon-repeat-20261027.md',
 'experiments/regime-map-methodology-20261019/epsilon-slice-20261027/cell-service/PLAN.md',
]
commit='469527882ea3a8f326286b34fd8aa14aea1bf71b'
upath='experiments/regime-map-methodology-20261019/epsilon-slice-20261027/count-price/result.json'
def blob(ref,path):return subprocess.check_output(['git','cat-file','blob',ref+':'+path],cwd=ROOT)
raw=norm(blob(commit,upath)); (HERE/'reference-C3.json').write_bytes(raw)
external={upath:dict(commit=commit,sha256=sha(raw),local_snapshot='reference-C3.json')}
for ref,path in [(commit,'theory/t196-count-error-price-20261027.md'),
 ('65dcceb57810b5ebf4ed393639c927a573ea6ecf','experiments/t186-method-comparison/stage4/adapter.py'),
 ('65dcceb57810b5ebf4ed393639c927a573ea6ecf','experiments/t186-method-comparison/stage4/CONDITIONS.md')]:
 external[path]=dict(commit=ref,sha256=sha(blob(ref,path)),use='read-only documentary reference; not needed to execute replay')
out=dict(base_main='c0864fff17eb1bdd28d66e81e4d9f7fc2acf4b22',plan_commit='899de7a7428788aded969295ce37c3077cdd9d7e',
 source_sha256={x:sha((ROOT/x).read_bytes()) for x in paths},external_references=external,
 input_and_all_PR281_settings_unchanged=True,old_A11_not_recomputed=True,
 status='PR281 accepted; PR283 published conditional C1-C5, no self acceptance')
(HERE/'SOURCES.json').write_bytes((json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
print('Frozen',len(paths),'current sources and C3 reference. No calculations run.')
