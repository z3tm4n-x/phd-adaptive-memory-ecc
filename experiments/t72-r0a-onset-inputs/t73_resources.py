"""Independent finite calendar, strip and FIFO checks (nanosecond units)."""
from bisect import bisect_right
from fractions import Fraction as F
from t73_calendar import Calendar


def periodic_work(start,length,width,period):
    def integral(t):
        q,r=divmod(t,period)
        return q*width+min(width,r)
    return integral(start+length)-integral(start)


def check_peak():
    checked=0
    for h in [1,45,91,181,182,239,240,241,1000,1000000]:
        bound=(h//240)*182+min(182,h%240)
        maximum=max(periodic_work(s,h,182,240) for s in range(240))
        assert maximum==bound
        checked+=240
    return checked


def fifo_delay(clock=F(1),pattern='full',offset=0):
    """Actual nonpreemptive 45ns requests with a declared aggregate envelope."""
    blocks=[]
    for frame in range(5000):
        for block in [0,1]:
            active=(pattern=='full' or ((frame*5+block*3)%7 not in [0,1,2]))
            if active:
                start=(240*frame+91*block)*clock
                blocks.append((start,start+91*clock))
    starts=[x[0] for x in blocks]
    jobs=[(F(offset),F(45)),(F(offset),F(45)),(F(offset),F(45)),(F(offset),F(10))]
    # Application burst45, rate.04; monitor burst100, rate.0001, all jobs<=45.
    jobs += [(F(offset+1125*k),F(45)) for k in range(1,600)]
    jobs += [(F(offset+450000*k),F(45)) for k in range(1,3)]
    jobs.sort(key=lambda x:x[0])
    ready=F(0);maximum=F(0)
    for arrival,duration in jobs:
        t=max(ready,arrival)
        while True:
            i=bisect_right(starts,t)-1
            if i>=0 and t<blocks[i][1]:
                t=blocks[i][1];continue
            nxt=i+1
            if nxt<len(blocks) and t+duration>blocks[nxt][0]:
                t=blocks[nxt][1];continue
            break
        ready=t+duration;maximum=max(maximum,ready-arrival)
    return maximum


def check_fifo():
    max_delay=F(0);cases=0
    for clock in [F(99999,100000),F(1),F(100001,100000)]:
        for pattern in ['full','switching']:
            for offset in [0,1,45,90,91,137,181,182,226,227,239]:
                d=fifo_delay(clock,pattern,offset)
                cplus=F(91)*F(100001,100000);gminus=F(120)*F(99999,100000)
                block=2*cplus+45;rate=1-block/(2*gminus)
                bound=block+145/rate
                assert d<=bound
                max_delay=max(max_delay,d);cases+=1
    return {'cases':cases,'max_observed_delay_ns_fraction':str(max_delay),'not_a_worst_case_proof':True}


def check_price_strips():
    cal=Calendar(8,3,2,3,2,1,5,250)
    w,d,lease,D=4,2,70,61
    bad_windows={3,4,12};err_times={17,19,55}
    bad_times=[0];extra=[];j=0;window=0
    for t in range(250):
        if t in err_times:cal.err(t);bad_times.append(t)
        if t>=w+d and (t-w-d)%w==0:
            bad=window in bad_windows
            cal.message(window,at=t,lease_end=window*w+lease,count=11 if bad else 0,k=10,qualified=True)
            if bad:bad_times.append(t)
            window+=1
        while cal.start(j)-cal.lead<=t and cal.start(j)<cal.horizon:
            act=cal.decide(j)
            if act and j%cal.ka:extra.append(cal.start(j))
            j+=1
    assert all(any(b<=t<=b+D for b in bad_times) for t in extra)
    assert len(extra)*cal.c<=F(cal.c,cal.g)*D*len(bad_times)
    return {'extra_slots':len(extra),'alarm_or_initial_strips':len(bad_times),'D_ticks':D,
            'all_extra_slots_covered':True,'consecutive_bad_windows_included':True}


def checks():
    return {'peak_phase_checks':check_peak(),'FIFO':check_fifo(),'price_strips':check_price_strips()}


if __name__=='__main__':
    import json
    print(json.dumps(checks(),indent=2))
