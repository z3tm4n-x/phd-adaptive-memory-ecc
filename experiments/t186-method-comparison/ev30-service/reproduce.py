"""Standalone source-pinned replay; stdlib only, no Git/network at runtime."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
from checks import run
from service import evaluate, sensitivity

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()


def load_inputs():
    pins=json.loads((HERE/'sources.json').read_text(encoding='utf-8'))
    for path,meta in pins['local_sources'].items():
        if sha(ROOT/path)!=meta['sha256_LF']:
            raise ValueError('pinned source mismatch: '+path)
    if sha(HERE/'service-input.json')!=pins['input_sha256_LF']:
        raise ValueError('pinned service input mismatch')
    p=json.loads((HERE/'service-input.json').read_text(encoding='utf-8'))
    common=json.loads((HERE.parent/'code-strength/common-input.json').read_text(encoding='utf-8'))
    return p,common,pins


def encode(v):
    if isinstance(v,F):return str(v)
    raise TypeError(type(v).__name__)


def serialize(v):
    return (json.dumps(v,indent=2,ensure_ascii=False,default=encode)+'\n').encode('utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--record',action='store_true')
    parser.add_argument('--datasheet',type=Path)
    args=parser.parse_args()
    p,common,pins=load_inputs()
    if args.datasheet and hashlib.sha256(args.datasheet.read_bytes()).hexdigest()!=pins['datasheet']['sha256']:
        raise ValueError('datasheet bytes differ from source pin')
    result=evaluate(p,common)
    if not all(result['conditional_checks'].values()):
        raise ValueError('selected service violates a declared conditional constraint')
    result['sensitivity']=sensitivity(p,common)
    result['service_input_sha256_LF']=pins['input_sha256_LF']
    # Reference resource of the demonstrated codec, not a lower bound for t2.
    previous=json.loads((HERE.parent/'app-only/outputs/result.json').read_text(encoding='utf-8'))
    result['price']['demonstrated_codec_resources_reference']=previous['full_price']['codec_resources']
    result['price']['codec_reference_is_not_hardware_timing_evidence']=True
    outputs={'result.json':result,'checks.json':run(p,common)}
    output_dir=HERE/'outputs'
    if args.record:output_dir.mkdir(exist_ok=True)
    hashes={}
    for name,value in outputs.items():
        data=serialize(value);path=output_dir/name
        if args.record:path.write_bytes(data)
        elif path.read_bytes().replace(b'\r\n',b'\n')!=data:
            raise ValueError('output differs: '+name)
        hashes[name]=hashlib.sha256(data).hexdigest()
    print(json.dumps({'checks':outputs['checks.json']['passed'],'source_pins':len(pins['local_sources']),
                      'physical_Q_computed':False,'hashes':hashes},ensure_ascii=False))


if __name__=='__main__':main()
