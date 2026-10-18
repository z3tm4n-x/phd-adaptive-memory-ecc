"""Directed and differential implementation checks; not scientific acceptance."""
from copy import deepcopy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import random
import sys
from engine import Grid,run
from policies import Constant,Our,Krasnikov,Patent,Chen,make,HOUR,NS,next_cut
from scenarios import digest,generate
from training import fit


def validate(cfg,root):
    items=[]
    def ok(name,value):
        assert value,name
        items.append(name)
    grid=Grid(524288)
    rng=random.Random(18602)
    for i in range(160):
        k=rng.choice([1,3,9,27]); a=rng.choice([0,524280,2000000000])+rng.randrange(30)
        b=a+rng.randrange(1,200);t=grid.start(a)+rng.randrange((b-a)*196+150)
        assert grid.work(a,b,k,t)==sum(max(0,min(92,t-grid.start(j))) for j in range(a,b) if grid.eligible(j,k))
        assert grid.count(a,b,k)==sum(grid.eligible(j,k) for j in range(a,b))
    ok('160 exact pulse integrals/counts, four strides and warmup',True)
    ok('nested masks retain every stride-27 slot',all(grid.eligible(j,k) for j in range(524313,525000,27) for k in [1,3,9,27]))
    small=dict(NW=10,NH=20,NR=10,timer_tick_ns=20,pair_source_ticks=100,source_tick_ns=4)
    weights=['1','0','0','0','0','0','0']
    for spec in cfg['methods']:
        for seed in range(3):
            rr=random.Random(1000+seed)
            marks=[dict(t=rr.randrange(50000),word=rr.randrange(8),bit=rr.randrange(6)) for _ in range(40)]
            marks += [dict(t=t,word=0,bit=i%3) for i,t in enumerate([0,1,60,61,70,90,92,132,148])]
            apps=[dict(arrival_ns=8000,word=4)]
            def calc(literal):
                return run(50000,marks,apps,make(spec,words=8,weights=weights,our_cfg=small,cut=80),literal=literal)
            a,b=calc(False),calc(True)
            for key in a:
                if key!='simulator_work':
                    assert a[key]==b[key],(spec['id'],seed,key,a[key],b[key])
        ok(spec['id']+': active queue equals exhaustive small calendar (3 histories)',True)
    late=run(100,[dict(t=70,word=0,bit=5)],[],Constant(words=8))
    ok('late hit after implicit clean latch survives without write',late['residual_errors']=={'0':{'5':70}} and not late['err_events'])
    partial=run(100,[dict(t=50,word=0,bit=5)],[],Constant(words=8))
    ok('partial repair charges only 8 ns beyond clean pulse',partial['bus']['correction_extra_ns']==8 and partial['unfinished_operations'][0]['end_ns']==148)
    retained=run(200,[dict(t=1,word=0,bit=0),dict(t=70,word=0,bit=1),dict(t=90,word=0,bit=1)],[],Constant(words=8))
    ok('birth-preserving repair and sticky first hit',retained['residual_errors']=={'0':{'0':1}} and retained['first_exceedance']['t']==70)
    for H,charge,end in [(46,46,None),(92,92,92),(164,92,92)]:
        r=run(H,[],[],Constant(words=8))
        ok(f'empty/unfinished boundary H={H}',r['bus']['total_ns']==charge and r['started_control_operations']==1)
    boundary=run(1342,[],[dict(arrival_ns=0,word=4)],Constant(words=8))
    ok('partial app charges 30 ns',boundary['bus']['application_read_ns']==30)
    for spec in cfg['methods']:
        a=[dict(t=1000,word=0,bit=1)]
        p=run(10000,a,[],make(spec,words=8,weights=weights,our_cfg=small,cut=80))
        q=run(10000,a+[dict(t=11000,word=7,bit=4)],[],make(spec,words=8,weights=weights,our_cfg=small,cut=80))
        ok(spec['id']+': future suffix cannot affect observed prefix',p==q)
    p=Patent(window_s=60)
    p.wake(60*NS)
    ok('patent empty window goes LOW',p.k==27)
    p.observe(61*NS,61*NS-64);p.observe(62*NS,62*NS-64)
    ok('patent high equality holds LOW',p.k==27)
    p.observe(63*NS,63*NS-64)
    ok('patent count above high enters FAST',p.k==1)
    p.wake(122*NS-64)
    ok('patent low equality holds FAST',p.k==1)
    p.wake(123*NS-64)
    ok('patent strict source window expires at boundary',p.k==27 and not p.sources)
    p=Patent(window_s=120);p.observe(10*NS,9*NS)
    ok('patent first observation does not bypass startup window',p.k==1)
    p=Krasnikov(zero='hold'); p.finish(10**15)
    ok('Krasnikov empty hold has counted virtual cycles',p.k==1 and p.updates==10**15//p.period)
    p=Krasnikov(zero='longest');end=p.period;p.wake(end)
    ok('Krasnikov empty longest changes once',p.k==27 and p.target==1)
    p=Krasnikov(zero='hold');end=p.period;p.observe(end,0)
    ok('Krasnikov delivery on right boundary belongs to next cycle',p.anchor==end and p.count==1 and p.updates==1)
    p.wake(2*end)
    ok('Krasnikov count equal target holds period',p.k==1 and p.target==1)
    p=Krasnikov(zero='hold');end=p.period;p.observe(1,0);p.observe(2,1);p.wake(end)
    m=1+2*524288*F('.001')*F(end,NS)/(2*315576000)
    ok('Krasnikov formula 10 exact rational target',p.target==m)
    c=Chen(weights=['-1']+['0']*6)
    for h in range(1,7): c.wake(next_cut(h*HOUR))
    ok('Chen negative forecast clamps and six complete bins gate',c.k==27 and c.hour==7)
    c=Chen(weights=['0']*6+['100000'],fault_budget='.1')
    c.observe(6*HOUR+1,0)
    for h in range(1,7): c.wake(next_cut(h*HOUR))
    ok('Chen unavailable current-hour observation cannot alter closed bin forecast',c.k==27)
    c.wake(next_cut(7*HOUR))
    ok('Chen delivered observation enters next closed-hour forecast',c.k==1)
    zero=fit({'train_a':[],'train_b':[],'train_c':[],'train_d':[]})
    ok('exact ridge zero data and normal-equation residual',zero['weights']==['0']*7 and zero['training_pairs']==72)
    try:
        fit({'test_a':[]})
        raise AssertionError('test accepted into training')
    except AssertionError as exc:
        if str(exc)=='test accepted into training': raise
    ok('training rejects test episode keys',True)
    accepted=json.loads((root/'experiments/t186-method-comparison/inputs.json').read_text(encoding='utf-8'))
    expected=json.loads((root/'experiments/t186-method-comparison/outputs/results.json').read_text(encoding='utf-8'))
    # Compare stored accepted result, without rewriting or rerunning its source verifier.
    if isinstance(expected,dict):
        expected=expected['results']
    for spec,old in zip([dict(family='constant',k=1),dict(family='our')],expected):
        new=run(accepted['horizon_ns'],accepted['injections'],accepted['application_reads'],
                make(spec,our_cfg=accepted['policy'],cut=accepted['policy']['cut_ns']))
        for key in ['first_exceedance','bus','started_control_operations','completed_control_operations',
                    'application','residual_errors','bus_after_first_exceedance','max_application_delay_ns']:
            assert new[key]==old[key],('accepted pilot',spec,key,new[key],old[key])
        assert [x['t'] for x in new['err_events']]==[x['t'] for x in old['err_events']]
        assert new['mode_history']==[dict(t_ns=x['t_ns'],k=3 if x['low'] else 1) for x in old['mode_history']]
        ok(spec['family']+': stored accepted pilot cost/event/phase compatibility',True)
    return dict(status='checks passed',count=len(items),items=items,
                scope='implementation verification by author; not independent scientific review')


if __name__=='__main__':
    here=Path(__file__).resolve().parent
    cfg=json.loads((here/'inputs.json').read_text(encoding='utf-8'))
    result=validate(cfg,here.parents[2])
    print(json.dumps(result,ensure_ascii=False,indent=2))
