"""Addressed author check of PR204, including a price-domain witness.

Usage: python -B check.py --source-root /path/to/exact-PR204-checkout
No mutation of the engineer's sources or accepted results.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.source_root.resolve()
    versions = json.loads((HERE/'versions.json').read_text())
    for item in versions['source_blobs']:
        data = (root/item['path']).read_bytes()
        got = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert got == item['sha'], (item['path'], got, item['sha'])
    p = root/'experiments/t186-method-comparison/stage4'
    sys.path.insert(0, str(p))
    from checks import exercise
    from loss_checks import validate_loss
    from adapter import Adapter
    from application import Application
    from grid import Grid
    from engine import run
    from bounds import calculate
    cfg = json.loads((p/'common-input.json').read_text())
    directed = validate_loss(cfg, exercise)
    bounds = calculate(cfg)
    spec = dict(id='our_r4', family='our')
    start, stop = 200_000_000_000, 200_040_000_000
    prefix = [dict(t=0, kind='GAP'), dict(t=4, kind='RESTORE')]
    events = prefix+[dict(t=t, kind='GAP', covers=[1, 1])
                     for t in range(start, stop, 4000)]
    a, trace = exercise(spec, cfg['delivery'], events, stop+16000)
    assert a.mode(start-4) == 3
    assert all(x['k'] == 1 for x in trace if start <= x['t'] < stop)
    assert a.losses == a.restores == a.source_losses == a.source_recoveries == 1
    assert a.gap_confirmations == 10000 and a.false == 0
    app = Application(cfg['application']['profiles'][0], cfg['application'],
                      Grid(cfg['memory']['words']))
    result = run(stop+16000, [], app, Adapter(spec, cfg['delivery']), faults=events)
    base = run(stop+16000, [], app, Adapter(spec, cfg['delivery']), faults=prefix)
    assert result['application'] == base['application']
    extra = result['bus']['total_ns']-base['bus']['total_ns']
    assert extra == 12518256
    counts = result['algorithm']
    keep = ('loss_rises', 'restores', 'raw_GAP_notifications',
            'raw_RESTORE_notifications', 'source_health_loss_rises',
            'source_health_recoveries', 'GAP_confirmations', 'source_false',
            'processed_G', 'current_G')
    out = dict(
        reviewed_head=versions['reviewed_head'], executable=versions['executable'],
        checked_blobs=len(versions['source_blobs']),
        scope='author applicability check, not independent review or full matrix repeat',
        engineer_loss_checks=directed['count'],
        cause_permutations=directed['evidence']['permutation_runs'],
        R1_first_ready_ns=7900, R1_restore_ready_ns=11900,
        R2_methods=[x['method'] for x in directed['evidence']['R2']],
        delivery_upper_ns=bounds['delivery_upper_ns'], queue=bounds['queue'],
        price_witness=dict(interval_ns=[start, stop], spacing_ns=4000,
                           production_timers=True, counts={k:counts[k] for k in keep},
                           extra_bus_ns=extra,
                           extra_control_operations=result['started_control_operations']-base['started_control_operations'],
                           no_new_NR=a.recovery == 7900+a.cfg['NR']*20,
                           final_k=a.k, final_UNKNOWN=a.unknown),
        full_price_scope=dict(
            old_OUR_upper=bounds['methods']['our_r4']['full_expected_SRAM_price_upper'],
            hard_envelope=bounds['methods']['patent_60']['full_expected_SRAM_price_upper'],
            nominal_FAST_base='23/49',
            limitation='unbounded extra source notifications are not bounded by episode counts'))
    text = json.dumps(out, ensure_ascii=False, sort_keys=True, indent=2)+'\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text, end='')


if __name__ == '__main__':
    main()
