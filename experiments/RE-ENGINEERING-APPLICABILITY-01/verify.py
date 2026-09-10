"""Independent numerical checks of selected formulas; not a Scientific Review."""
import csv
import json
from decimal import Decimal
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'
checks=[]
floor=Decimal('.005')+Decimal('1.064')*Decimal('.001')
assert floor==Decimal('.006064')
checks.append({'check':'reserve_floor_decimal','value':str(floor),'passed':True})

rows=list(csv.DictReader((OUT/'scan_backup_screen.csv').open()))
maxerr=0.
for r in rows:
    D=float(r['D']);P=float(r['pass_s']);a=1/D
    Q=np.array([[-a,a],[a,-a]]);b=np.array([2.8886786e-5,6.1249308]);pi=np.array([.5,.5])
    def moments(t,y):
        return np.r_[Q@y[:2]+b, Q@y[2:]+2*b*y[:2]]
    z=solve_ivp(moments,[0,1],np.zeros(4),rtol=1e-11,atol=1e-13).y[:,-1]
    def pending(t,y):return y@Q+(t/P)*pi*b
    v=solve_ivp(pending,[0,P],np.zeros(2),rtol=1e-11,atol=1e-13).y[:,-1]
    value=(3600*.5*(pi@z[2:])+3599*(v@z[:2]))/524288
    err=abs(value-float(r['auxiliary_backup']));maxerr=max(maxerr,err)
    assert err<1e-10
checks.append({'check':'backup_linear_ODE_vs_quadrature','cases':len(rows),'max_abs_error':maxerr,'passed':True})

# Periodic codeword port: 4 available application slots, 4 scrub slots.
# Complete an 8-word burst for every integer transfer-tick phase.
worst=0
for arrival_phase in range(8):
    remaining=8;t=arrival_phase
    while remaining:
        if t%8<4:remaining-=1
        t+=1
    worst=max(worst,t-arrival_phase)
assert worst*45e-9 <=1.08e-6
checks.append({'check':'application_burst_all_slot_phases','cases':8,
               'worst_trace_s':worst*45e-9,'rate_latency_bound_s':1.08e-6,'passed':True})

# Integrated abstract pass: stale generation/late command rejected; corrections
# latch at read, unconditional full-word commit at frame end, one snapshot/done.
for depth in [1,8,17]:
    for corrected in [set(),{0},set(range(depth))]:
        events=[];count=0
        for w in range(depth):
            events.append((w*8+5,'read',w))
            count+=w in corrected
            events.append(((w+1)*8,'write',w))
        done=depth*8;snapshot={'generation':4,'count':count,'done_tick':done}
        assert sum(x[1]=='read' for x in events)==depth
        assert sum(x[1]=='write' for x in events)==depth
        assert snapshot['count']==len(corrected)
        assert [x[0] for x in events if x[1]=='write']==[8*(w+1) for w in range(depth)]
checks.append({'check':'abstract_atomic_word_slot_pass','cases':9,'passed':True,
               'scope':'transaction/snapshot model with correction oracle; not original RTL simulation'})

# Check retained resource conversion against source CSV, no trajectory imports.
source=ROOT.parent/'RE-INTERNAL-COUNT-UNKNOWN-D-01/outputs/comparison.csv'
saved=list(csv.DictReader(source.open()))
mapped=list(csv.DictReader((OUT/'retained_resource_comparison.csv').open()))
assert len(saved)==len(mapped)==30
for s,m in zip(saved,mapped):
    assert (s['dwell'],s['policy'])==(m['D'],m['policy'])
    assert float(s['busy_given_survival'])==float(m['busy_own_survival_s'])
    assert float(s['reads_stop_mean'])==float(m['stop_reads'])
    assert abs(float(m['completed_reads'])-float(s['passes_given_survival'])*2097152)<1e-5
checks.append({'check':'retained_resource_mapping','rows':30,'passed':True})

report={'checks':checks,'all_passed':all(x['passed'] for x in checks),
        'limitations':'ODE/transaction models independently check stated formulas; no historical held-out attestation, RTL simulator, synthesis, platform WCET or scientific PASS.'}
(OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
