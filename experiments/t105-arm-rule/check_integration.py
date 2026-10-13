"""Independent full trace checker: accepted E oracle + absolute rule oracle.

Shares declared constants and wire ABI, not any production mapping/update,
CRC circuit, batch C, AXI or CDC helper. B's independent E oracle is reused.
"""
import hashlib,struct,sys
from pathlib import Path
from batch_model import collect
from verify_batch import decision_expected
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'t104-rtl-resume'))
from reference import ETransaction,Request,ServiceConfig

def check(path):
    offers={};accepts=[];responses=[];grants={};appgrants=[];releases={}
    events=[];history=[];programs=[];groups=[];start=None;latest=0;lease=None
    previous=0;pin_edges=0;max_credits=0;max_response=0;max_output=0
    slots=0;freeze_index=2;freezes={0:True,1:True};skips=0;veto=0;installed=0
    config=ServiceConfig(words=16).validate()
    allowed_certificates=set()
    sent_payloads=set()
    for line in path.read_text().splitlines():
        f=line.split()
        if not f:continue
        k=f[0]
        if k=='RULE_START':start=int(f[2],16)
        elif k=='HISTORY':
            t,e,tick=int(f[1]),int(f[2],16),int(f[3],16)
            history.append((t,e,tick))
        elif k=='PROGRAM':
            b=struct.unpack('<10Q4I',int(f[2],16).to_bytes(96,'little'))
            d=struct.unpack('<QQQII',int(f[3],16).to_bytes(32,'little'))
            es=[(tick,(e>>2)&((1<<64)-1),e&1,(e>>1)&1) for _,e,tick in history if previous<tick<=b[3]]
            groups.append((b[3],es));programs.append((b,d));previous=b[3]
            allowed_certificates.add((d[1],d[2],d[3]))
        elif k=='INTERVAL_SEND':
            tick,p=int(f[2],16),int(f[3],16)
            assert any(g==p>>1 and bool(flags&1)==bool(p&1) and
                       (not p&1 or tick>=deadline)
                       for g,deadline,flags in allowed_certificates),'premature interval'
            sent_payloads.add(p)
        elif k=='EVENT':
            e=int(f[2],16);events.append((int(f[1]),e));latest=e>>66;lease=None
        elif k=='INSTALLED':
            g=int(f[2],16);p=int(f[3],16)
            assert p in sent_payloads,'no sent certificate'
            assert g==p>>1==latest,('stale installation',g,p,latest)
            # CRC/sequence is separately tested at the mailbox; only a
            # C-originated generation/allow pair may reach this boundary.
            assert any(x[0]==g and bool(x[2]&1)==bool(p&1) for x in allowed_certificates)
            lease=(g,bool(p&1));installed+=1
        elif k=='FREEZE':
            edge=4*int(f[2]);pos=int(f[3]);permit,alarm,must=(int(x,16) for x in f[4:7])
            assert edge==config.start(freeze_index)-320
            assert pos==freeze_index%8 and must==config.mandatory(freeze_index)
            if permit:assert not alarm and lease==(latest,True),('unjustified LOW',f,lease,latest)
            freezes[freeze_index]=bool(must or not permit or alarm);veto+=alarm;freeze_index+=1
        elif k=='SLOT':
            edge=4*int(f[2]);execute,word,busy=(int(x,16) for x in f[3:6])
            assert edge==config.start(slots) and word==config.address(slots)
            assert execute==freezes.pop(slots) and not busy,('frozen operation changed',slots)
            skips+=not execute;slots+=1
        elif k=='OFFER':
            p=int(f[3],16);offers[p>>57]=(int(f[1]),int(f[2]),p)
        elif k=='ACCEPT':
            p=int(f[3],16);ident=p>>57;assert p==offers[ident][2]
            accepts.append(ident);max_credits=max(max_credits,len(accepts)-len(responses));assert max_credits<=2
        elif k=='GRANT':
            t,seq,app=int(f[1]),int(f[2]),int(f[3]);p=int(f[4],16)
            req=Request(p&3,(p>>2)&((1<<19)-1),(p>>21)&0xffffffff,(p>>53)&15)
            grants[seq]=(ETransaction(req,0),t)
            if app:
                ident=accepts[len(appgrants)];assert p==offers[ident][2]&((1<<57)-1)
                appgrants.append((ident,seq))
        elif k=='PIN':
            seq,age=int(f[2]),int(f[3]);v=[int(x,16) for x in f[4:]]
            expected=grants[seq][0].step(age,v[16],bool(v[17]))
            keys=('busy','ce','oe','we','drive','alias','be','dout','sample','flag','done','commit','pending','data')
            assert v[:14]==[expected[x] for x in keys],('E trace',seq,age,v,expected)
            assert v[14]==grants[seq][0].request.word;pin_edges+=1
        elif k=='RELEASE':releases[int(f[2])]=int(f[1])
        elif k=='REPLY':
            t,owner=int(f[1]),int(f[2]);p=int(f[3],16);ident=p>>33
            assert ident==accepts[len(responses)] and owner==offers[ident][1]
            seq=appgrants[len(responses)][1];tr=grants[seq][0]
            expect=(ident<<33)|((tr.sampled_low|(tr.sampled_high<<16))<<1)|int(tr.request.kind!=1 and tr.latch_err)
            assert p==expect
            max_response=max(max_response,(t-offers[ident][0])/1000)
            max_output=max(max_output,(t-releases[seq])/1000);responses.append(ident)
        elif k in ('Fatal:','FATAL:','ERROR:'):raise AssertionError(line)
    assert start is not None
    expected=collect(start,groups,nw=40,nh=80,nr=130)
    for (b,d),(eb,state) in zip(programs,expected):
        assert b==eb,('batch differs from raw events',b,eb)
        assert d==decision_expected(b[0],state),('rule differs',b,d,state)
    assert accepts==responses and len(responses)>0 and skips>0 and veto>0 and installed>0
    assert [e for _,e in events]==[e for _,e,_ in history],'raw history loss/repetition'
    assert 'PASS ARM integrated' in path.read_text()
    return {'packets':len(programs),'raw_events':len(history),'installed_certificates':installed,
      'slots':slots,'skips':skips,'veto_freezes':veto,'E_pin_edges':pin_edges,
      'requests':len(responses),'max_credits':max_credits,
      'observed_max_response_ns':max_response,'observed_max_release_to_consumed_ns':max_output,
      'log_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'timing_type':'observed HDL simulated time, no CPU WCET or universal bound'}
