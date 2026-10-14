"""Original full-timer C versus raw-event deadlines; no policy retuning.

Tests the conditional theorem's functional bridge, not CPU execution time.
collect only constructs packets; its expected state comes from independent
Oracle, which consumes every event. Production code is loaded unchanged.
"""
import ctypes as C
import hashlib
import json
import random
from pathlib import Path
from batch_model import collect
from verify import State
from verify_batch import Batch, BatchState, Decision, native_library, decision_expected

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE/'config.json').read_text())
NW, NH, NR, PAIR = (CFG[k] for k in ('NW','NH','NR','PAIR_WINDOW'))


def cases():
    # 1 second is a test input, NOT an ARM WCET or proposed service upper.
    step = 50000000
    yield 'startup', [(step, []), (NR-1, []), (NR, []), (NR+1, [])]
    for delta in (-1, 0, 1):
        t = NR+step
        src = 5*t
        second = t+(PAIR+delta+4)//5+10
        yield 'pair_'+str(delta), [(NR, []), (t, [(t,src,1,0)]),
              (second, [(second,src+PAIR+delta,1,0)]),
              (second+NW, []), (second+NH, [])]
    yield 'internal_recovery', [(NR, []), (NR+step,
       [(NR+1,5*(NR+1),0,1), (NR+2,5*(NR+2),0,0),
        (NR+3,5*(NR+3),1,0)]), (2*NR+1, []), (2*NR+2, [])]
    yield 'loss_remains', [(NR, []), (NR+1, [(NR+1,5*NR,0,1)]),
                          (10*NR, []), (10*NR+1, [(10*NR+1,50*NR,0,0)]),
                          (11*NR+1, [])]
    yield 'event_at_expiry', [(NR-1, []), (NR, [(NR,5*NR,1,0)]),
                             (NR+NW-1, []), (NR+NW, [])]
    yield 'loss_burst_2002', [(2003, [(i,5*i,0,i%2) for i in range(1,2003)]),
                             (NR+2002, [])]
    # Ten consecutive ~44-second batches (near the sufficient ceiling).
    # Each batch contains multiple ERR; no hidden limit on mission ERR count.
    groups=[]; t=NR
    for _ in range(10):
        end=t+2200000000
        groups.append((end,[(q,5*q,1,0) for q in range(t+1,end,10000000)]))
        t=end
    groups += [(t+NH, [])]
    yield 'continuous_err', groups
    # Chosen 1ms service allocation: 49999 ticks, not 50000, once the
    # declared +10ppm period and jitter envelope are included. This is an
    # injected bounded-service trace, NOT a CPU execution-time measurement.
    origin=NR+step
    groups=[(origin,[])]
    previous_loss=False
    for i in range(20):
        begin=origin+i*49999;end=begin+49999
        loss=i%4==1
        err=i%3==0
        records=[(begin+1,5*(begin+1),int(err),int(loss))] if err or loss!=previous_loss else []
        if i%4==2:
            records.append((end,5*end,1,0))
        previous_loss=loss
        groups.append((end,records))
    groups.append((end+NR+NH,[]))
    yield 'selected_ms_round',groups
    # Bounded randomized shapes, fixed seed; full-size words/times.
    rng=random.Random(10520261016)
    for case in range(100):
        groups=[]; t=0; loss=0
        for _ in range(40):
            span=rng.choice((1,50,step,2200000000))
            end=t+span
            events=[]
            slots=sorted(rng.sample(range(t+1,end+1),min(span,rng.randrange(9))))
            for q in slots:
                if rng.randrange(4)==0: loss=1-loss
                events.append((q,5*q-1,rng.randrange(2),loss))
            groups.append((end,events));t=end
        groups.append((t+NR+NH, []))
        yield 'random_'+str(case), groups


