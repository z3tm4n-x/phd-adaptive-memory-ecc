"""New executor/generator verification; accepted results are read-only."""
from copy import deepcopy
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import json
import math
from pathlib import Path
import random
from application import Application,DURATION
from engine import run
from generator import generate,parts,hazard_at,Segment
from reuse import HERE,ROOT,policies,calendar,formats,load


def validate(cfg):
    items=[]
    def ok(name,value):
        assert value,name
        items.append(name)
    fast=dict(family='constant',k=1)
    small_policy=dict(NW=10,NH=20,NR=10,timer_tick_ns=20,pair_source_ticks=100,source_tick_ns=4)
    rng=random.Random(18603)
    appcfg=dict(cfg['application'],first_ns=0)
    profiles=cfg['application']['profiles']
    for profile in profiles:
        app=Application(profile,appcfg,words=8)
        for H in [46,1312,1342,1528,100000,500000,1000000,5000001,9010031]:
            intervals=list(app.intervals(H))
            for kind in DURATION:
                literal=sum(min(DURATION[kind],H-x['start']) for x in intervals if x['kind']==kind)
                assert literal==app.pulse_prefix(H,kind),(profile['id'],H,kind)
            for w in range(8):
                for t in [0,1312,100000,456789,2000000]:
                    choice=app.next_for_word(w,t)
                    if choice:
                        s,q=choice
                        assert app.word(q)==w and s>=t
                        assert q<8 or app.start(q-8,'write32')<t
        ok(profile['id']+': exact pulse/count prefixes and modular dirty-word next visit',True)
    accelerated=dict(id='directed',pairs_per_epoch=1,epoch_ns=20000,read_offsets_ns=[0],write_offset_ns=10000)
    app=Application(accelerated,appcfg,words=8)
    method_specs=json.loads((HERE.parent/'stage2/inputs.json').read_text(encoding='utf-8'))['methods']
    weights=json.loads((HERE.parent/'stage2/training.json').read_text(encoding='utf-8'))['weights']
    for spec in method_specs:
        for seed in range(3):
            rr=random.Random(186030+seed)
            marks=[dict(t=rr.randrange(250000),word=rr.randrange(8),bit=rr.randrange(8)) for _ in range(65)]
            s=app.start(0,'write32')
            marks += [dict(t=s+x,word=0,bit=i%3) for i,x in enumerate([-1,1,60,61,100,132,140,200,215])]
            a=run(250000,marks,app,policies.make(spec,words=8,weights=weights,our_cfg=small_policy,cut=80))
            b=run(250000,marks,app,policies.make(spec,words=8,weights=weights,our_cfg=small_policy,cut=80),literal=True)
            for key in a:
                if key!='simulator_work':assert a[key]==b[key],(spec['id'],seed,key,a[key],b[key])
        ok(spec['id']+': dirty executor equals literal full-service traversal, 3 histories',True)
    none=Application(profiles[0],cfg['application'])
    accepted_cfg=json.loads((HERE.parent/'inputs.json').read_text(encoding='utf-8'))
    for spec in [fast,dict(family='our')]:
        marks=accepted_cfg['injections']
        old=calendar.run(accepted_cfg['horizon_ns'],marks,[],policies.make(spec))
        new=run(accepted_cfg['horizon_ns'],marks,none,policies.make(spec))
        for key in ['first_exceedance','mode_history','residual_errors','started_control_operations']:
            assert old[key]==new[key],key
        assert old['bus']['total_ns']==new['bus']['total_ns']
        assert [x['t'] for x in old['err_events']]==[x['t'] for x in new['err_events']]
        ok(spec['family']+': empty-application regression against accepted executor',True)
    # Independent accepted memory/pin oracle for a write crossing both commit edges.
    mem=load('stage3_accepted_memory',ROOT/'experiments/t104-rtl-resume/memory_oracle.py')
    ref=load('stage3_accepted_pins',ROOT/'experiments/t104-rtl-resume/reference.py')
    s=app.start(0,'write32')
    marks=[dict(t=s-1,word=0,bit=0),dict(t=s+140,word=0,bit=1)]
    m=mem.MemoryOracle(8);m.words[0].toggle(0,s-1);m.begin(1,0,s,'write32');m.observe(s+60)
    m.write(s+132,0,0,transaction_id=1);m.words[0].toggle(1,s+140);m.write(s+200,1,0,transaction_id=1);m.release(s+216)
    r=run(s+216,marks,app,policies.make(fast,words=8))
    ok('two observed-write commits preserve post-start birth, accepted memory oracle',r['residual_errors']=={'0':{'1':s+140}} and m.words[0].errors=={1:s+140})
    ok('observed-write ERR is separately counted and pending delivery preserved',r['algorithm']['observed_write_ERR']==1 and r['algorithm']['pending_ERR']==1)
    tx=ref.ETransaction(ref.Request(ref.WRITE32,0),0)
    pins=[(t,tx.step(t,dq=0,err=t==60)) for t in range(0,217,4)]
    ok('accepted write pins: observation60 publication64 commits132/200 release216',
       [t for t,p in pins if p['sample']]==[60] and [t for t,p in pins if p['flag']]==[64]
       and [t for t,p in pins if p['commit']]==[132,200] and [t for t,p in pins if p['done']]==[216])
    for edge in [s,s+1,s+59,s+60,s+64,s+131,s+132,s+199,s+200,s+215,s+216,s+616]:
        r=run(edge,[dict(t=s+70,word=0,bit=2)],app,policies.make(fast,words=8))
        z=run(edge,[dict(t=s+70,word=0,bit=2)],app,policies.make(fast,words=8),literal=True)
        for key in ['application','bus','residual_errors','err_events','unfinished_control']:
            assert r[key]==z[key],(edge,key)
    ok('12 boundaries: late hit, both writes, pending SRAM and outbound reply',True)
    r=run(s+216,[dict(t=s-1,word=0,bit=1),dict(t=s+1,word=0,bit=2),dict(t=s+2,word=0,bit=2)],app,policies.make(fast,words=8))
    ok('first hit survives XOR and useful write; price continues',r['first_exceedance']['t']==s+1 and r['bus_after_first_exceedance']['total_ns']>0)
    H=315576000*10**9
    for profile in profiles[1:]:
        a=Application(profile,cfg['application'])
        summary=a.summary(H)
        ok(profile['id']+': all 631152000000 application operations counted without enumeration',
           all(v['started']==315576000000 for v in summary['counts'].values()) and
           summary['bus']['read32_ns']==315576000000*184 and summary['bus']['write32_ns']==315576000000*216)
    ep=dict(cfg['episodes'][2]);ep.update(horizon_s=100,peak_start_s=10,rise_s=10,hold_s=20,fall_s=10)
    env=dict(cfg['environment']);env.update(background_per_s='0.05',peak_per_s='2')
    testcfg=dict(cfg,environment=env)
    g=generate(ep,testcfg,keep_hazards=True)
    with localcontext() as ctx:
        ctx.prec=70
        ss=parts(ep,env)
        for mark,h in zip(g['marks'],g['hazards']):
            lo=hazard_at(D(mark['t']-1)/10**9,ss);hi=hazard_at(D(mark['t'])/10**9,ss)
            assert lo-D('1e-40')<=D(h)<=hi+D('1e-40')
    ok('inverse NHPP event hazards lie inside the corresponding 1 ns cells',True)
    # Independent Simpson integral over each smooth segment, no production hazard function.
    integral=0.
    for s in parts(ep,env):
        n=1000;dt=(s.end-s.start)/n;x,y=float(s.low),float(s.high)
        alpha=math.log(y/x)/(s.end-s.start) if x!=y else 0.
        values=[x*math.exp(alpha*i*dt) for i in range(n+1)]
        integral+=dt/3*(values[0]+values[-1]+4*sum(values[1:-1:2])+2*sum(values[2:-1:2]))
    ok('integrated intensity agrees with independent Simpson quadrature',abs(integral-float(g['generation']['integrated_intensity']))<1e-8)
    zero=Segment(0,10,D(0),D(0));ok('zero-rate segment has zero hazard',zero.mass==0)
    for s in [Segment(0,10,D('.1'),D('1')),Segment(10,20,D('1'),D('.1')),Segment(20,30,D('.1'),D('.1'))]:
        with localcontext() as ctx:
            ctx.prec=50
            for u in [D(0),D('.001'),D(5),D('9.999'),D(10)]:
                assert abs(s.inverse(s.hazard(u))-u)<D('1e-45')
    ok('flat/rising/falling inverse segments include both endpoints',True)
    counts=[]
    flat=dict(ep,shape='quiet',horizon_s=100)
    flatcfg=dict(cfg,environment=dict(env,background_per_s='.2',peak_per_s='.2'))
    for i in range(cfg['generator']['counter_check_runs']):
        flat['seed']=cfg['generator']['counter_check_seed']+i
        counts.append(len(generate(flat,flatcfg)['marks']))
    n=len(counts);mean=sum(counts)/n;var=sum((x-mean)**2 for x in counts)/(n-1)
    ok('512-count fixed-seed Poisson diagnostic: mean and variance within registered broad numerical checks',abs(mean-20)<6*math.sqrt(20/n) and abs(var-20)<6*20*math.sqrt(2/(n-1)))
    return dict(status='checks passed',count=len(items),items=items,poisson_counter_diagnostic=dict(runs=n,mean=mean,variance=var,expected=20),
                scope='directed implementation/generator verification; no mission Q or independent scientific acceptance')


if __name__=='__main__':
    print(json.dumps(validate(json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))),indent=2))
