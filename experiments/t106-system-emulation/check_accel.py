"""Independent clean-case full-top checker; no state-transfer helper imports.

Shared accepted specifications: absolute E pin table/calendar and raw rule
Oracle. No production mapping, C transition or jump implementation is called.
Only the explicitly clean/no-application cases of ACCELERATION.md are accepted.
"""
import argparse
import bisect
import gzip
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'t104-rtl-resume'))
from reference import ETransaction,Request,ServiceConfig
sys.path.insert(0,str(HERE.parent/'t105-arm-rule'))
from oracle import Oracle

STEP=9408
PERIOD=188160
W=524288

def rows(path):
    with gzip.open(path,'rt') as f:
        for number,line in enumerate(f,1):
            fields=line.split()
            if fields:yield number,fields

def compare_short(a,b):
    """Every observable row outside the represented interval must match.

    END is host-stop bookkeeping after the declared horizon, not a free drain.
    The resumed interval starts at the SAME within-frame/CPU phase.
    """
    ar=[f for _,f in rows(a) if f[0]!='END']
    br=[f for _,f in rows(b) if f[0]!='END']
    jumps=[f for f in br if f[0]=='JUMP']
    assert jumps,'no accelerated interval exercised'
    intervals=[(int(f[1]),int(f[1])+int(f[2])*1000) for f in jumps]
    for f in ar:
        if f[0]=='JUMP':assert f in br,'baseline jump changed'
    expected=[f for f in ar if f[0]!='JUMP' and not any(x<=int(f[1])<y for x,y in intervals)]
    actual=[f for f in br if f[0]!='JUMP']
    assert len(expected)==len(actual),('tail length',len(expected),len(actual))
    for i,(x,y) in enumerate(zip(expected,actual)):
        assert x==y,('first tail difference',i,x,y)
    return dict(compared_rows=len(expected),represented_intervals=len(jumps))

def packet(text):return struct.unpack('<10Q4I',int(text,16).to_bytes(96,'little'))
def decision(text):return struct.unpack('<QQQII',int(text,16).to_bytes(32,'little'))

