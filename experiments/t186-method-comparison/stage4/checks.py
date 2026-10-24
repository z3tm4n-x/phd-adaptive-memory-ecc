"""Addressed checks of the changed contract; no mission Monte Carlo."""
from copy import deepcopy
from fractions import Fraction as F
import heapq
import json
import random
from adapter import Adapter,HOUR,encode_record,decode_record
from application import Application,DURATION
from engine import run
from grid import Grid
from reuse import HERE,ROOT,formats,load

def exercise(spec,cfg,events,H,our_cfg=None,weights=None,initial_G=0):
    a=Adapter(spec,cfg,words=8,our_cfg=our_cfg,weights=weights)
    a.generation=a.processed=initial_G
    heap=[];serial=0;last=object();trace=[]
    def push(t,p,k,x):
        nonlocal serial
        if 0<=t<=H:serial+=1;heapq.heappush(heap,(t,p,serial,k,x))
    def timer():
        nonlocal last
        if last!=a.timer:
            last=a.timer
            if last is not None:push(last,2,'timer',last)
    a.bind(push)
    for e in events:push(e['t'],1,'source',e)
    timer()
    while heap:
        t,_,_,kind,x=heapq.heappop(heap)
        if kind=='source':a.source(t,x['kind'],**{k:v for k,v in x.items() if k not in ('t','kind')})
        elif kind=='timer':
            if a.timer!=x:continue
            a.wake(t)
        else:a.handle(t,kind,x)
        timer();trace.append(dict(t=t,event=kind,k=a.k,G=a.generation,processed_G=a.processed,
                                 unknown=a.unknown,health=a.source_health,losses=a.losses,
                                 restores=a.restores,recovery=a.recovery))
    a.finish(H);return a,trace