def main():
    lib=native_library();rows=[];packets=events=0
    for name,groups in cases():
        state=BatchState();lib.t105_batch_init(C.byref(state))
        deadlines=[]
        for values,expected in collect(0,groups):
            b=Batch(*values)
            assert lib.t105_batch_apply(C.byref(state),C.byref(b)),(name,values)
            actual=tuple(getattr(state.rule,k) for k,_ in State._fields_)
            assert actual==expected,(name,values,actual,expected)
            d=Decision();assert lib.t105_decide(C.byref(state),C.byref(d))
            assert tuple(getattr(d,k) for k,_ in Decision._fields_)==decision_expected(values[0],expected)
            deadlines.append([values[3],values[2],d.not_before,d.flags])
            packets+=1;events+=values[10]
        rows.append({'case':name,'packets':len(groups),'last':deadlines[-1],
                     'deadlines_sha256':hashlib.sha256(json.dumps(deadlines).encode()).hexdigest()})
    # Counterexample to arbitrary sleeping/aggregation: span exceeds PAIR.
    # Actual C refuses it (safe fault, but not the priced ordinary behavior).
    later=(PAIR+1+4)//5+1
    values,_=collect(0,[(later,[(1,0,1,0),(later,PAIR+1,1,0)])])[0]
    state=BatchState();lib.t105_batch_init(C.byref(state))
    accepted=lib.t105_batch_apply(C.byref(state),C.byref(Batch(*values)))
    d=Decision();lib.t105_decide(C.byref(state),C.byref(d))
    assert not accepted and d.flags==2
    # Hand-checkable counterexample to moving holds to CPU completion.
    # Nominal units: event at tick100, CPU response 50 million ticks later.
    event_tick=100;cpu_delay=50000000
    exact=event_tick+NW;wrong=event_tick+cpu_delay+NW
    assert wrong-exact==cpu_delay
    # Actual C witness separating processed_G freshness and mature permit.
    # One event just after a cut, a 1ms cut period, reply by the second cut.
    # The initial NR has expired; no CPU timer reset is used.
    origin=10000000000;period=50000
    witness=collect(0,[(origin-1,[]),
        (origin+period-1,[(origin+1,5*(origin+1),1,0)])])
    state=BatchState();lib.t105_batch_init(C.byref(state))
    for vals,expected in witness:
        assert lib.t105_batch_apply(C.byref(state),C.byref(Batch(*vals)))
    wd=Decision();assert lib.t105_decide(C.byref(state),C.byref(wd))
    reply=origin+2*period-1
    assert wd.not_before==origin+1+NW and wd.generation==1 and wd.flags==1
    assert (reply-(origin+1))*20>10000 and reply<wd.not_before
    result={'status':'PASS functional preparation checks; NOT hardware time',
        'cases':rows,'packet_count':packets,'raw_event_count':events,
        'full_timer_constants':{k:CFG[k] for k in ('NW','NH','NR','PAIR_WINDOW')},
        'unbounded_summary_counterexample':{'batch':list(values),'C_accepts':bool(accepted),'decision_flags':d.flags},
        'CPU_epoch_mutant':{'correct_deadline_tick':exact,'wrong_deadline_tick':wrong,
                           'unpaid_extra_FAST_nominal_ns':cpu_delay*20},
        'late_delivery_counterexample':{'deadline_tick':exact,'delivery_tick':exact+500,
                                       'late_by_nominal_ns':10000},
        'literal_fresh_history_counterexample':{
            'cut_period_nominal_ns':period*20,'event_tick':origin+1,
            'reply_tick':reply,'processed_G_delay_nominal_ns':(reply-origin-1)*20,
            'actual_C_not_before':wd.not_before,'generation':wd.generation,
            'preparation_lead_nominal_ns':(wd.not_before-reply)*20,
            'note':'violates literal10us processed_G, does not delay the future rule expiry; not an ARM timing measurement'},
        'independence':'raw absolute deadlines vs C countdown; shared inputs/ABI/ctypes loader only',
        'CPU_upper_ns':None}
    (HERE/'outputs/advance-functional.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Advance C/raw-oracle:',len(rows),'cases,',packets,'packets,',events,'events; negative cases rejected')


if __name__=='__main__':main()
