"""Full-domain data/error checker, independent of the sparse RTL transfer.

Shared test specifications: birth-labelled Memory, ETransaction/ServiceConfig,
raw rule Oracle, and previously checked continuous-window price integral.
No production C/RTL update or accelerator helper is imported.
"""
import argparse
import json
from pathlib import Path
import struct
import zlib
from check import Memory
from check_accel import (HERE, W, STEP, PERIOD, packet, decision, clean_work,
                         window_peak, ETransaction, Request, ServiceConfig, Oracle)
from burst_codec import rows
from burst_price import Ledger

def check(path,meta):
    cfg=ServiceConfig(words=W).validate();raw=[];history=[];oracle=Oracle();ledger=Ledger()
    mem=Memory();stim=meta['stimulus'];injections=0;state_checked=False
    offers={};accepted=[];replies=[];app_grants=[];app_transactions={}
    accept_times={};release_times={};maxcredits=0;app_kind=None
    app_work={'read':0,'write':0};control_extra=0;expected_err=0;memory_samples=0
    touched=set();read_results=[]
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
                assert ident==operations
                req=Request(p&3,(p>>2)&(W-1),(p>>21)&0xffffffff,(p>>53)&15)
                req.validate(W)
                if app:
                    ident_app=accepted[len(app_grants)]
                    assert p==offers[ident_app][2]&((1<<57)-1)
                    assert (t-t0)%1568==1312
                    app_grants.append((ident_app,ident))
                    app_kind='read' if req.kind==1 else 'write'
                else:
                    assert req.kind==0 and req.word==cfg.address(slot-1);app_kind=None
                mem.begin(ident,req,t);touched.add(req.word)
                active=ident;started=t;transaction=ETransaction(req,0);operations+=1
                if app:app_transactions[ident]=(transaction,t)
            elif kind=='INJECT':
                p,w,bit,mask,exc=int(f[2]),int(f[3]),int(f[4]),int(f[5],16),int(f[6])
                e=stim['injections'][injections]
                assert (t-t0,w,bit,p)==(e['at_ns'],e['word'],e['bit'],e['parent'])
                mem.toggle(w,bit,t);touched.add(w);injections+=1
                assert (mask,exc)==(mem.mask(w),int(mem.first_exceedance is not None))
            elif kind=='OBSERVE':
                assert int(f[2])==active
                alias,dq,err,mask=[int(x,16) for x in f[3:]]
                assert (dq,err)==mem.sample(active,alias,t),('memory DQ/ERR',active)
                assert mask==mem.mask(transaction.request.word);memory_samples+=1
                if not alias and transaction.request.kind!=1 and err and t+4<t0+stim['horizon_ns']:
                    expected_err+=1
            elif kind=='PIN':
                ident,age=int(f[2]),int(f[3]);v=[int(x,16) for x in f[4:]]
                assert ident==active and t==started+age
                e=transaction.step(age,v[16],bool(v[17]))
                keys=('busy','ce','oe','we','drive','alias','be','dout','sample','flag','done','commit','pending','data')
                assert v[:14]==[e[x] for x in keys],('E edge',ident,age)
                assert v[14]==transaction.request.word;pin_edges+=1
            elif kind=='WRITE':
                ident=int(f[2]);alias,data,be,value,errors=[int(x,16) for x in f[3:]]
                assert (value,errors)==mem.write(ident,alias,data,be,t);writes+=1
            elif kind=='RELEASE':
                assert int(f[2])==active;mem.release(active,t)
                ledger.explicit(started-t0,t-t0);completed+=1
                if app_kind:
                    app_work[app_kind]+=t-started;release_times[active]=t
                elif transaction.latch_err:control_extra+=t-started-92
                active=None
            elif kind=='OFFER':
                owner,p=int(f[2]),int(f[3],16);ident=p>>57
                assert ident==len(offers)
                a=stim['applications'][ident]
                assert (owner,p)==(a['owner'],int(a['packet'],16))
                assert 0<=t-t0-a['at_ns']<20
                offers[ident]=(t,owner,p)
            elif kind=='ACCEPT':
                owner,p=int(f[2]),int(f[3],16);ident=p>>57
                assert ident==len(accepted) and offers[ident][1:]==(owner,p)
                assert 0<=t-offers[ident][0]<=320
                accepted.append(ident);accept_times[ident]=t
                maxcredits=max(maxcredits,len(accepted)-len(replies));assert maxcredits<=2
            elif kind=='REPLY':
                owner,p=int(f[2]),int(f[3],16);ident=p>>33
                assert ident==accepted[len(replies)] and owner==offers[ident][1]
                seq_app=app_grants[len(replies)][1];tr,start_app=app_transactions[seq_app]
                data=tr.sampled_low|(tr.sampled_high<<16)
                expected=(ident<<33)|(data<<1)|int(tr.request.kind!=1 and tr.latch_err)
                assert p==expected,('reply ID/data',ident,p,expected)
                assert seq_app in release_times and 0<=t-release_times[seq_app]<=320
                assert t-offers[ident][0]<=3000
                replies.append((ident,t))
                if tr.request.kind==1:
                    read_results.append(dict(id=ident,word=tr.request.word,at_ns=t-t0,data=f'{data:08x}'))
            elif kind=='EVENT':
                e=int(f[2],16);gen+=1
                assert e>>66==gen and (e>>2)&((1<<64)-1)==(t-t0)//4
                assert not current_permit,'publication must veto on this fast edge'
                if e&1:
                    assert active is not None and transaction.request.kind!=1 and transaction.latch_err and t==started+64
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
                assert len(accepted)==len(replies)==len(offers),'pending application jumped'
                assert all(not t-t0<=e['at_ns']<t-t0+delta for e in stim['injections'][injections:])
                assert all(not t-t0<=a['at_ns']<t-t0+delta for a in stim['applications'][len(offers):])
                # Independent inverse of word=(174763*j) mod W. The guard
                # deliberately tests ALL slots, including skipped LOW slots.
                for w,errors in mem.errors.items():
                    if not errors:continue
                    j=(3*w)%W
                    if j<slot:j+=((slot-j+W-1)//W)*W
                    assert j>=slot+n*960,('dirty word inside jump',w,j,slot,n)
                assert mem.lock is None
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
                ledger.add(t-t0,t-t0+delta,int(bool(low)))
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
                if active is not None:ledger.explicit(started-t0,horizon)
            elif kind=='STATE':
                ds,es=int(f[2],16),int(f[3],16)
                # Full W, not just touched words; a compact end-state audit.
                expected_ds=sum((w+1)*mem.value(w) for w in range(W)) & ((1<<64)-1)
                expected_es=sum((2*w+1)*mem.mask(w) for w in mem.errors) & ((1<<64)-1)
                assert (ds,es,int(f[4]),int(f[5]))==(expected_ds,expected_es,
                    sum(len(x) for x in mem.errors.values()),int(mem.first_exceedance is not None))
                state_checked=True
            elif kind in ('QUALIFIED','END'):pass
            else:raise AssertionError('unexpected input/record '+kind)
        except (AssertionError,IndexError,KeyError,ValueError) as e:
            raise AssertionError(f'{fname}:{line}:{kind} t={t}ns: {e}') from e
    assert horizon and raw==[e for _,e,_ in history]
    assert err_events==expected_err,('lost ERR',err_events,expected_err)
    assert state_checked and injections==len(stim['injections'])
    assert len(offers)==len(accepted)==len(replies)==len(stim['applications'])
    assert [x[0] for x in replies]==accepted
    assert all(b['at_ns']-a['at_ns']>=100000 for a,b in zip(stim['applications'],stim['applications'][1:]))
    assert len(loss_edges)==(2 if meta['scenario']=='loss' else 0)
    assert len(blocks)==len(meta['macros'])
    for block,m in zip(blocks,meta['macros']):
        assert block==(m['begin_ns'],m['end_ns'],m['low'])
        assert clean_work(block[1],block[2])-clean_work(block[0],block[2])==m['price']['occupied_ns']
    work=ledger.total
    peak,peak_at=ledger.peak(horizon)
    assert peak<=800000
    return dict(mode=meta['mode'],scenario=meta['scenario'],horizon_ns=horizon,
        pin_edges_checked=pin_edges,explicit_operations=completed,represented_operations=skipped_completed,
        unfinished_operations=int(active is not None),completed_operations=completed+skipped_completed,
        calendar_slots=slot,empty_blocks=len(blocks),represented_services=represented,programs_checked=programs,
        err_events=err_events,history_events=len(history),loss_publication_relative_ns=loss_edges,physical_alias_writes=writes,
        bus_work_ns=work,mean_bus_fraction=work/horizon,peak_any_1ms_fraction=peak/1000000,
        peak_window_start_relative_ns=peak_at,permissions=permissions,
        model_full_service_ns=PERIOD if cuts else None,hardware_ARM_time_ns=None,whole_mission_Q_inferred=False,
        injections=injections,memory_samples_checked=memory_samples,full_domain_state_checked=state_checked,
        first_exceedance_relative_ns=None if mem.first_exceedance is None else mem.first_exceedance-t0,
        remaining_error_positions=sum(len(e) for e in mem.errors.values()),
        application_completed=len(replies),max_credits=maxcredits,application_work_ns=app_work,
        control_corrective_extra_ns=control_extra,
        max_application_delay_ns=max((t-offers[i][0] for i,t in replies),default=None),
        read_results=read_results,
        logical_data_words_changed=len(mem.data),never_written_words=W-len(mem.data))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stem');args=ap.parse_args()
    meta=json.loads((HERE/f'outputs/{args.stem}.json').read_text())
    p=HERE/f'outputs/{args.stem}.trace.ctz'
    if not p.exists():p=p.with_suffix('.gz')
    print(json.dumps(check(p,meta),indent=2))