def validate(cfg):
    names=[];details={}
    def ok(name,test):
        assert test,name
        names.append(name)
    small=dict(NW=10,NH=20,NR=10,timer_tick_ns=20,pair_source_ticks=100,source_tick_ns=4)
    fast=dict(id='constant_1',family='constant',k=1)
    ours=dict(id='our_r4',family='our')
    weights=json.loads((HERE.parent/'stage2/training.json').read_text())['weights']
    specs=json.loads((HERE.parent/'stage2/inputs.json').read_text())['methods']
    accelerated=dict(id='directed',pairs_per_epoch=5,epoch_ns=200000,read_offsets_ns=[0,20000,40000,60000,80000],write_offset_ns=10000)
    appcfg=dict(cfg['application'],first_ns=0)
    for period in [None,3396]:
        grid=Grid(16,period)
        starts=[grid.start(j) for j in range(800)]
        for t in range(0,30000,7):
            assert grid.first(t)==next(j for j,s in enumerate(starts) if s>=t)
            app_starts=[grid.start(j)+1312 for j in range(0,800,8)]
            assert grid.grant(t)==next(s for s in app_starts if s>=t)
        ok(str(period)+': inverse control/app calendar equals exhaustive calendar',True)
        app=Application(accelerated,appcfg,grid)
        for H in [1,1312,1313,1496,1528,200000,201314,401000]:
            intervals=list(app.intervals(H))
            for k,d in DURATION.items():
                assert app.pulse_prefix(H,k)==sum(min(d,H-x['start']) for x in intervals if x['kind']==k)
            assert app.summary(H)['transport_request_records']>=len(intervals)
        ok(str(period)+': exact prefix price including partial application tail',True)
    for spec in specs:
        for seed in range(3):
            grid=Grid(16)
            app=Application(accelerated,appcfg,grid)
            rr=random.Random(186040+seed)
            marks=[dict(t=rr.randrange(250000),word=rr.randrange(16),bit=rr.randrange(8)) for _ in range(65)]
            s=app.start(0,'write32');marks += [dict(t=s+d,word=0,bit=i%3) for i,d in enumerate([-1,1,60,61,100,132,140,200,215])]
            a=run(250000,marks,app,Adapter(spec,cfg['delivery'],words=16,weights=weights,our_cfg=small))
            b=run(250000,marks,app,Adapter(spec,cfg['delivery'],words=16,weights=weights,our_cfg=small),literal=True)
            for k in a:
                if k!='simulator_work':assert a[k]==b[k],(spec['id'],seed,k)
        ok(spec['id']+': packet/dirty executor equals literal traversal, three histories',True)
    for seed in range(3):
        app=Application(accelerated,appcfg,Grid(16,3396));rr=random.Random(seed)
        marks=[dict(t=rr.randrange(250000),word=rr.randrange(16),bit=rr.randrange(5)) for _ in range(70)]
        a=run(250000,marks,app,Adapter(fast,cfg['delivery'],words=16))
        b=run(250000,marks,app,Adapter(fast,cfg['delivery'],words=16),literal=True)
        assert all(a[k]==b[k] for k in a if k!='simulator_work')
    ok('sufficient fixed nonuniform frames: three literal histories',True)
    delivery=[]
    for t,cut in [(2996,4000),(3000,8000),(3004,8000)]:
        a,tr=exercise(ours,cfg['delivery'],[dict(t=t,kind='ERR')],20000,small)
        ok(f'source{t}: ingress equality goes to correct whole packet',a.batches[0]['cut']==cut and a.delivered[0]['t']==cut+3900)
        assert all(x['processed_G']==0 for x in tr if x['t']<cut+3900)
        delivery.append(dict(source=t,capture=cut,ready=cut+3900))
    details['delivery_boundaries']=delivery
    for delta in (396,400,404):
        a,tr=exercise(ours,cfg['delivery'],[dict(t=0,kind='ERR'),dict(t=delta,kind='ERR')],20000,small)
        ok(f'PAIR source delta{delta}: equality included; no packet coalescing',len(a.delivered)==2 and (a.long>0)==(delta<=400))
        end=max(a.short,a.long,a.recovery);expiry=4*((end+4)//4)
        assert a.mode(end)==1 and a.mode(expiry)==3
        assert expiry not in [b['cut'] for b in a.batches]
    ok('precomputed strict expiry applies without an extra capture',True)
    a,tr=exercise(ours,cfg['delivery'],[dict(t=0,kind='ERR'),dict(t=8104,kind='ERR')],30000,small,initial_G=2**40)
    ok('same-edge expiry/source veto and full G64 freshness',a.mode(8104)==1 and a.generation==2**40+2 and a.processed==a.generation)
    ok('no prefix token before complete processing',all(x['processed_G']<x['G'] for x in tr if x['event']=='source'))
    events=[dict(t=0,kind='ERR',drop=True),dict(t=4,kind='GAP',covers=[1,1]),dict(t=8,kind='RESTORE'),dict(t=12,kind='ERR')]
    a,tr=exercise(ours,cfg['delivery'],events,30000,small)
    ok('dropped record is explicit UNKNOWN; restore preserves G and loads NR',a.dropped==1 and len(a.delivered)==1 and a.processed==4 and a.recovery==7900+small['NR']*20 and bool(a.unknown_ranges))
    a,tr=exercise(ours,cfg['delivery'],[dict(t=0,kind='ERR',drop=True),dict(t=4,kind='ERR')],20000,small)
    ok('unconfirmed missing prefix persists as UNKNOWN, not zero-filled',a.unknown and a.k==1 and a.losses==1 and a.restores==0)
    # A long old hold cannot be shortened by GAP/RESTORE/another short hold.
    slow=dict(small,NH=10000)
    a,tr=exercise(ours,cfg['delivery'],[dict(t=0,kind='ERR'),dict(t=4,kind='ERR'),dict(t=20000,kind='GAP'),dict(t=24000,kind='RESTORE')],250000,slow)
    ok('restore preserves previous long hold and equality FAST',a.long==207900 and a.mode(207900)==1 and a.mode(207904)==3)
    app=Application(accelerated,appcfg,Grid(16))
    j=31;f=app.grid.start(j)-320
    ad=Adapter(ours,cfg['delivery'],words=16,our_cfg=small)
    run(30000,[],app,ad,faults=[dict(t=f+4,kind='ERR')])
    ok('source after freeze does not cancel a committed skip',ad.mode(f)==3 and not app.grid.eligible(j,ad.mode(f)) and ad.mode(f+4)==1)
    for source in [f-4,f]:
        ad=Adapter(ours,cfg['delivery'],words=16,our_cfg=small)
        run(30000,[],app,ad,faults=[dict(t=source,kind='ERR')])
        assert ad.mode(f)==1 and app.grid.eligible(j,ad.mode(f))
    ok('source before/on freeze vetoes LOW; equality is FAST',True)
    a,tr=exercise(fast,cfg['delivery'],[dict(t=0,kind='ERR'),dict(t=0,kind='FALSE')],20000)
    ok('one source-edge combines causes, not independent transaction ERR',len(a.records)==len(a.delivered)==1 and a.coalesced==1)
    packet=dict(t=315576000*10**9,g=2**63+7,causes=['ERR','GAP'],covers=[2**63,2**63+6])
    wire=encode_record(packet);decoded=decode_record(wire)
    ok('32-byte wire format preserves full G64, timestamp and GAP endpoints',len(wire)==32 and decoded['g']==packet['g'] and decoded['t']==packet['t'] and decoded['payload']==packet['covers'])
    # Strong valid source stream, with compression of <=1000 ns ingress.
    dense=[dict(t=t,kind='ERR',ingress_ns=max(0,3996-t) if 3000<=t<=3996 else 0) for t in range(0,24000,4)]
    a,tr=exercise(fast,cfg['delivery'],dense,40000)
    ok('finite two-bank transport under dense ordered ingress',a.peak_batch<=1253 and a.peak_inflight<=253 and a.peak_records<=4096 and len(a.delivered)==len(dense))
    details['dense_transport']=a.costs(40000)
    try:exercise(fast,cfg['delivery'],[dict(t=0,kind='ERR',ingress_ns=1000),dict(t=4,kind='ERR',ingress_ns=0)],10000)
    except AssertionError:ok('cross-packet unordered prefix is rejected',True)
    else:
        # Same packet may be ordered by its explicit G; a cross-cut reorder must fail.
        try:exercise(fast,cfg['delivery'],[dict(t=3500,kind='ERR',ingress_ns=1000),dict(t=3504,kind='ERR',ingress_ns=0)],16000)
        except AssertionError:ok('cross-packet unordered prefix is rejected',True)
        else:raise AssertionError('cross-cut reorder accepted')
    for spec in [dict(id='k',family='krasnikov',Ms='.001',zero='longest'),dict(id='p',family='patent',window_s=F(1,50000))]:
        a,tr=exercise(spec,cfg['delivery'],[dict(t=80000,kind='GAP'),dict(t=90000,kind='RESTORE')],200000)
        ok(spec['family']+': GAP is explicit and does not inject OUR same-edge FAST',a.mode(79999)==a.mode(80000)==27 and bool(a.unknown_ranges))
    spec=dict(id='c',family='chen_analog',fault_budget='.1')
    a,tr=exercise(spec,cfg['delivery'],[dict(t=7*HOUR,kind='GAP'),dict(t=8*HOUR,kind='RESTORE')],16*HOUR,weights=weights)
    ok('Chen UNKNOWN bins suspend forecasts until six complete known bins',a.unknown_forecasts>0 and a.forecasts>0 and a.known_hour==9)
    app=Application(accelerated,appcfg,Grid(16));s=app.start(0,'write32')
    marks=[dict(t=s-1,word=0,bit=0),dict(t=s+140,word=0,bit=1)]
    for edge in [s,s+1,s+60,s+64,s+132,s+140,s+200,s+216,s+616]:
        a=run(edge,marks,app,Adapter(fast,cfg['delivery'],words=16))
        b=run(edge,marks,app,Adapter(fast,cfg['delivery'],words=16),literal=True)
        assert all(a[k]==b[k] for k in a if k!='simulator_work'),edge
    ok('write boundaries, late births and packet/reply pending preserved',a['residual_errors'].get('0')=={'1':s+140})
    a=run(s+216,marks,app,Adapter(ours,cfg['delivery'],words=16,our_cfg=small),faults=[dict(t=s+128,kind='GAP'),dict(t=s+144,kind='RESTORE')])
    ok('GAP/RESTORE during pending write do not cancel either commit',a['residual_errors'].get('0')=={'1':s+140} and a['algorithm']['pending_records']>=2)
    g=Grid(cfg['memory']['words'],cfg['fixed']['period_ns'])
    frames=[g.phase(r+1)-g.phase(r) for r in range(g.groups-1)]+[g.period-g.phase(g.groups-1)]
    ok('full fixed phases/startup: 1696/1700 frames and 552 gap',set(frames)=={1696,1700} and g.max_gap==552 and all(g.start(g.words+j)-g.start(j)<=g.period for j in range(g.words)))
    from loss_checks import validate_loss
    details['loss_repair']=validate_loss(cfg,exercise)
    names+=details['loss_repair']['checks']
    ok('validation evidence has canonical JSON roundtrip',json.loads(formats.dumps(details))==details)
    return dict(status='OWN RESULT / checks passed, pending review',count=len(names),checks=names,details=details,
                scope='addressed changed-interface verification; no physical/WCET/MC qualification')

if __name__=='__main__':
    print(formats.dumps(validate(json.loads((HERE/'common-input.json').read_text()))))
