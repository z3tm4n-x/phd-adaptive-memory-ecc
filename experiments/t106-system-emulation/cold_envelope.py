"""Additional in-envelope realization of scenario4; historical run retained."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
from burst_run_inputs import build as original_build
from report_guard import publish_or_compare

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]


def build(case='cold-envelope',pilot_events=0):
    if case!='cold-envelope':return original_build(case,pilot_events)
    assert not pilot_events
    old=json.loads((HERE/'config.json').read_text())
    cfg=next(s for s in old['scenarios'] if s['id']==4)
    apps=[]
    for i in range(48):
        kind=2 if i%2==0 else 1
        mask=cfg['application']['write_masks_cycle'][(i//2)%5]
        word=400000+i//2
        packet=(i<<57)|(mask<<53)|((0x12340000|i)<<21)|(word<<2)|kind
        apps.append(dict(at_ns=10000+i*1_000_000,owner=i%2,packet=f'{packet:x}'))
    return dict(scenario=case,horizon_ns=48_000_000,initial_data='0xa5a50000 XOR word',
        initial_errors=0,injections=sorted(cfg['injections'],key=lambda x:(x['at_ns'],x['parent'])),
        applications=apps,false_ERR_interval_ns=[0,0],loss_slow_interval_ns=[0,0],
        ready_low_ns=80,ready_period_ns=340)


def verify(mode,execute=False,record=False):
    stem=f'burst-cold-envelope-{mode}-skip'
    if execute:
        from run_burst import execute as run,read_config
        # Injection point is the TEST input builder only, never firmware/RTL.
        # The unchanged runner imports it locally. Record this wrapper as source.
        with patch('burst_run_inputs.build',build):
            run(mode,read_config(),'cold-envelope')
    path=HERE/f'outputs/{stem}.json';meta=json.loads(path.read_text())
    assert meta['stimulus']==build()
    for p,h in meta['source_sha256'].items():
        assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
    from burst_codec import pack,digest
    from check_burst import check
    trace=HERE/f'outputs/{stem}.trace.ct3'
    if execute or not trace.exists():
        assert record
        pack(HERE/f'outputs/{stem}.trace.ctz',trace)
    assert digest(trace)==meta['trace_sha256']
    result=check(trace,meta)
    assert result['horizon_ns']==48000000 and result['application_completed']==48
    assert result['first_exceedance_relative_ns'] is None
    assert not any(x[1] or x[2] for x in result['permissions'])
    apps=build()['applications']
    assert all(b['at_ns']-a['at_ns']>=100000 for a,b in zip(apps,apps[1:]))
    assert 24/(result['horizon_ns']/1e9)<=1000
    sources=[path,trace]+[HERE/f for f in
        ('cold_envelope.py','COLD_ENVELOPE.md','check_burst.py','burst_price.py','burst_codec.py','report_guard.py')]
    report=dict(scope='scenario4 additional in-envelope cold-start; historical stress retained',
        results=result,sha256={p.relative_to(REPO).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        application_interval_ns=1000000,read_rate_per_s=500,write_rate_per_s=500,
        hardware_ARM_time_ns=None,Q_T_certified_by_emulation=False)
    dest=HERE/f'outputs/{stem}-checked.json'
    publish_or_compare(dest,report,record)
    print(json.dumps({k:result[k] for k in ('mode','mean_bus_fraction','peak_any_1ms_fraction',
        'application_completed','max_application_delay_ns','first_exceedance_relative_ns')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--record',action='store_true')
    p.add_argument('--mode',choices=['adaptive','fixed','both'],default='both');a=p.parse_args()
    for mode in (['adaptive','fixed'] if a.mode=='both' else [a.mode]):verify(mode,a.execute,a.record)
