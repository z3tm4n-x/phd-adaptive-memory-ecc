"""Addressed negative/positive regressions for the failed full-profile stand."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(execute=False, record=False):
    from burst_codec import pack, digest
    from check_burst import check
    from burst_boundary import build
    from report_guard import publish_or_compare
    out = HERE/'outputs'
    folder = HERE/'.build/burst-repair'
    if execute:
        assert record
        folder.mkdir(parents=True, exist_ok=True)
        with (folder/'old-boundary.log').open('w') as log:
            bad = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--old-boundary-child'],
                                 stdout=log, stderr=subprocess.STDOUT)
        assert bad.returncode != 0, 'old boundary mutation was not rejected'
        old_run = max((HERE/'.build').glob('burst-boundary-fixed-1-*'), key=lambda p: p.stat().st_mtime_ns)
        old_log = (old_run/'vendor.log').read_text()
        assert 'Fatal: nonempty input/dirty word inside jump' in old_log, old_log[-2000:]
        negative = dict(rejected=True, returncode=bad.returncode,
            fatal='nonempty input/dirty word inside jump',
            vendor_log_sha256=sha(old_run/'vendor.log'))
        (folder/'negative.json').write_text(json.dumps(negative, indent=2)+'\n')
        for case, mode in (('boundary', 'fixed'), ('short', 'adaptive')):
            subprocess.run([sys.executable, str(HERE/'run_burst_v2.py'), '--case', case, '--mode', mode], check=True)
        with (folder/'time-format.log').open('w') as log:
            cmd = [os.environ.get('VIVADO', '/home/z3tm4n/bin/vivado-wsl'),
                   '-mode', 'batch', '-nolog', '-nojournal', '-source', str(HERE/'time_format.tcl'),
                   '-tclargs', str(folder)]
            subprocess.run(cmd, cwd=folder, stdout=log, stderr=subprocess.STDOUT, check=True)
        lines = [line for line in (folder/'time-format.log').read_text().splitlines() if line.startswith('FORMAT ')]
        (out/'burst-time-format.txt').write_text('\n'.join(lines)+'\n')
        (out/'burst-boundary-negative.json').write_text(json.dumps(negative, indent=2)+'\n')
    negative = json.loads((out/'burst-boundary-negative.json').read_text())
    assert negative['rejected'] and negative['fatal'] == 'nonempty input/dirty word inside jump'
    results = {}
    paths = [out/'burst-time-format.txt', out/'burst-boundary-negative.json']
    for case, mode in (('boundary', 'fixed'), ('short', 'adaptive')):
        stem = f'burst2-{case}-{mode}-skip'
        meta_path = out/(stem+'.json')
        meta = json.loads(meta_path.read_text())
        assert meta['stimulus'] == build(case)
        for p, h in meta['source_sha256'].items(): assert sha(REPO/p) == h, p
        trace = out/(stem+'.trace.ct3')
        if execute:
            pack(out/(stem+'.trace.ctz'), trace)
        assert digest(trace) == meta['trace_sha256']
        results[case] = check(trace, meta)
        paths += [meta_path, trace]
        if case == 'short':
            previous = json.loads((out/'burst-short-adaptive-skip.json').read_text())
            assert meta['trace_sha256'] == previous['trace_sha256'], 'unaffected short trace changed'
        else:
            assert results[case]['injections'] == 1 and results[case]['remaining_error_positions'] == 1
    formats = []
    for line in (out/'burst-time-format.txt').read_text().splitlines():
        _, ns, old, new = line.split(); ns, old, new = map(int, (ns, old, new))
        assert new == 1000*ns and new//1000 == ns
        formats.append(dict(ns=ns, old_ps=old, integer_ps=new, old_floor_error_ns=old//1000-ns))
    assert len(formats) == 5 and any(x['old_floor_error_ns'] for x in formats)
    paths += [HERE/p for p in ('verify_burst_repair.py', 'test_burst_boundary.py', 'tb_time_format.sv', 'time_format.tcl',
                              'BURST_REPAIR.md', 'report_guard.py')]
    report = dict(scope='technical stand regressions ONLY; full scenario2 not inferred',
        negative={k: v for k, v in negative.items() if k != 'vendor_log_sha256'}, results=results, time_formats=formats,
        sha256={p.relative_to(REPO).as_posix(): sha(p) for p in paths})
    publish_or_compare(out/'burst-repair-checks.json', report, record)
    print('Old boundary rejected; new boundary and unchanged short trace checked; integer time exact in XSim', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--execute', action='store_true'); p.add_argument('--record', action='store_true')
    p.add_argument('--old-boundary-child', action='store_true')
    a = p.parse_args()
    if a.old_boundary_child:
        from run_burst import execute, read_config
        from burst_boundary import build
        with patch('burst_run_inputs.build', build): execute('fixed', read_config(), 'boundary')
    else:
        main(a.execute, a.record)
