"""Single candidate, four directed branches, full-T ledger. Standard library only."""
import argparse
from hashlib import sha256
from pathlib import Path
from sources import HERE,load,encoded,digest,export_sources
import risk,pilot,cost

def calculate(export=None):
    manifest,inp,cfg,hist=load(export)
    r=risk.calculate(inp,cfg,hist)
    cases=[pilot.run_case(name,inp,cfg,hist) for name in pilot.CASES]
    price=cost.calculate(inp,cfg,r,cases,hist)
    return dict(status='OWN_RESULT_CONDITIONAL_PILOT_NOT_SCIENTIFIC_OR_HARDWARE_ACCEPTANCE',
        input_sha256=manifest['input_sha256_raw'],plan_commit=manifest['plan_commit'],
        source_dependencies=manifest['historical_sources'],
        implementation_sha256={p:digest((HERE/p).read_bytes()) for p in
            ('sources.py','risk.py','pilot.py','cost.py','run.py','test_pilot.py')},
        risk=r,branches=cases,weak_E_witness=pilot.weak_E_witness(r['timing']['block_ticks']),cost=price,
        preserved_W_T_epsilon_and_input=True,no_new_transport=True,no_hardware_work=True,
        new_rule_search_or_parameter_sweep=False,
        remaining=['usable closed source/processed/health prefix including empty and lost tail',
            'mandatory service and pending=false; all-history bounded resource release',
            'per-packet WCET and finalization/install deadline',
            'lifetime delta_C coverage, not inferred from deterministic tests',
            'guard work and all CPU/energy/controller unit costs',
            'independent review of PR271/272; repeated economy is outside this pilot'])

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--historical-root')
    p.add_argument('--export-dependencies')
    p.add_argument('--write',action='store_true')
    p.add_argument('--check',action='store_true')
    a=p.parse_args()
    if a.export_dependencies:
        export_sources(a.export_dependencies)
    else:
        data=encoded(calculate(a.historical_root))
        if a.write:
            (HERE/'result.json').write_bytes(data)
        elif a.check:
            if data!=(HERE/'result.json').read_bytes():
                raise SystemExit('FAIL: result.json differs')
        else:
            print(data.decode(),end='')
        if a.write or a.check:
            print('Verified one candidate / four branches; result SHA256='+sha256(data).hexdigest())
