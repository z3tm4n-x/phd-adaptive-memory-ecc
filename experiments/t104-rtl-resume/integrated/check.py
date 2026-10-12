"""Independent trace checks; old E and T114 definitions remain read-only.

The checker consumes actual vendor-XPM simulation, not a test transport stub.
Costs from stress traces are NOT substituted into the T135 envelope.
"""
import argparse
import hashlib
import json
import re
import os
from pathlib import Path
import subprocess
import sys
import time
import zlib

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from reference import ETransaction,Request,ServiceConfig

def check(path):
    offers={};accepts=[];replies=[];events=[];history=[];app_grants=[]
    releases={};grants={};pin_checks=0;skips=0;freezes={0:True,1:True}
    calendar=ServiceConfig(words=16).validate()
    slot_index=0;freeze_index=2;candidate_count=0;veto_edges=0
    rule_gen=0;short=long=0;recovery=130;healthy=True;rule_started=False
    last_err=None;pending_event=None
    max_credit=0;max_reply=0;max_response=0
    latest_generation=0;leases={};beacons={};sent_candidates={};eligible=[];candidate_latencies=[]
    rule_start=None;mission_start=None
    for line in path.read_text().splitlines():
        f=line.split()
        if not f:continue
        k=f[0]
        if k=='OFFER':
            packet=int(f[3],16);ident=packet>>57
            offers[ident]=(int(f[1]),int(f[2]),packet)
        elif k=='ACCEPT':
            packet=int(f[3],16);ident=packet>>57
            assert packet==offers[ident][2]
            accepts.append(ident);max_credit=max(max_credit,len(accepts)-len(replies))
            assert max_credit<=2,'more than two unfinished requests'
        elif k=='EVENT':
            e=int(f[2],16);events.append((int(f[1]),e));latest_generation=e>>66
            leases.clear()
        elif k=='BEACON':beacons[int(f[2],16)]=int(f[1])
        elif k=='SEND':
            payload=int(f[2],16);assert (payload>>32)&((1<<64)-1)==rule_gen
            if (payload>>96)&1:assert healthy and not(short or long or recovery) and pending_event is None
            sent_candidates[payload]=int(f[1])
        elif k=='ELIGIBLE':eligible.append(int(f[1]))
        elif k=='RULE_START':
            rule_start=int(f[1]);assert mission_start is not None and 0<=rule_start-mission_start<=100000
        elif k=='HISTORY':
            pending_event=int(f[2],16);history.append((int(f[1]),pending_event))
        elif k=='RULE':
            # Actual synchronized calendar start is a separate observed input,
            # checked against mission t0; timers must not start before t0.
            t=int(f[1]);actual=[int(x,16) for x in f[2:]]
            was_started=rule_started
            if rule_start is not None:rule_started=True
            if was_started:
                short=max(0,short-1);long=max(0,long-1);recovery=max(0,recovery-1)
            if pending_event is not None:
                e=pending_event;gen=e>>66;stamp=(e>>2)&((1<<64)-1)
                loss=bool(e&2);err=bool(e&1)
                assert gen==rule_gen+1;rule_gen=gen
                if healthy is False and not loss:recovery=max(recovery,130)
                healthy=not loss
                if err:
                    short=40
                    if last_err is not None and stamp-last_err<=200:long=80
                    last_err=stamp
                pending_event=None
            # low is additionally masked by a newly visible next FIFO event;
            # test the state exactly, and any true LOW must be justified.
            assert actual[:4]==[rule_gen,short,long,recovery],(t,actual,[rule_gen,short,long,recovery])
            assert actual[5:]==[int(healthy),0]
            if actual[4]:assert rule_started and healthy and not(short or long or recovery)
        elif k=='FREEZE':
            t=int(f[2])*4;pos=int(f[3]);permit,alarm,must=map(lambda x:int(x,16),f[4:7])
            assert t==calendar.start(freeze_index)-320,(freeze_index,t)
            assert pos==freeze_index%8 and must==calendar.mandatory(freeze_index)
            if permit:
                assert not alarm
                assert leases.get((freeze_index//8)%16)==(latest_generation,True),'stale/unprocessed LOW'
            freezes[freeze_index]=bool(must or not permit or alarm)
            veto_edges+=alarm;freeze_index+=1
        elif k=='SLOT':
            if mission_start is None:mission_start=int(f[1])
            t=int(f[2])*4;execute,word,busy=map(lambda x:int(x,16),f[3:6])
            assert t==calendar.start(slot_index)
            assert word==calendar.address(slot_index)
            assert execute==freezes.pop(slot_index),('committed decision changed',slot_index)
            assert not busy
            skips+=not execute;slot_index+=1
        elif k=='GRANT':
            t,seq,app=int(f[1]),int(f[2]),int(f[3]);p=int(f[4],16)
            r=Request(p&3,(p>>2)&((1<<19)-1),(p>>21)&0xffffffff,(p>>53)&15)
            grants[seq]=(ETransaction(r,0),t,app)
            if app:
                ident=accepts[len(app_grants)];assert p==(offers[ident][2]&((1<<57)-1))
                app_grants.append((ident,seq));assert r.kind in (1,2)
            else:assert r.kind==0
        elif k=='PIN':
            seq,age=int(f[2]),int(f[3]);v=[int(x,16) for x in f[4:]]
            expected=grants[seq][0].step(age,v[16],bool(v[17]))
            keys=('busy','ce','oe','we','drive','alias','be','dout','sample','flag','done','commit','pending','data')
            assert v[:14]==[expected[x] for x in keys],(seq,age,v,expected)
            assert v[14]==grants[seq][0].request.word
            pin_checks+=1
        elif k=='RELEASE':releases[int(f[2])]=int(f[1])
        elif k=='REPLY':
            t,owner=int(f[1]),int(f[2]);p=int(f[3],16);ident=p>>33
            assert ident==accepts[len(replies)] and owner==offers[ident][1]
            seq=app_grants[len(replies)][1];tr=grants[seq][0]
            expected=ident<<33 | (tr.sampled_low|(tr.sampled_high<<16))<<1 | int(tr.request.kind!=1 and tr.latch_err)
            assert p==expected,(ident,p,expected)
            max_reply=max(max_reply,(t-releases[seq])/1000)
            max_response=max(max_response,(t-offers[ident][0])/1000)
            replies.append(ident)
        elif k=='CANDIDATE':
            t=int(f[1]);target=int(f[2],16);generation=int(f[3],16)
            payload=int(f[4],16);crc=int(f[5],16)
            assert zlib.crc32(payload.to_bytes(16,'little'))==crc
            assert payload in sent_candidates and payload>>97==0
            assert target==payload&0xffffffff
            assert ((payload>>32)&((1<<64)-1))==generation==latest_generation
            leases={k:v for k,v in leases.items() if k%4!=target%4}
            leases[target]=(generation,bool((payload>>96)&1))
            dt=(t-beacons[(target-2)%16])/1000
            assert dt<=1000,'candidate preparation/delivery'
            candidate_latencies.append(dt);candidate_count+=1
        elif k in ('ERROR:','FATAL:','Fatal:'):raise AssertionError(line)
    assert accepts==replies and len(replies)>0
    assert [e for _,e in events]==[e for _,e in history], 'lost or repeated history'
    assert skips>0 and veto_edges>0 and candidate_count>0
    assert len(eligible)==len(offers)
    input_latencies=[(t-offers[ident][0])/1000 for ident,t in zip(accepts,eligible)]
    assert 'PASS integrated' in path.read_text()
    return dict(requests=len(replies),slots=slot_index,skips=skips,pin_edges=pin_checks,
                history_events=len(events),max_history_delivery_ns=max((h[0]-e[0])/1000 for e,h in zip(events,history)),
                candidates=candidate_count,max_credits=max_credit,max_release_to_consumed_ns=max_reply,
                max_first_valid_to_eligible_ns=max(input_latencies),
                max_beacon_to_candidate_ns=max(candidate_latencies),
                max_first_valid_to_consumed_ns=max_response,sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--log',type=Path);ap.add_argument('--phase',type=int,default=0)
    ap.add_argument('--stress',type=int,default=0)
    ap.add_argument('--clocked',action='store_true')
    ap.add_argument('--mutant',choices=['stale-low','third-credit','revoke-frozen'])
    args=ap.parse_args()
    assert not(args.clocked and args.mutant)
    if args.log: print(json.dumps(check(args.log),indent=2));return
    build=BASE/'.build'/('integrated-'+str(time.time_ns()));build.mkdir(parents=True)
    log=build/'simulation.log'
    overrides=build/'overrides';overrides.mkdir()
    if args.mutant:
        file={'stale-low':'candidate_link.sv','third-credit':'executor.sv','revoke-frozen':'frame_engine.sv'}[args.mutant]
        source=(HERE/file).read_text()
        if args.mutant=='stale-low':
            source=source.replace('prepared_permit && !invalidate && !loss && !fault','prepared_permit && !fault')
            source=source.replace('==freeze_frame && !invalidate && !loss && !fault','==freeze_frame && !fault')
            source=source.replace('if(invalidate || loss) begin cache_low<=0; uninterrupted<=0; end','if(invalidate || loss) uninterrupted<=0;')
        elif args.mutant=='third-credit':source=source.replace('credits<2','credits<3')
        else:source=source.replace('if(start_wait==1 && slot_pos==0)',"if(alarm) decisions<=4'b1111;\n            if(start_wait==1 && slot_pos==0)")
        assert source!=(HERE/file).read_text()
        (overrides/file).write_text(source)
    with log.open('w') as out:
        r=subprocess.run([os.environ.get('VIVADO','/home/z3tm4n/bin/vivado-wsl'),'-mode','batch','-nojournal','-nolog',
            '-source',str(HERE/('clocked_sim.tcl' if args.clocked else 'sim.tcl')),'-tclargs',str(build/'xsim'),str(args.phase),str(args.stress),str(overrides)],
            stdout=out,stderr=subprocess.STDOUT,cwd=build,timeout=300)
    print('LOG',log,flush=True)
    assert r.returncode==0,log.read_text()[-5000:]
    if args.clocked:
        content=log.read_text();match=re.search(r'^CLOCKED_PASS .+$',content,re.M)
        assert match and 'Fatal:' not in content,content[-5000:]
        result=dict(clocked_top=True,status='passed',result=match[0],
                    log=str(log),sha256=hashlib.sha256(log.read_bytes()).hexdigest())
        (build/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2));return
    try:
        result=check(log)
    except AssertionError as e:
        if not args.mutant:raise
        # Syntax/elaboration failure is not a successful mutation rejection.
        assert 'GRANT ' in log.read_text() and ('PASS integrated' in log.read_text() or 'Fatal:' in log.read_text()),'not an executed sentinel'
        result=dict(mutant=args.mutant,rejected=True,reason=str(e),sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    else:
        assert not args.mutant,'mutant survived the independent checks'
    result.update(phase=args.phase,stress=args.stress,log=str(log))
    (build/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