def clean_work(t,low):
    # Direct integral of disjoint length92 pulses, 24 residue classes per4704ns.
    # LOW is permitted here only after warmup; the caller checks that fact.
    ans=0
    for r in range(0,24,3 if low else 1):
        s=(r//8)*1568+(r%8)*164
        d=t-s
        if d<=0:continue
        q,rem=divmod(d,4704)
        ans+=q*92+min(rem,92)
    return ans

def window_peak(intervals,blocks,horizon,width=1000000):
    """Exact continuous-window maximum for explicit pulses + periodic blocks.

    A wholly internal window repeats every4704ns. All other extrema occur at
    pulse boundaries or a boundary minus width; enumerate those near each
    block edge, as well as every explicit pulse. No sampled-time maximum.
    """
    intervals=sorted(intervals);blocks=sorted(blocks)
    ends=[b for a,b in intervals];sums=[0]
    for a,b in intervals:sums.append(sums[-1]+b-a)
    bend=[b for a,b,l in blocks];bsum=[0]
    for a,b,l in blocks:bsum.append(bsum[-1]+clean_work(b,l)-clean_work(a,l))
    def prefix(t):
        i=bisect.bisect_right(ends,t);value=sums[i]
        if i<len(intervals):value+=max(0,t-intervals[i][0])
        j=bisect.bisect_right(bend,t);value+=bsum[j]
        if j<len(blocks):
            a,b,l=blocks[j]
            if t>a:value+=clean_work(t,l)-clean_work(a,l)
        return value
    candidates={0,horizon-width}
    for a,b in intervals:
        candidates.update((a,b,a-width,b-width))
    for a,b,l in blocks:
        candidates.update((a,b,a-width,b-width))
        for center in (a,b):
            first=max(a,center-width-4704);last=min(b,center+width+4704)
            for frame in range(max(0,first//1568-1),last//1568+2):
                for k in range(8):
                    if l and (frame*8+k)%3:continue
                    p=frame*1568+k*164
                    if a<=p<=b:candidates.update((p,p+92,p-width,p+92-width))
    best=max((prefix(x+width)-prefix(x),-x) for x in candidates if 0<=x<=horizon-width)
    return best[0],-best[1]

def check(path,meta):
    cfg=ServiceConfig(words=W).validate();raw=[];history=[];oracle=Oracle()
    slot=0;freeze=2;frozen={0:True,1:True};t0=None;horizon=None;rule_start=None
    active=None;transaction=None;started=0;seq=0;gen=0;previous_cut=None
    last_end=None;old_gen=0;healthy=True;processed=0;latest_deadline=None
    operations=0;completed=0;skipped_completed=0;pin_edges=0;writes=0
    intervals=[];blocks=[];cuts=[];programs=0;represented=0;permissions=[];err_events=0
    local_loss=False;current_permit=0;loss_edges=[]
    false_slot=(181000000000//1568)*8
    while cfg.start(false_slot)<181000000000 or false_slot%3:false_slot+=1
    false_begin=cfg.start(false_slot)+58 if meta['scenario']=='quiet' else 0
    fname=Path(path).name

    def verify_program(b,d,count=1):
        nonlocal seq,last_end,old_gen,healthy,processed,latest_deadline,programs
        assert b[0]==seq+count,('sequence',b[0],seq,count)
        assert b[1]==old_gen and b[4]==rule_start and b[13]==0
        events=[(e,tick) for _,e,tick in history if (last_end is None or tick>last_end) and tick<=b[3]]
        if count!=1:assert not events,'nonempty history was skipped'
        errs=[];recoveries=[]
        for e,tick in events:
            loss=bool(e&2)
            if healthy and loss:healthy=False
            elif not healthy and not loss:healthy=True;recoveries.append(tick)
            if e&1:errs.append((e,tick))
            oracle.apply((tick,e>>66,(e>>2)&((1<<64)-1),2|4*(e&1)|8*bool(e&2),0))
        flags=1+2*healthy+4*bool(recoveries)+8*bool(events and events[-1][1]==b[3])
        expected=(seq+count,old_gen,old_gen+len(events),b[3],rule_start,
            (errs[0][0]>>2)&((1<<64)-1) if errs else 0,
            (errs[-1][0]>>2)&((1<<64)-1) if errs else 0,
            errs[0][1] if errs else 0,errs[-1][1] if errs else 0,
            recoveries[-1] if recoveries else 0,len(events),len(errs),flags,0)
        assert b==expected,('collector raw history',b,expected)
        if b[3]>oracle.now:oracle.apply((b[3],0,0,0,0))
        assert not oracle.fault
        ss=oracle.snapshot();allow=oracle.started and oracle.healthy and not oracle.fault
        expected_d=(b[0],b[2],b[3]+max(*ss[3:6],int(oracle.blocked)) if allow else 0,int(allow))
        expected_d+= (zlib.crc32(struct.pack('<QQQI',*expected_d)),)
        assert d==expected_d,('ARM decision',d,expected_d)
        seq=b[0];last_end=b[3];old_gen=b[2];processed=b[2];latest_deadline=d[2]
        programs+=1

    for line,f in rows(path):
        kind=f[0];t=int(f[1])//1000
        try:
            if kind=='T0':t0=t
            elif kind=='RULE_START':
                rule_start=int(f[2],16);oracle.apply((rule_start,0,0,1,0))
            elif kind=='FREEZE':
                rel,p,a,m=int(f[2]),*[int(x,16) for x in f[3:]]
                assert rel==t-t0==cfg.start(freeze)-320
                assert bool(m)==cfg.mandatory(freeze)
                frozen[freeze]=bool(m or not p or a);freeze+=1
            elif kind=='SLOT':
                rel,execute,w,busy=int(f[2]),*[int(x,16) for x in f[3:]]
                assert rel==t-t0==cfg.start(slot) and w==cfg.address(slot)
                assert execute==frozen.pop(slot) and not busy
                slot+=1
            elif kind=='GRANT':
                assert active is None
                ident,app,p=int(f[2]),int(f[3]),int(f[4],16)
                assert not app and ident==operations
                req=Request(p&3,(p>>2)&(W-1),(p>>21)&0xffffffff,(p>>53)&15)
                assert req.kind==0 and req.word==cfg.address(slot-1)
                active=ident;started=t;transaction=ETransaction(req,0);operations+=1
            elif kind=='OBSERVE':
                assert int(f[2])==active and t==started+60
                alias,dq,err,mask=[int(x,16) for x in f[3:]]
                assert (alias,dq,mask)==(0,0,0)
                assert err==int(bool(false_begin) and false_begin<=t-t0<false_begin+4)
            elif kind=='PIN':
                ident,age=int(f[2]),int(f[3]);v=[int(x,16) for x in f[4:]]
                assert ident==active and t==started+age and v[16]==0
                e=transaction.step(age,v[16],bool(v[17]))
                keys=('busy','ce','oe','we','drive','alias','be','dout','sample','flag','done','commit','pending','data')
                assert v[:14]==[e[x] for x in keys],('E edge',ident,age)
                assert v[14]==transaction.request.word;pin_edges+=1
            elif kind=='WRITE':
                ident=int(f[2]);alias,data,be,value,errors=[int(x,16) for x in f[3:]]
                assert ident==active and transaction.latch_err and t==started+132
                assert (alias,data,be,value,errors)==(0,0,3,0xa5a50000,0);writes+=1
            elif kind=='RELEASE':
                assert int(f[2])==active and t-started==(148 if transaction.latch_err else 92)
                intervals.append((started-t0,t-t0));completed+=1;active=None
            elif kind=='EVENT':
                e=int(f[2],16);gen+=1
                assert e>>66==gen and (e>>2)&((1<<64)-1)==(t-t0)//4
                assert not current_permit,'publication must veto on this fast edge'
                if e&1:
                    assert active is not None and transaction.latch_err and t==started+64
                    assert meta['scenario']=='quiet' and t-t0==false_begin+6
                    err_events+=1
                if bool(e&2)!=local_loss:
                    assert meta['scenario']=='loss'
                    scheduled=(181000000000,181002000000)[len(loss_edges)]
                    assert 0<=t-t0-scheduled<=100,'bounded slow-input to fast publication CDC'
                    loss_edges.append(t-t0);local_loss=bool(e&2)
                raw.append(e)
            elif kind=='HISTORY':
                assert len(history)<len(raw) and int(f[2],16)==raw[len(history)],'history loss/repetition'
                history.append((t,int(f[2],16),int(f[3],16)))
            elif kind=='CUT':
                tick=int(f[2],16)
                if previous_cut is not None:assert tick-previous_cut==STEP,('cut spacing',tick-previous_cut)
                else:assert 0<t-t0<=1000000,'initial full-service deadline'
                previous_cut=tick;cuts.append(t)
            elif kind=='PROGRAM':verify_program(packet(f[2]),decision(f[3]))
            elif kind=='JUMP':
                delta,n,done,low,word=[int(x) for x in f[2:7]]
                assert active is None and delta==n*PERIOD and n>0 and n%2==0
                assert word==cfg.address(slot)
                if low:assert slot>=W,'LOW macro must not omit warmup'
                expected_done=n*(320 if low else 960)
                assert done==expected_done
                if meta['mode']!='fixed':
                    b,d=packet(f[7]),decision(f[8]);verify_program(b,d,n)
                    assert previous_cut+n*STEP==b[3]+1
                    previous_cut=b[3]+1;represented+=n
                frozen={k+n*960:v for k,v in frozen.items()}
                slot+=n*960;freeze+=n*960;operations+=done;skipped_completed+=done
                blocks.append((t-t0,t-t0+delta,bool(low)))
            elif kind=='PERMISSION':
                permit,low,loss,g,pg,deadline=[int(x,16) for x in f[2:]]
                if low:
                    # slow posedges are 10+20*k ns; after that edge tick=k+1.
                    # PERMISSION is sampled by the fast clock, not at a cut.
                    assert deadline==latest_deadline and (t+10)//20>=deadline and processed==pg,(t,deadline,latest_deadline,pg,processed)
                    assert oracle.healthy and not oracle.fault
                # loss in this record is the EXTERNAL slow-domain pin. Its
                # standard CDC precedes fast publication/local invalidation.
                if permit:assert not local_loss and g==pg and latest_deadline is not None and (t+10)//20>=latest_deadline
                current_permit=permit
                permissions.append((t-t0,permit,low,loss,g,pg,deadline))
            elif kind=='HORIZON':
                horizon=t-t0
                assert horizon==meta['stimulus']['horizon_ns'],'declared horizon changed'
                assert int(f[2])==(-1 if active is None else active)
                if active is not None:intervals.append((started-t0,horizon))
            elif kind in ('QUALIFIED','END'):pass
            else:raise AssertionError('unexpected input/record '+kind)
        except (AssertionError,IndexError,KeyError,ValueError) as e:
            raise AssertionError(f'{fname}:{line}:{kind} t={t}ns: {e}') from e
    assert horizon and raw==[e for _,e,_ in history]
    assert err_events==int(meta['scenario']=='quiet')
    assert len(loss_edges)==(2 if meta['scenario']=='loss' else 0)
    assert len(blocks)==len(meta['macros'])
    for block,m in zip(blocks,meta['macros']):
        assert block==(m['begin_ns'],m['end_ns'],m['low'])
        assert clean_work(block[1],block[2])-clean_work(block[0],block[2])==m['price']['occupied_ns']
    work=sum(b-a for a,b in intervals)+sum(clean_work(b,l)-clean_work(a,l) for a,b,l in blocks)
    peak,peak_at=window_peak(intervals,blocks,horizon)
    assert peak<=800000
    return dict(mode=meta['mode'],scenario=meta['scenario'],horizon_ns=horizon,
        pin_edges_checked=pin_edges,explicit_operations=completed,represented_operations=skipped_completed,
        unfinished_operations=int(active is not None),completed_operations=completed+skipped_completed,
        calendar_slots=slot,empty_blocks=len(blocks),represented_services=represented,programs_checked=programs,
        err_events=err_events,history_events=len(history),loss_publication_relative_ns=loss_edges,physical_alias_writes=writes,
        bus_work_ns=work,mean_bus_fraction=work/horizon,peak_any_1ms_fraction=peak/1000000,
        peak_window_start_relative_ns=peak_at,permissions=permissions,
        model_full_service_ns=PERIOD if cuts else None,hardware_ARM_time_ns=None,whole_mission_Q_inferred=False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',default='short');ap.add_argument('--mode',default='adaptive')
    ap.add_argument('--compare',action='store_true');args=ap.parse_args()
    stem=f'accel-{args.case}-{args.mode}-skip';meta=json.loads((HERE/f'outputs/{stem}.json').read_text())
    path=HERE/f'outputs/{stem}.trace.gz';result=check(path,meta)
    if args.compare:
        base=f'accel-{args.case}-{args.mode}-'+('no-low' if args.case=='lowprobe' else 'literal')
        result['literal_equivalence']=compare_short(HERE/f'outputs/{base}.trace.gz',path)
    print(json.dumps(result,indent=2))
    (HERE/f'outputs/{stem}-check.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
