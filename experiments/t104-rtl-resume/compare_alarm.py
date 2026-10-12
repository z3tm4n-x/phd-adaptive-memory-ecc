"""Read-only extraction of the bounded alarm-short cycle, both speed grades."""
import argparse
from collections import defaultdict
import csv
import io
import json
from pathlib import Path
import re
import zipfile

from audit_sta import audit
from compare_sta import cdc_groups, detail_summary, digest, paths, reports, DETAIL_FILES

HERE = Path(__file__).resolve().parent
BASE = '3a3656bdf09b7e99fd5f1de2baabb1b55e6a905d'
SERIES = HERE/'outputs/sta/alarm-short-01'
PARTS = ['xc7z020clg484-1', 'xc7z020clg484-2']
FILES = (*DETAIL_FILES, 'setup.tsv', 'adjacent_gate.rpt', 'fanout.tsv')


def skew_summary(text):
    actual = [float(v) for v in re.findall(r'Actual Bus Skew:\s*(-?[\d.]+)ns', text)]
    slacks = [float(v) for v in re.findall(r'^Slack \((?:MET|VIOLATED)\)\s*:\s*(-?[\d.]+)ns', text, re.M)]
    requirement = {float(v) for v in re.findall(r'Requirement:\s*([\d.]+)ns', text)}
    if not actual or len(actual) != len(slacks) or requirement != {2.0}:
        raise ValueError('incomplete/changed skew constraint')
    if any(abs(2-a-s) > 0.0011 for a, s in zip(actual, slacks)):
        raise ValueError('skew slack/sign contradiction')
    return dict(requirement_ns=2.0, worst_actual_ns=max(actual), worst_slack_ns=min(slacks),
                scope='conservative union of both Gray copies')


def setup_summary(detail, timing):
    rows = list(csv.DictReader(io.StringIO(detail['setup.tsv']), delimiter='\t'))
    if len(rows) != timing['setup_failing_endpoints'] or len({r['end'] for r in rows}) != len(rows):
        raise ValueError('setup endpoint coverage/uniqueness')
    values = [float(r['slack_ns']) for r in rows]
    if min(values) != timing['WNS_ns'] or max(values) >= 0:
        raise ValueError('setup sign/worst mismatch')
    if abs(sum(values)-timing['TNS_ns']) > (len(rows)+1)*0.0005:
        raise ValueError('setup total inconsistent with report resolution')
    groups = defaultdict(list)
    for row in rows:
        groups[row['group']].append(float(row['slack_ns']))
    return [dict(clock=k, failing_endpoints=len(v), worst_ns=min(v),
                 sum_printed_slacks_ns=round(sum(v), 3)) for k, v in sorted(groups.items())]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--detail-dirs', type=Path, nargs=2)
    p.add_argument('--write', action='store_true')
    args = p.parse_args()
    before = audit(PARTS[0], HERE/'outputs/sta/config-load-01', BASE)
    baseline = json.loads((HERE/'outputs/sta/config-load-01'/PARTS[0]/'summary.json').read_text())
    results, source_sets = [], []
    for index, part in enumerate(PARTS):
        target = SERIES/part
        checked = audit(part, SERIES)
        summary = json.loads((target/'summary.json').read_text())
        source_sets.append(summary['source_sha256'])
        changed = sorted(k for k, v in baseline['source_sha256'].items() if summary['source_sha256'].get(k) != v)
        if changed != ['rtl/permission_gate.sv'] or set(baseline['source_sha256']) != set(summary['source_sha256']):
            raise ValueError('unexpected RTL/constraint difference from 3a3656b')
        archive = target/'detail.zip'
        if args.write:
            if not args.detail_dirs:
                raise ValueError('--write requires both completed detail directories')
            directory = args.detail_dirs[index]
            checkpoint = Path(summary['raw_directory'])/'routed.dcp'
            if digest(checkpoint.read_bytes()) != summary['routed_checkpoint_sha256']:
                raise ValueError('wrong routed checkpoint')
            if archive.exists():
                with zipfile.ZipFile(archive) as z:
                    if set(z.namelist()) != set(FILES) or any(z.read(n) != (directory/n).read_bytes() for n in FILES):
                        raise ValueError('refusing to overwrite different checkpoint detail')
            else:
                with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
                    for name in FILES:
                        z.writestr(name, (directory/name).read_bytes())
        detail = reports(archive)
        if set(detail) != set(FILES):
            raise ValueError('incomplete detail archive')
        original = reports(target/'reports.zip')
        results.append(dict(part=part, audit=checked,
                            setup_groups=setup_summary(detail, checked['timing']),
                            hold_gray=detail_summary(detail, checked['timing']),
                            cdc_groups=cdc_groups(original['cdc.rpt']),
                            gray_bus_skew=skew_summary(original['bus_skew.rpt']),
                            memory_paths=paths(original['memory_paths.rpt']),
                            adjacent_gate_paths=paths(detail['adjacent_gate.rpt']),
                            high_fanout=list(csv.DictReader(io.StringIO(detail['fanout.tsv']), delimiter='\t')),
                            detail_sha256=digest(archive.read_bytes()),
                            checkpoint_sha256=summary['routed_checkpoint_sha256']))
    if source_sets[0] != source_sets[1]:
        raise ValueError('different RTL/XDC between speed grades')
    primary = results[0]['audit']
    result = dict(baseline_commit=BASE, changed_implementation_inputs=['rtl/permission_gate.sv'],
                  constraints_unchanged=True, same_RTL_XDC_both_parts=True, before=before,
                  primary_delta={k: round(primary['timing'][k]-before['timing'][k], 3)
                                 for k in ('WNS_ns', 'TNS_ns', 'WHS_ns', 'THS_ns')},
                  results=results, detail_script_sha256=digest((HERE/'alarm_detail.tcl').read_bytes()),
                  scope='report transfer/extraction verification, not a second STA engine')
    output = SERIES/'comparison.json'
    if args.write:
        output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    elif json.loads(output.read_text()) != result:
        raise ValueError('published alarm comparison differs')
    print(json.dumps(dict(delta=result['primary_delta'],
                          results=[dict(part=r['part'], timing=r['audit']['timing'],
                                        resources=r['audit']['resources'], groups=r['setup_groups'],
                                        hold_gray=r['hold_gray'], critical=r['memory_paths'][0])
                                   for r in results]), indent=2))


if __name__ == '__main__':
    main()
