"""Small T88 pilot; never writes to accepted T82 outputs."""
from __future__ import annotations

from fractions import Fraction as F
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 't82-realistic-timing'))
import t80_engine as old
import t80_joint as joint
from t80_err import err_scan
from run_t80 import json_write


def main():
    variant = joint.source_check()[0]
    config = json.loads((HERE / 'config.json').read_text())
    rows = []
    for si in (1, 0):
        p = old.context(variant, config['margin'], 'internal38', si)
        for mode in ('combined', 'monitor-only', 'ERR-only'):
            q = dict(p, mode=mode)
            started = time.monotonic()
            if mode == 'ERR-only':
                records, best = err_scan(q)
                result = best or {'status': 'not_certified'}
                candidates = len(records)
            else:
                m = joint.window(q, F(10**6), F(1), F(1), F(2), 'total_load', 2)
                result = joint.best_direct(q, m)
                candidates = result['evaluated_candidates']
            row = dict(shield=p['shield'], mode=mode, Dstar=p['Dstar'],
                       elapsed_s=time.monotonic()-started, candidates=candidates,
                       result=result)
            rows.append(row)
            print(p['shield'], mode, row['elapsed_s'], candidates,
                  result.get('status'),
                  float(max(result.get('quiet_upper', F(0)), result.get('returns_upper', F(0)))), flush=True)
    out = HERE / 'outputs'
    out.mkdir(exist_ok=True)
    json_write(out / 'pilot.json', {'scope': 'accepted T82 baseline at D_min, g=131', 'rows': rows})


if __name__ == '__main__':
    main()
