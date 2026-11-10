"""Stage4 executor: full useful application and packet-observed policies.

The accepted policies and Grid are imported read-only. This is a new
executor for observed writes and analytic clean useful work, not a mutation
of accepted stage2. All policy inputs remain endogenous observations.
"""
from fractions import Fraction
import heapq
import time
from application import DURATION
from reuse import calendar

Grid=calendar.Grid


def run(H,marks,app,policy,literal=False,deadline=None,faults=()):
    grid=app.grid
    heap=[];serial=0;processed=0
    errors={};active={};versions={}
    corrections=[];errs=[];delivered=policy.delivered;transactions=[]
    counts={};first=None;max_dirty=0;max_heap=0;max_active=0
    last_timer=object();late_birth_commits=0

    def push(t,priority,kind,x):
        nonlocal serial,max_heap
        if 0<=t<=H:
            serial+=1;heapq.heappush(heap,(t,priority,serial,kind,x))
            max_heap=max(max_heap,len(heap))

    def timer():
        nonlocal last_timer
        if last_timer!=policy.timer:
            last_timer=policy.timer
            if last_timer is not None:push(last_timer,2,'timer',last_timer)

    def schedule(w,t):
        if literal or w in active or not errors.get(w):return
        j0=(3*w)%grid.words
        j=j0+max(0,calendar.ceildiv(grid.first(t)-j0,grid.words))*grid.words
        s=grid.start(j)
        useful=app.next_for_word(w,t)
        versions[w]=versions.get(w,0)+1
        if useful and useful[0]<s:
            push(useful[0],4,'dirty_write',(w,useful[1],versions[w]))
        else:push(s,4,'control',(j,versions[w]))

    def start(w,s,kind,slot=None,q=None,known_clean=False,now=None):
        nonlocal max_active
        assert w not in active,('word lock conflict',w,s,kind)
        tx=dict(word=w,start=s,kind=kind,slot=slot,q=q,err=False,end=None)
        active[w]=tx;transactions.append(tx);max_active=max(max_active,len(active))
        if not known_clean:
            push(s+60,5,'snapshot',tx)
        else:
            tx['end']=s+(92 if kind=='control' else DURATION[kind])
            if kind=='write32':
                for offset in (132,200):
                    if s+offset>=now:push(s+offset,6,'commit',tx)
            push(tx['end'],7,'release',tx)
        return tx

    policy.bind(push)
    for fault in faults:push(fault['t'],1,'source_fault',fault)
    for mark in marks:
        assert 0<=mark['word']<grid.words and 0<=mark['bit']<38
        push(mark['t'],0,'injection',mark)
    if literal:
        push(0,4,'literal_control',0)
        for cut in range(policy.cut,H+1,policy.cut):push(cut,3,'adapter_empty_literal',cut)
        for req in app.intervals(H):push(req['start'],4,'literal_app',req)
    timer()

    while heap:
        t,_,_,kind,x=heapq.heappop(heap)
        processed+=1;counts[kind]=counts.get(kind,0)+1
        if deadline is not None and processed%1024==0 and time.perf_counter()>deadline:
            raise TimeoutError('stage3 registered wall budget reached')
        if kind=='injection':
            w,bit=x['word'],x['bit'];e=errors.setdefault(w,{})
            if bit in e:del e[bit]
            else:e[bit]=t
            if len(e)>1 and first is None:first=dict(t=t,word=w,bits=sorted(e))
            if not e:
                errors.pop(w,None);versions[w]=versions.get(w,0)+1
            elif not literal and w not in active:
                useful=app.active_for_word(w,t)
                j0=3*w%grid.words;last=grid.first(t+1)-1
                j=j0+((last-j0)//grid.words)*grid.words
                s=grid.start(j) if j>=0 else -1000
                if useful and useful['start']<H:
                    versions[w]=versions.get(w,0)+1
                    start(w,useful['start'],useful['kind'],q=useful['q'],known_clean=t>useful['start']+60,now=t)
                elif j>=0 and s<=t<s+92 and s<H and grid.eligible(j,policy.mode(s-320)):
                    versions[w]=versions.get(w,0)+1
                    start(w,s,'control',slot=j,known_clean=t>s+60,now=t)
                else:schedule(w,t)
            max_dirty=max(max_dirty,len(errors))
        elif kind in ('control','literal_control'):
            j=x if kind=='literal_control' else x[0];w=grid.address(j)
            if kind=='literal_control':push(grid.start(j+1),4,kind,j+1)
            elif versions.get(w)!=x[1] or not errors.get(w) or w in active:continue
            if t>=H:continue
            if grid.eligible(j,policy.mode(t-320)):start(w,t,'control',slot=j)
            else:schedule(w,t+1)
        elif kind in ('dirty_write','literal_app'):
            if kind=='dirty_write':
                w,q,version=x
                if versions.get(w)!=version or not errors.get(w) or w in active:continue
                k='write32'
            else:w,q,k=x['word'],x['q'],x['kind']
            if t<H:start(w,t,k,q=q)
        elif kind=='snapshot':
            tx=x;tx['err']=bool(errors.get(tx['word']))
            k=tx['kind'];s=tx['start']
            tx['end']=s+((148 if tx['err'] else 92) if k=='control' else DURATION[k])
            if tx['err'] and k!='read32':push(s+64,1,'publish',tx)
            if k=='control' and tx['err']:
                corrections.append((s+92,s+148));push(s+132,6,'commit',tx)
            if k=='write32':
                push(s+132,6,'commit',tx);push(s+200,6,'commit',tx)
            push(tx['end'],7,'release',tx)
        elif kind=='publish':
            errs.append(dict(t=t,word=x['word'],kind=x['kind'],slot=x['slot'],q=x['q']))
            policy.source(t,'ERR',word=x['word'],origin=x['kind']);timer()
        elif kind=='source_fault':
            policy.source(t,x['kind'],**{k:v for k,v in x.items() if k not in ('t','kind')});timer()
        elif kind.startswith('adapter_'):
            policy.handle(t,kind,x);timer()
        elif kind=='timer':
            if policy.timer!=x:continue
            policy.wake(t);timer()
        elif kind=='commit':
            w=x['word'];e={b:born for b,born in errors.get(w,{}).items() if born>=x['start']}
            if e:errors[w]=e;late_birth_commits+=1
            else:errors.pop(w,None)
        elif kind=='release':
            active.pop(x['word']);schedule(x['word'],t)
        else:raise AssertionError(kind)
    policy.finish(H)
    slots=grid.first(H)
    cuts=[(0,policy.modes[0])]+[(grid.first(t+320),k) for t,k in zip(policy.times[1:],policy.modes[1:]) if grid.first(t+320)<slots]+[(slots,1)]
    segments=[(a,b,k) for (a,k),(b,_) in zip(cuts,cuts[1:]) if b>a]
    def base(t):return sum(grid.work(a,b,k,t) for a,b,k in segments)
    def pulse(intervals,a,b):return sum(max(0,min(b,y)-max(a,x)) for x,y in intervals)
    def price(a,b):
        value=dict(control_base_ns=base(b)-base(a),correction_extra_ns=pulse(corrections,a,b))
        value.update(app.work(a,b));value['total_ns']=sum(value.values());return value
    bus=price(0,H)
    application=app.summary(H)
    started=sum(grid.count(a,b,k) for a,b,k in segments)
    unfinished=[]
    if slots:
        j=slots-1;s=grid.start(j)
        if grid.eligible(j,policy.mode(s-320)):
            tx=active.get(grid.address(j))
            end=tx['end'] if tx and tx['slot']==j else (s+92 if s+60<=H else None)
            if end is None or end>H:unfinished.append(dict(kind='control',start=s,end=end,charged_ns=H-s))
    if literal:
        literal_controls=[x for x in transactions if x['kind']=='control']
        assert len(literal_controls)==started
        assert sum(min(H,x['end'] or x['start']+92)-x['start'] for x in literal_controls)==bus['control_base_ns']+bus['correction_extra_ns']
        for kind in DURATION:
            actual=[x for x in transactions if x['kind']==kind]
            assert len(actual)==application['counts'][kind]['started']
            assert sum(min(H,x['start']+DURATION[kind])-x['start'] for x in actual)==bus[kind+'_ns']
    algorithm=policy.costs(H)
    algorithm.update(control_ERR=sum(x['kind']=='control' for x in errs),
                     observed_write_ERR=sum(x['kind']=='write32' for x in errs))
    return dict(horizon_ns=H,first_exceedance=first,Q_MC=None,bus=bus,
                mean_bus_fraction_exact=str(Fraction(bus['total_ns'],H)),mean_bus_percent=100*bus['total_ns']/H,
                bus_after_first_exceedance=price(first['t'],H) if first else None,
                started_control_operations=started,completed_control_operations=started-len(unfinished),
                unfinished_control=unfinished,application=application,algorithm=algorithm,
                err_events=errs,delivered_ERR=delivered,transport_batches=policy.batches,unknown_ranges=policy.unknown_ranges,source_records=policy.records,
                mode_history=[dict(t_ns=t,k=k) for t,k in zip(policy.times,policy.modes)],
                residual_errors={str(w):{str(b):v for b,v in sorted(e.items())} for w,e in sorted(errors.items())},
                simulator_work=dict(event_counts=counts,events=processed,explicit_transactions=len(transactions),
                                    maximum_dirty_words=max_dirty,maximum_active_transactions=max_active,max_heap=max_heap,
                                    commits_retaining_late_births=late_birth_commits))
