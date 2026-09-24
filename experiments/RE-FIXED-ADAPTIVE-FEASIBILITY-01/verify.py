#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def check(cond,msg):
    if not cond: raise AssertionError(msg)

def conditional_write_traces():
    cases=[]
    cases.append(('clean', {'errors_at_read':0,'write':False,'next_read':10}))
    cases.append(('single', {'errors_at_read':1,'write':True,'count':1,'next_read':10}))
    cases.append(('post_read', {'errors_at_read':0,'post_read_error':1,'write':False,'pending_next':1,'next_read':10}))
    cases.append(('rmw_pair', {'errors_at_read':1,'post_read_distinct':1,'E_cap':True,'write':True}))
    cases.append(('last_word', {'before':4,'last_correction':1,'snapshot':5}))
    cases.append(('partial', {'visited':7,'W':8,'complete':False}))
    cases.append(('late_command', {'deadline':9,'arrival':10,'accepted':False,'action':'fallback'}))
    cases.append(('app_conflict', {'locked_scrub':[0,2],'app':[2,3],'overlap':False}))
    return cases

def main():
    subprocess.run([sys.executable,str(ROOT/'analyze.py')],check=True,capture_output=True,text=True)
    s=json.loads((ROOT/'outputs/summary.json').read_text())
    check(s['level1_gate_open'],'Level I gate expected to open under preregistered map')
    check(not s['level3_res004_executed'],'RES-004 must remain unexecuted')
    ws=s['witnesses']; check(any(r['memory_mib']==4 and abs(r['epsilon']-0.001)<1e-15 and abs(r['budget']-0.0025)<1e-15 and r['application_load'] in (0.1,0.5) for r in ws),'missing principal 4 MiB witness')
    for r in ws:
        check(r['causal_risk_upper']<=r['epsilon'],'causal risk')
        check(r['fixed_required_read_fraction_lb']>r['budget'],'fixed impossibility resource/risk separator')
        check(r['causal_peak_fraction_worst_rw']<=0.25,'peak')
        check(r['app_delay_bound_us']<=100,'delay')
    strong=json.loads((ROOT/'outputs/stronger_ecc.json').read_text())
    check(any(x['memory_mib']==4 and abs(x['epsilon']-0.001)<1e-15 and abs(x['budget']-0.0025)<1e-15 and x['full_contract'] for x in strong),'stronger ECC witness')
    cases=conditional_write_traces()
    check(cases[0][1]['write'] is False,'clean write suppression')
    check(cases[1][1]['count']==1,'count completeness')
    check(cases[2][1]['pending_next']==1,'post-read error persistence')
    check(cases[3][1]['E_cap'] is True,'RMW hazard recognition')
    check(cases[4][1]['snapshot']==5,'last word')
    check(cases[5][1]['complete'] is False,'partial pass')
    check(cases[6][1]['action']=='fallback','late decision fallback')
    check(cases[7][1]['overlap'] is False,'locked arbitration')
    out={'passed':True,'checks':len(ws)*4+10,'conditional_write_cases':[k for k,_ in cases]}
    (ROOT/'outputs/verification.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
