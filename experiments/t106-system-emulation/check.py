"""Independent step checker. No production C/RTL mapping/update helpers.

Memory uses birth-labelled sets, not the SV error/recent bit masks. Reused
accepted test oracles: absolute E pin table, absolute rule deadlines. Trust
dependencies and the limited first-run scope are stated in CONTRACT.md.
"""
import gzip
import json
from pathlib import Path
import struct
import sys
import zlib

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'t104-rtl-resume'))
from reference import ETransaction,Request,ServiceConfig
sys.path.insert(0,str(HERE.parent/'t105-arm-rule'))
from batch_model import collect

class Memory:
    def __init__(self):
        self.data={};self.errors={};self.first_exceedance=None
        self.lock=None;self.observed=False;self.had_error=False;self.commits=set()
    def value(self,w):return self.data.get(w,0xa5a50000^w)
    def mask(self,w):return sum(1<<b for b in self.errors.get(w,{}))
    def toggle(self,w,b,t):
        assert 0<=w<524288 and 0<=b<38
        es=self.errors.setdefault(w,{})
        if b in es:del es[b]
        else:es[b]=t
        if len(es)>1 and self.first_exceedance is None:self.first_exceedance=t
    def begin(self,seq,req,t):
        assert self.lock is None,'global word/alias lock'
        self.lock=(seq,req,t);self.observed=False;self.had_error=False;self.commits=set()
    def sample(self,seq,alias,t):
        ident,req,start=self.lock;assert seq==ident
        assert t==start+(152 if alias else 60)
        if not alias:
            assert not self.observed;self.observed=True
            self.had_error=bool(self.errors.get(req.word,{}))
        else:assert req.kind==1
        v=self.value(req.word)
        if len(self.errors.get(req.word,{}))>1:v^=self.mask(req.word)&0xffffffff
        return (v>>(16*alias))&65535,int(bool(self.errors.get(req.word,{})))
    def write(self,seq,alias,val,mask,t):
        ident,req,start=self.lock
        assert ident==seq and self.observed and alias not in self.commits
        assert t==start+(200 if alias else 132)
        assert req.kind==2 or (req.kind==0 and self.had_error and alias==0)
        self.commits.add(alias)
        # Removal follows the E-envelope; a later-born token is retained.
        self.errors[req.word]={b:birth for b,birth in self.errors.get(req.word,{}).items() if birth>=start}
        if req.kind==2:
            v=self.value(req.word)
            for b in range(2):
                if mask&(1<<b):
                    shift=16*alias+8*b
                    v=(v&~(255<<shift))|(((val>>(8*b))&255)<<shift)
            self.data[req.word]=v
        return self.value(req.word),self.mask(req.word)
    def release(self,seq,t):
        ident,req,start=self.lock;assert ident==seq and self.observed
        d=216 if req.kind==2 else 184 if req.kind==1 else 148 if self.had_error else 92
        assert t==start+d
        assert self.commits==({0,1} if req.kind==2 else {0} if req.kind==0 and self.had_error else set())
        self.lock=None

def exact_peak(intervals,begin,end,width):
    """Max of a continuous piecewise-linear sliding-window integral."""
    assert end-begin>=width
    edges={begin,end-width}
    for a,b,_ in intervals:
        for p in (a,b,a-width,b-width):
            if begin<=p<=end-width:edges.add(p)
    # This independent direct sum is bounded for the first ~6200 operations.
    def work(x):return sum(max(0,min(b,x+width)-max(a,x)) for a,b,_ in intervals)
    best=max((work(x),-x) for x in edges)
    return best[0]/width,-best[1]

