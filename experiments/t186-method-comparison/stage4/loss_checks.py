"""Directed acceptance regressions; unchanged scientific matrix/parameters."""
from itertools import combinations,permutations
import json
from adapter import Adapter,encode_record,decode_record,HOUR
from application import Application
from engine import run
from grid import Grid
from reuse import HERE


def state(a,H):
    core={k:getattr(a.core,k,None) for k in
          ('k','timer','anchor','count','hour','bins','sources','observations','updates')}
    if core['sources'] is not None:core['sources']=list(core['sources'])
    if core['bins'] is not None:core['bins']={str(k):v for k,v in core['bins'].items()}
    return dict(k=a.k,health=a.source_health,unknown=a.unknown,
                holds=[a.short,a.long,a.recovery],timer=a.timer,
                modes=[list(x) for x in zip(a.times,a.modes)],delivered=a.delivered,
                ranges=a.unknown_ranges,core=core,cost=a.costs(H))


def validate_loss(cfg,exercise):
    names=[];evidence={}
    def ok(name,test):
        assert test,name
        names.append('loss repair: '+name)
    delivery=cfg['delivery']
    weights=json.loads((HERE.parent/'stage2/training.json').read_text())['weights']
    specs=json.loads((HERE.parent/'stage2/inputs.json').read_text())['methods']
    ids=['constant_1','our_r4','krasnikov_0.001_longest','patent_60','chen_0.1']
    specs=[next(s for s in specs if s['id']==id_) for id_ in ids]
    ours=specs[1];small=dict(NW=10,NH=20,NR=10,timer_tick_ns=20,pair_source_ticks=100,source_tick_ns=4)
    traces=[
        [dict(t=2992,kind='ERR',drop=True),dict(t=2996,kind='ERR'),
         dict(t=3000,kind='GAP',covers=[1,1]),dict(t=3004,kind='RESTORE')],
        [dict(t=3000,kind='ERR',drop=True),dict(t=3004,kind='ERR',ingress_ns=0),
         dict(t=3008,kind='GAP',covers=[1,1],ingress_ns=992),dict(t=3012,kind='RESTORE')]]
    evidence['R1']=[]
    for sp in specs:
        for i,events in enumerate(traces):
            a,tr=exercise(sp,delivery,events,16000,weights=weights)
            early=next(x for x in tr if x['event']=='adapter_ready' and x['t']==7900)
            assert early['unknown'] and early['processed_G']==2 and early['losses']==1
            assert not a.unknown and a.losses==a.restores==a.source_losses==a.source_recoveries==1
            assert a.generation==a.processed==4 and len(a.records)==4 and len(a.delivered)==1
            assert a.gap_confirmations==1 and a.inferred_gaps==1
            if sp['family']=='our':
                assert early['k']==1 and a.recovery==11900+a.cfg['NR']*20
            evidence['R1'].append(dict(method=sp['id'],variant=i,first_ready=early,
                                       final=state(a,16000)))
        ok(sp['id']+': both accepted inter-packet counterexamples, one episode/recovery',True)
    for arrival in (3999,4000,4001):
        ev=[dict(t=3004,kind='ERR',drop=True),dict(t=3008,kind='ERR',ingress_ns=0),
            dict(t=3012,kind='GAP',covers=[1,1],ingress_ns=arrival-3012),
            dict(t=3016,kind='RESTORE')]
        assert arrival-3004<=1000
        a,tr=exercise(ours,delivery,ev,16000)
        expect=7900 if arrival<4000 else 11900
        ok('GAP arrival '+str(arrival)+': strict cut, timely recognition, no additional wait',
           a.losses==a.restores==1 and a.unknown_ranges[-1]['processed_at']==expect
           and a.recovery==11900+a.cfg['NR']*20)
    repeated=[dict(t=0,kind='ERR',drop=True),dict(t=4,kind='ERR'),
              dict(t=8,kind='GAP',covers=[1,1]),dict(t=12,kind='GAP',covers=[1,1]),
              dict(t=16,kind='RESTORE'),dict(t=20000,kind='GAP',covers=[1,1]),
              dict(t=20004,kind='RESTORE')]
    for sp in specs:
        a,tr=exercise(sp,delivery,repeated,40000,our_cfg=small,weights=weights)
        assert a.losses==a.restores==a.source_losses==a.source_recoveries==1
        assert a.gap_confirmations==3 and a.restore_confirmations==1
        assert a.gap_notices==3 and a.restore_notices==2 and a.generation==a.processed==7
        assert len(a.records)==7 and not a.unknown and a.source_health
        if sp['family']=='our':assert a.recovery==8100 and a.mode(20000)==1
        ok(sp['id']+': repeated confirmation before/after restore is charged, no second NR',True)
    distinct=repeated[:5]+[dict(t=20000,kind='ERR',drop=True),dict(t=20004,kind='ERR'),
                           dict(t=20008,kind='GAP',covers=[6,6]),dict(t=20012,kind='RESTORE')]
    a,tr=exercise(ours,delivery,distinct,40000,our_cfg=small,initial_G=0)
    ok('two separate loss episodes preserve generation and pay two recoveries',
       a.losses==a.restores==a.source_losses==a.source_recoveries==2 and
       a.generation==a.processed==9 and a.recovery==27900+200)
    high=2**63
    high_events=[dict(e,**({'covers':[v+high for v in e['covers']]} if 'covers' in e else {})) for e in traces[1]]
    a,tr=exercise(ours,delivery,high_events,16000,initial_G=high)
    ok('inferred range and restored watermark retain high G64 bits',
       a.processed==a.resolved_G==high+4 and a.unknown_ranges[0]['range']==[high+1,high+1])
    no_restore=[dict(t=0,kind='ERR',drop=True),dict(t=4,kind='ERR'),dict(t=20000,kind='ERR')]
    a,tr=exercise(ours,delivery,no_restore,40000,our_cfg=small)
    ok('no new holes is not RESTORE',a.unknown and a.k==1 and a.restores==0 and a.losses==1)
    # Tail-loss cannot be inferred from simulator bookkeeping or current G.
    a,tr=exercise(ours,delivery,[dict(t=20000,kind='ERR',drop=True)],40000,our_cfg=small)
    ok('unreported tail loss is not silently detected from private source log',
       not a.unknown and a.inferred_gaps==a.losses==0 and a.processed==0 and a.generation==1 and a.k==1)
    tail=[dict(t=20000,kind='ERR',drop=True),dict(t=20004,kind='GAP',covers=[1,1],ingress_ns=996),
          dict(t=24000,kind='RESTORE')]
    a,tr=exercise(ours,delivery,tail,40000,our_cfg=small)
    ok('timely explicit signal closes the otherwise unobservable tail-loss case',
       a.losses==a.restores==1 and a.inferred_gaps==1 and a.processed==3 and a.recovery==32100)
    # Every nonempty subset/permutation of the four compatible edge causes.
    combos=0
    for sp in specs:
        for n in range(1,5):
            for subset in combinations(['ERR','FALSE','GAP','RESTORE'],n):
                reference=None
                for order in permutations(subset):
                    ev=[dict(t=0,kind=k) for k in order]
                    a,tr=exercise(sp,delivery,ev,20000,our_cfg=small,weights=weights)
                    raw=encode_record(a.records[0]);wire=decode_record(raw)
                    roundtrip=[dict(t=wire['t'],kind=k,**({'covers':wire['covers']} if k=='GAP' else {}))
                               for k in wire['causes']]
                    b,_=exercise(sp,delivery,roundtrip,20000,our_cfg=small,weights=weights)
                    current=state(a,20000)
                    assert current==state(b,20000),(sp['id'],order,'wire')
                    assert reference is None or reference==(raw,current),(sp['id'],order,'permutation')
                    reference=(raw,current);combos+=1
        ok(sp['id']+': all cause permutations and decoded source replay have one meaning',True)
    evidence['permutation_runs']=combos
    # Production-sized time constants reproduce the actual acceptance cases.
    evidence['R2']=[]
    for sp in [ours,specs[3]]:
        compared=[]
        for order in [('GAP','RESTORE'),('RESTORE','GAP')]:
            prefix=[dict(t=i*4,kind='ERR') for i in range(10)] if sp['family']=='patent' else []
            ev=prefix+[dict(t=10000,kind=k) for k in order]
            a,tr=exercise(sp,delivery,ev,200000000000,weights=weights)
            compared.append((list(map(encode_record,a.records)),state(a,200000000000)))
        ok(sp['id']+': actual 200-second counterexample resolved',compared[0]==compared[1]
           and not a.unknown and a.source_health and a.k==(3 if sp['family']=='our' else 27)
           and a.losses==a.restores==1)
        evidence['R2'].append(dict(method=sp['id'],wire=compared[0][0][-1].hex(),state=compared[0][1]))
    # Direct and decoded receivers execute the same record, even after UNKNOWN.
    for order in permutations(['ERR','FALSE','GAP','RESTORE']):
        r=dict(t=4,g=2,causes=list(order),covers=[1,1])
        states=[]
        for decoded in [r,decode_record(encode_record(r))]:
            a=Adapter(ours,delivery,our_cfg=small);a.ready_time=7900
            a._gap(7900,dict(t=4,g=2,covers=[1,1]),inferred=True)
            a.apply_record(7900,decoded);states.append(state(a,10000))
        assert states[0]==states[1]
    ok('direct/decoded receive is independent of list order for every combined cause',True)
    # An old hold outlives both loss and the restarted short recovery.
    slow=dict(small,NH=10000)
    ev=[dict(t=0,kind='ERR'),dict(t=4,kind='ERR'),
        dict(t=20000,kind='GAP'),dict(t=20000,kind='RESTORE')]
    a,tr=exercise(ours,delivery,ev,250000,our_cfg=slow)
    ok('combined restore preserves max old hold and strict equality',
       a.long==207900 and a.mode(207900)==1 and a.mode(207904)==3)
    # Pending write and first-hit cost: same literal/accelerated execution.
    prof=dict(id='directed',pairs_per_epoch=1,epoch_ns=20000,read_offsets_ns=[0],write_offset_ns=10000)
    appcfg=dict(cfg['application'],first_ns=0)
    for period in [None,3396]:
        app=Application(prof,appcfg,Grid(16,period));s=app.start(0,'write32')
        marks=[dict(t=s-2,word=0,bit=0),dict(t=s-1,word=0,bit=1),dict(t=s+140,word=0,bit=2)]
        fault=traces[1]+[dict(t=s+128,kind='RESTORE'),dict(t=s+128,kind='GAP')]
        args=(100000,marks,app)
        a=run(*args,Adapter(ours if period is None else specs[0],delivery,words=16,our_cfg=small),faults=fault)
        b=run(*args,Adapter(ours if period is None else specs[0],delivery,words=16,our_cfg=small),faults=fault,literal=True)
        assert all(a[k]==b[k] for k in a if k!='simulator_work')
        assert a['first_exceedance']['t']==s-1 and a['bus_after_first_exceedance']['total_ns']>0
        if period is not None:
            clean=run(*args,Adapter(specs[0],delivery,words=16))
            assert a['started_control_operations']==clean['started_control_operations'] and a['bus']==clean['bus']
        ok(str(period)+': combined loss during pending write, first-hit and full price match literal',True)
    app=Application(prof,appcfg,Grid(16));j=31;freeze=app.grid.start(j)-320
    for delta in [-4,0,4]:
        a=Adapter(ours,delivery,words=16,our_cfg=small)
        run(30000,[],app,a,faults=[dict(t=freeze+delta,kind='RESTORE'),dict(t=freeze+delta,kind='GAP')])
        ok('combined source at freeze'+str(delta)+': veto/frozen skip retained',
           a.mode(freeze)==(1 if delta<=0 else 3) and a.mode(freeze+delta)==1)
    evidence['loss_state_allocation_bytes']=64
    evidence['scope']='addressed implementation checks; no new matrix seed, MC, physical timing or accepted theorem'
    return dict(checks=names,count=len(names),evidence=evidence)
