"""Run the bounded continuation without modifying any input package."""
from pathlib import Path
import argparse
from datetime import datetime,timezone
import hashlib
import json
import platform
import shutil
import sys
import numpy as np
import scipy
import mpmath
import numba
import checks_numeric,checks_word,checks_interface,checks_budget

ROOT=Path(__file__).resolve().parent


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--reference-root',type=Path,
        default=ROOT.parents[1]/'RE-INTERNAL-COUNT-UNKNOWN-D-01')
    ap.add_argument('--out',type=Path,default=ROOT/'outputs')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((ROOT/'config.json').read_text())
    source_paths=sorted(ROOT.glob('*.py'))+[ROOT/'config.json']
    own_before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    before={n:hashlib.sha256((args.reference_root/n).read_bytes()).hexdigest() for n in checks_budget.PIN}
    data={'numeric':checks_numeric.run(cfg),'word':checks_word.run(cfg),
          'interface':checks_interface.run(cfg),'budget':checks_budget.run(cfg,args.reference_root)}
    after={n:hashlib.sha256((args.reference_root/n).read_bytes()).hexdigest() for n in checks_budget.PIN}
    if before!=after: raise RuntimeError('Input bytes changed')
    own_after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    if own_before!=own_after: raise RuntimeError('Own source bytes changed during checks')
    for name,result in data.items():
        (args.out/(name+'.json')).write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    environment=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
        executor=cfg['executor'],python=sys.version,platform=platform.platform(),
        numpy=np.__version__,scipy=scipy.__version__,mpmath=mpmath.__version__,numba=numba.__version__,
        rtl_backends={n:shutil.which(n) for n in ['iverilog','vvp','verilator','yosys','vivado']},
        input_hashes_before=before,input_hashes_after=after,
        continuation_sources_sha256=own_before,continuation_sources_unchanged=own_before==own_after,
        command='OPENBLAS_NUM_THREADS=1 python run_checks.py --reference-root <pinned-package> --out <new-output>',
        executed=['deterministic local calculations','finite word/command/service checks','short accepted-kernel budget trace'],
        not_executed=['Monte Carlo','retuning','five-year replay','RTL simulation','synthesis','placement','hardware WCET'])
    (args.out/'execution.json').write_text(json.dumps(environment,indent=2)+'\n')
    print(json.dumps({k:{a:b for a,b in v.items() if a not in ['information','backup_rows','word_traces','trace','rule_comparisons']} for k,v in data.items()},indent=2))


if __name__=='__main__': main()
