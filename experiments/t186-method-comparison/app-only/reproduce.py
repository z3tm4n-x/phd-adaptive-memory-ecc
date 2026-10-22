"""Short source-pinned app-only check, with an explicit #196 gate."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

from app_only import evaluate
from app_checks import run as check

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ACCEPTED=HERE.parent/'code-strength'


def digest(raw):return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()


def encode(data):
    def default(x):
        if isinstance(x,F):return str(x)
        raise TypeError(type(x).__name__)
    return (json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True,default=default)+'\n').encode('utf-8')


def build():
    manifest=json.loads((HERE/'sources.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        if digest((ROOT/entry['path']).read_bytes())!=entry['sha256']:
            raise ValueError('source changed: '+entry['path'])
    raw=(ACCEPTED/'common-input.json').read_bytes();cfg=json.loads(raw)
    basis=json.loads((HERE/'basis.json').read_text(encoding='utf-8'))
    if digest(raw)!=basis['common_input_sha256']:raise ValueError('basis input binding mismatch')
    accepted=json.loads((ACCEPTED/'outputs/results.json').read_text(encoding='utf-8'))
    result=evaluate(cfg,basis,accepted)
    validation=check(cfg,basis,accepted,result)
    result.update(common_input_sha256=digest(raw),sources=manifest,
                  implementation_sha256={p.name:digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))})
    return {'result.json':encode(result),'validation.json':encode(validation)},result,validation


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--record',action='store_true')
    p.add_argument('--require-basis',action='store_true')
    args=p.parse_args();files,result,validation=build()
    if args.require_basis and result['Q_upper'] is None:
        print(json.dumps(dict(status=result['status'],reason='specific #196 basis is pending; no new Q or full price evaluated'),indent=2))
        return 2
    out=HERE/'outputs';out.mkdir(exist_ok=True)
    for name,raw in files.items():
        if args.record:(out/name).write_bytes(raw)
        elif (out/name).read_bytes().replace(b'\r\n',b'\n')!=raw:raise ValueError('output mismatch: '+name)
    print(json.dumps(dict(status=result['status'],checks=validation['count'],risk_evaluated=validation['risk_evaluated'],
                         output_sha256={n:digest(b) for n,b in files.items()}),indent=2))
    return 0


if __name__=='__main__':sys.exit(main())
