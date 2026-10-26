"""Frozen repository-only sources; no old campaign replay."""
import ast
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NS = 10**9

def normalized(raw):
    return raw.replace(b'\r\n', b'\n')

def load(historical_root=None):
    manifest = json.loads((HERE/'manifest.json').read_bytes())
    for path, digest in manifest['source_sha256'].items():
        if hashlib.sha256(normalized((ROOT/path).read_bytes())).hexdigest() != digest:
            raise ValueError('Frozen source changed: '+path)
    raw = (HERE/manifest['canonical_input']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest['canonical_input_sha256']:
        raise ValueError('Agreed input changed')
    inp = json.loads(raw)
    cfg = json.loads((ROOT/inp['fixed']['source']).read_bytes())
    history = {}
    for path, data in manifest['historical_sources'].items():
        if historical_root:
            raw = (Path(historical_root)/Path(path).name).read_bytes()
        else:
            raw = subprocess.check_output(['git','show',data['commit']+':'+path],cwd=ROOT)
        if hashlib.sha256(normalized(raw)).hexdigest() != data['sha256']:
            raise ValueError('Historical source changed: '+path)
        history[Path(path).name] = raw.decode('utf-8')
    return manifest,inp,cfg,history

def wire_functions(source):
    """Load only unchanged wire functions; do not import/run old Adapter policies."""
    tree=ast.parse(source)
    names={'canonical_causes','encode_record','decode_record'}
    nodes=[n for n in tree.body if (
        isinstance(n,ast.Import) and any(a.name=='struct' for a in n.names))
        or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CAUSE_BITS' for t in n.targets))
        or (isinstance(n,ast.FunctionDef) and n.name in names)]
    scope={}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'frozen-stage4-wire','exec'),scope)
    return scope['encode_record'],scope['decode_record']

def intervals():
    spec=importlib.util.spec_from_file_location('interface_price_directed',ROOT/'experiments/t114-two-stage-err/intervals.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.I

def ceil(x):
    return -(-x.numerator//x.denominator)

def encoded(value):
    return (json.dumps(value,default=str,indent=2,sort_keys=True)+'\n').encode()
