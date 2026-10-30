"""python experiments/article-intensity-comparison-20261030/reproduce.py [--check|--pilot]"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import platform
import sys
import time
from pathlib import Path
import calculation as c


def encoded(obj):
    return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def run():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--check',action='store_true',help='Rebuild in memory and compare all deterministic deliverables')
    group.add_argument('--pilot',action='store_true',help='One main row, no output mutation or figures')
    args=parser.parse_args()
    started=time.perf_counter()
    pilot=c.comparison_row(c.ACCEPTED['sensitivity'][8],9)
    pilot_time=time.perf_counter()-started
    if args.pilot:
        print(encoded(dict(pilot_seconds=pilot_time,row=pilot)).decode('utf-8'))
        return
    import checks
    tested=checks.run()
    compute_start=time.perf_counter()
    data=c.collect()
    compute_time=time.perf_counter()-compute_start
    data['checks']['directed_checks_passed']=tested
    assert [r['accepted'] for r in data['rows']]==c.ACCEPTED['sensitivity']
    import figures
    plot_start=time.perf_counter()
    plot_data=figures.datasets(data)
    artifacts={'outputs/results.json':encoded(data),
               'outputs/TABLE.md':c.table_markdown(data).encode('utf-8')}
    artifacts.update({f'outputs/{name}':encoded(content) for name,content in plot_data.items()})
    artifacts.update(figures.render(plot_data))
    figure_time=time.perf_counter()-plot_start
    provenance=dict(preregistration_commit=c.PREREGISTRATION,
        source_sha256_lf=c.CFG['source_sha256_lf'],
        code_sha256_lf={name:c.lf_hash(c.HERE/name) for name in
                        ('PLAN.md','inputs.json','README.md','RESULT.md','calculation.py','checks.py',
                         'figures.py','reproduce.py','requirements.txt')},
        output_hash_policy='JSON/Markdown/SVG canonical LF; PDF/PNG exact binary bytes',
        output_sha256={name:sha256(content).hexdigest() for name,content in artifacts.items()},
        rendering_versions=dict(python=platform.python_version(),matplotlib=figures.matplotlib.__version__,numpy=figures.np.__version__))
    artifacts['outputs/manifest.json']=encoded(provenance)
    if args.check:
        mismatches=[]
        for name,content in artifacts.items():
            path=c.HERE/name
            if not path.exists():
                mismatches.append(name+' (missing)')
                continue
            old=path.read_bytes()
            if path.suffix in ('.json','.md','.svg'):
                old=old.replace(b'\r\n',b'\n')
            if old!=content:
                mismatches.append(name)
        if mismatches:
            raise SystemExit('REPLAY MISMATCH: '+', '.join(mismatches))
        print(f'PASS: {len(data["rows"])} rows; {tested} directed checks; {len(artifacts)} matching deliverables (LF text; exact binary).')
    else:
        for name,content in artifacts.items():
            path=c.HERE/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(content)
        metadata=dict(recorded_utc=datetime.now(timezone.utc).isoformat(),
            python=sys.version,platform=platform.platform(),
            matplotlib=figures.matplotlib.__version__,numpy=figures.np.__version__,
            pilot_seconds=pilot_time,calculation_34_rows_seconds=compute_time,
            figure_data_and_9_exports_seconds=figure_time,
            total_seconds=time.perf_counter()-started,
            accepted_small16_recomputed=False,accepted_P_ref_recomputed=False,
            note='Wall time of this run, not a hardware WCET or an uncertainty estimate.')
        (c.HERE/'outputs/run_metadata.json').write_bytes(encoded(metadata))
        print(f'PASS: {len(data["rows"])} rows; {tested} directed checks; three figures in SVG/PDF/PNG.')
        print(json.dumps(metadata,ensure_ascii=False,indent=2))


if __name__=='__main__':
    run()