def check(path,config,mode):
    cfg=ServiceConfig(words=config['words']).validate();mem=Memory()
    case=next(s for s in config['scenarios'] if s['id']==4)
    expected_injections=sorted(case['injections'],key=lambda r:(r['at_ns'],r['parent']))
    traces=0;offers={};accepts=[];replies=[];app_grants=[];grants={};releases={};intervals=[]
    starts={};types={};pin_edges=0;writes=0;observations=0;injections=0
    raw=[];history=[];programs=[];cuts=[];rule_start=None;t0=None;end=None
    slot=0;freeze=2;frozen={0:True,1:True};gen=0;maxcredits=0;err_events=0
    horizon_state=None
    opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'rt') as f:
        for line_number,line in enumerate(f,1):
            fields=line.split()
            if not fields:continue
            k=fields[0];t=int(fields[1])//1000
            try:
                if k=='T0':
                    assert t0 is None;t0=t;end=t+case['horizon_ns']
                elif k=='INJECT':
                    p,w,b,mask,exc=int(fields[2]),int(fields[3]),int(fields[4]),int(fields[5],16),int(fields[6])
                    e=expected_injections[injections];assert (t-t0,w,b,p)==(e['at_ns'],e['word'],e['bit'],e['parent'])
                    mem.toggle(w,b,t);assert mask==mem.mask(w) and exc==int(mem.first_exceedance is not None)
                    injections+=1
                elif k=='FREEZE':
                    relative,permit,alarm,must=int(fields[2]),int(fields[3],16),int(fields[4],16),int(fields[5],16)
                    assert relative==t-t0==cfg.start(freeze)-320
                    assert bool(must)==cfg.mandatory(freeze)
                    # First cold-start run only: NR alone precludes every LOW.
                    assert not permit,'premature LOW in cold scenario'
                    frozen[freeze]=bool(must or not permit or alarm);freeze+=1
                elif k=='SLOT':
                    relative,execute,w,busy=int(fields[2]),int(fields[3],16),int(fields[4],16),int(fields[5],16)
                    assert relative==t-t0==cfg.start(slot) and w==cfg.address(slot)
                    assert execute==frozen.pop(slot) and not busy
                    slot+=1
                elif k=='GRANT':
                    seq,app,p=int(fields[2]),int(fields[3]),int(fields[4],16)
                    req=Request(p&3,(p>>2)&((1<<19)-1),(p>>21)&0xffffffff,(p>>53)&15)
                    req.validate(524288);mem.begin(seq,req,t)
                    assert seq not in grants
                    grants[seq]=ETransaction(req,0);starts[seq]=t;types[seq]='control' if not app else 'app_read' if req.kind==1 else 'app_write'
                    if app:
                        ident=accepts[len(app_grants)];assert p==offers[ident][2]&((1<<57)-1)
                        assert (t-t0)%1568==1312
                        app_grants.append((ident,seq))
                elif k=='OBSERVE':
                    seq,alias,dq,err,mask=int(fields[2]),*[int(x,16) for x in fields[3:]]
                    expected=mem.sample(seq,alias,t)
                    assert (dq,err)==expected,('memory DQ/ERR',seq,(dq,err),expected)
                    assert mask==mem.mask(grants[seq].request.word);observations+=1
                elif k=='PIN':
                    seq,age=int(fields[2]),int(fields[3]);v=[int(x,16) for x in fields[4:]]
                    assert t==starts[seq]+age
                    expected=grants[seq].step(age,v[16],bool(v[17]))
                    keys=('busy','ce','oe','we','drive','alias','be','dout','sample','flag','done','commit','pending','data')
                    assert v[:14]==[expected[x] for x in keys],('pin cycle',seq,age,v,expected)
                    assert v[14]==grants[seq].request.word;pin_edges+=1
                elif k=='WRITE':
                    seq=int(fields[2]);alias,val,mask,data,errors=[int(x,16) for x in fields[3:]]
                    assert (data,errors)==mem.write(seq,alias,val,mask,t);writes+=1
                elif k=='RELEASE':
                    seq=int(fields[2]);mem.release(seq,t);releases[seq]=t
                    intervals.append((starts[seq],t,types[seq]))
                elif k=='OFFER':
                    owner,p=int(fields[2]),int(fields[3],16);ident=p>>57
                    assert ident not in offers and ident==len(offers)
                    a=case['application'];scheduled=t0+a['first_offer_ns']+ident*a['interval_ns']
                    assert 0<=t-scheduled<20
                    offers[ident]=(t,owner,p)
                elif k=='ACCEPT':
                    owner,p=int(fields[2]),int(fields[3],16);ident=p>>57
                    assert ident==len(accepts) and offers[ident][1:]==(owner,p)
                    assert 0<=t-offers[ident][0]<=320
                    accepts.append(ident);maxcredits=max(maxcredits,len(accepts)-len(replies));assert maxcredits<=2
                elif k=='REPLY':
                    owner,p=int(fields[2]),int(fields[3],16);ident=p>>33
                    assert ident==accepts[len(replies)] and owner==offers[ident][1]
                    g=app_grants[len(replies)][1];tr=grants[g]
                    expected=(ident<<33)|((tr.sampled_low|(tr.sampled_high<<16))<<1)|int(tr.request.kind!=1 and tr.latch_err)
                    assert p==expected,('reply data/ID',p,expected)
                    assert g in releases and 0<=t-releases[g]<=320
                    assert t-offers[ident][0]<=3000
                    replies.append((ident,t))
                elif k=='EVENT':
                    e=int(fields[2],16);gen+=1
                    assert e>>66==gen;assert (e>>2)&((1<<64)-1)==(t-t0)//4
                    assert e&3==1,'only true ERR allowed in cold scenario'
                    # Exactly one publication at +64 for every non-read observed ERR.
                    eligible=[s for s in grants if starts[s]+64==t and grants[s].request.kind!=1 and grants[s].latch_err]
                    assert len(eligible)==1,'ERR without coherent observation'
                    raw.append(e);err_events+=1
                elif k=='RULE_START':rule_start=int(fields[2],16)
                elif k=='HISTORY':history.append((t,int(fields[2],16),int(fields[3],16)))
                elif k=='CUT':cuts.append((t,int(fields[2],16)))
                elif k=='PROGRAM':
                    b=struct.unpack('<10Q4I',int(fields[2],16).to_bytes(96,'little'))
                    d=struct.unpack('<QQQII',int(fields[3],16).to_bytes(32,'little'))
                    programs.append((b,d))
                elif k=='HORIZON':
                    assert t==end;horizon_state=[int(x) for x in fields[2:]]
                elif k in ('QUALIFIED','END'):pass
                else:raise AssertionError('unknown record '+k)
            except (AssertionError,IndexError,KeyError,ValueError) as e:
                raise AssertionError(f'{Path(path).name}:{line_number}:{k} t={t}ns: {e}') from e
            traces+=1
    assert end and horizon_state is not None and rule_start is not None
    assert injections==len(expected_injections)
    assert len(offers)==len(accepts)==len(replies)==case['application']['count']
    assert [x[0] for x in replies]==accepts
    assert raw==[e for _,e,_ in history],'history loss/repetition'
    # Reverse inclusion catches a dropped ERR, not only invented publications.
    expected_err=sum(tr.request.kind!=1 and bool(tr.latch_err) and starts[s]+64<end for s,tr in grants.items())
    assert err_events==expected_err,('ERR count loss',err_events,expected_err)
    groups=[];previous=rule_start
    for b,d in programs:
        groups.append((b[3],[(tick,(e>>2)&((1<<64)-1),e&1,(e>>1)&1) for _,e,tick in history if previous<tick<=b[3]]))
        previous=b[3]
    for (b,d),(eb,state) in zip(programs,collect(rule_start,groups)):
        assert b==eb,('packet differs from raw history',b,eb)
        now,g,last,short,long,rec,flags,_=state
        allow=(flags&3)==3 and not flags&8
        de=(b[0],g,now+max(short,long,rec,int(bool(flags&16))) if allow else 0,int(allow))
        assert d==(*de,zlib.crc32(struct.pack('<QQQI',*de))),('ARM rule result',d,de)
    assert [b[3]+1 for b,d in programs]==[c[1] for c in cuts[:len(programs)]]
    if mode=='fixed':assert not cuts and not programs
    else:
        assert programs and cuts and cuts[0][0]-t0<=1000000
        assert all((b-a)*1.00001<=1000000 for (a,_),(b,_) in zip(cuts,cuts[1:]))
    truncated=0
    for seq in grants:
        if seq not in releases:
            intervals.append((starts[seq],end,types[seq]));truncated+=1
    intervals.sort();assert all(a2>=b for (a,b,k),(a2,b2,k2) in zip(intervals,intervals[1:]))
    assert truncated==int(horizon_state[0]>=0)
    work={k:sum(b-a for a,b,c in intervals if c==k) for k in ('control','app_read','app_write')}
    peak,peak_at=exact_peak(intervals,t0,end,1000000)
    assert peak<=.8
    corrective=sum(max(0,min(end,releases.get(s,end))-starts[s]-92)
                   for s,tr in grants.items() if tr.request.kind==0 and tr.latch_err)
    return {'scenario':4,'mode':mode,'t0_ns':t0,'horizon_ns':end-t0,
        'records_checked':traces,'pin_edges_checked':pin_edges,'full_word_observations':observations,
        'injections':injections,'ERR_events':err_events,'raw_history_matches':len(history),
        'ARM_packets_checked':len(programs),'calendar_slots':slot,'completed_operations':len(releases),
        'unfinished_operations_at_horizon':truncated,'application_completed':len(replies),'max_credits':maxcredits,
        'physical_alias_writes':writes,'bus_work_ns':work,'corrective_extra_within_control_ns':corrective,
        'mean_bus_fraction':sum(work.values())/(end-t0),'peak_any_1ms_fraction':peak,
        'peak_window_start_relative_ns':peak_at-t0,
        'observed_model_max_application_ns':max(t-offers[i][0] for i,t in replies),
        'model_max_cut_to_cut_ns':max((b-a for (a,_),(b,_) in zip(cuts,cuts[1:])),default=None),
        'first_exceedance_relative_ns':None if mem.first_exceedance is None else mem.first_exceedance-t0,
        'first_cut_relative_ns':cuts[0][0]-t0 if cuts else None,
        'remaining_error_positions':sum(len(v) for v in mem.errors.values()),
        'whole_mission_Q_inferred':False}

if __name__=='__main__':
    c=json.loads((HERE/'config.json').read_text())
    for m in ('adaptive','fixed'):print(json.dumps(check(HERE/f'outputs/cold-{m}.trace.gz',c,m),indent=2))
