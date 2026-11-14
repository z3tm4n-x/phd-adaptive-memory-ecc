"""Pinned repository sources. Export supports replay without a Git checkout."""
import ast
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NS = 10**9

def normalized(raw):
    return raw.replace(b'\r\n', b'\n')

def digest(raw):
    return hashlib.sha256(normalized(raw)).hexdigest()

def encoded(obj):
    return (json.dumps(obj, default=str, sort_keys=True, indent=2)+'\n').encode()

def ceil(x):
    x = F(x)
    return -(-x.numerator // x.denominator)

def load(export=None):
    manifest = json.loads((HERE/'manifest.json').read_bytes())
    for path, sha in manifest['source_sha256'].items():
        if digest((ROOT/path).read_bytes()) != sha:
            raise ValueError('Changed frozen source: '+path)
    raw = (ROOT/'experiments/hybrid-p-r-20261026/inputs.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest['input_sha256_raw']:
        raise ValueError('Changed canonical input bytes')
    inp = json.loads(raw)
    cfg = json.loads((ROOT/inp['fixed']['source']).read_bytes())
    hist = {}
    for alias, source in manifest['historical_sources'].items():
        raw = ((Path(export)/alias).read_bytes() if export else
               subprocess.check_output(['git','show',source['commit']+':'+source['path']],cwd=ROOT))
        if digest(raw) != source['sha256']:
            raise ValueError('Changed pinned dependency: '+alias)
        hist[alias] = normalized(raw).decode('utf-8')
    return manifest, inp, cfg, hist

def export_sources(target):
    _, _, _, hist = load()
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    for alias, source in hist.items():
        (target/alias).write_bytes(source.encode())

def functions_only(source, names, scope=None, wire=False):
    """Reuse exact pure functions, without starting historical experiments."""
    nodes = []
    for node in ast.parse(source).body:
        keep = isinstance(node, ast.FunctionDef) and node.name in names
        if wire:
            keep |= isinstance(node, ast.Import) and any(a.name=='struct' for a in node.names)
            keep |= isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CAUSE_BITS' for t in node.targets)
        if keep:
            nodes.append(node)
    env = dict(scope or {})
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'pinned-pure-functions','exec'),env)
    return env

def bindings(hist):
    wire = functions_only(hist['adapter.py'],{'canonical_causes','encode_record','decode_record'},wire=True)
    binding = functions_only(hist['binding_interface.py'],{'slot_start','close_counter'},{'F':F})
    return wire['encode_record'], wire['decode_record'], binding['close_counter']
