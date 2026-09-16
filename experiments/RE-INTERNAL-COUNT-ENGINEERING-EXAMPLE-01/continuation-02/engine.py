"""Grouped exogenous streams and delayed full-word executor.

Only accepted _choose/_observe/_analog_next are shared with RES-003.
The controller receives its own completed count, q/slack and relative time.
"""
import hashlib, math
import numpy as np
from numba import njit
from reference import ROOT, config, accepted

@njit(cache=True)
def translate(template, offsets, ids, chips, shifts, lanes, W):
    n=len(ids); capacity=n*int(np.max(np.diff(offsets)))
    loc=np.empty(capacity,np.int32); masks=np.empty(capacity,np.uint64)
    ptr=np.empty(n+1,np.int64);ptr[0]=0;k=0
    for i in range(n):
        begin=k
        for j in range(offsets[ids[i]],offsets[ids[i]+1]):
            v=template[j];w=(v//16)^shifts[i];b=(v%16)^lanes[i];chip=chips[i]
            if w>=W or (chip==2 and b>=7):continue
            pos=chip*16+b; found=-1
            for l in range(begin,k):
                if loc[l]==w:found=l;break
            if found>=0:masks[found]^=np.uint64(1)<<np.uint64(pos)
            else:
                loc[k]=w;masks[k]=np.uint64(1)<<np.uint64(pos);k+=1
        ptr[i+1]=k
    return ptr,loc[:k],masks[:k]

def stream(seed,case,trial,c=None):
    c=config() if c is None else c
    rng=np.random.default_rng(np.random.SeedSequence([seed,case,trial]))
    H=c['horizon_seconds'];D=c['environment']['mean_dwell_seconds'][0]
    import json
    meta=json.loads((ROOT/'inputs/manifest.json').read_text(encoding='utf-8'))
    templates=np.load(ROOT/'inputs/templates.npz')
    merged=case==2
    points=templates['merged_points' if merged else 'points']; off=templates['merged_offsets' if merged else 'offsets']
    high=c['environment']['b_high'] if case==1 else 3*(len(off)-1)/meta['total_duration_s']
    z=int(rng.integers(2));t=0.;epochs=[];segments=[]
    while t<H:
        end=min(H,t+rng.exponential(D));rate=high*(c['environment']['low_flux_fraction'] if z==0 else 1)
        number=rng.poisson(rate*(end-t))
        epochs.append(np.sort(rng.uniform(t,end,number)));segments.append((t,end,z,rate))
        t=end;z=1-z
    times=np.concatenate(epochs);n=len(times);hasher=hashlib.sha256(times.tobytes())
    if case==1:
        loc=rng.integers(c['memory']['words'],size=n,dtype=np.int32)
        bits=rng.integers(39,size=n,dtype=np.uint64);masks=np.left_shift(np.uint64(1),bits)
        ptr=np.arange(n+1,dtype=np.int64);hasher.update(loc.tobytes());hasher.update(masks.tobytes())
    else:
        ids=rng.integers(len(off)-1,size=n,dtype=np.int32);chips=rng.integers(3,size=n,dtype=np.int32)
        shifts=rng.integers(2**21,size=n,dtype=np.int32);lanes=rng.integers(16,size=n,dtype=np.int32)
        for a in (ids,chips,shifts,lanes):hasher.update(a.tobytes())
        ptr,loc,masks=translate(points,off,ids,chips,shifts,lanes,c['memory']['words'])
    # Empty parents are retained in the hash, but cannot affect execution.
    keep=np.flatnonzero(np.diff(ptr)>0)
    endptr=np.r_[ptr[keep],len(loc)].astype(np.int64)
    return times[keep],endptr,loc,masks,hasher.hexdigest(),np.array(segments),n

@njit(cache=True)
def advance(w,stop,scan,step,delay,epoch,mask,seen,stage,pending,epoch_id):
    """Commit before group; latch after a tied group. Return acknowledged writes."""
    if seen[w]!=epoch_id:seen[w]=epoch_id;stage[w]=0;pending[w]=False
    completion=scan+(w+1)*step;latch=completion-delay
    if stage[w]==0 and latch<stop:
        pending[w]=mask[w]!=0;stage[w]=1
    if stage[w]==1 and completion<=stop:
        dirty=pending[w]
        if dirty:mask[w]=0
        pending[w]=False;stage[w]=2
        return int(dirty)
    return 0

@njit(cache=True)
def read_reservation(scan,stop,W,step):
    """Service reservation last half-slot; read first 20 ns of reservation."""
    elapsed=max(0.,min(W*step,stop-scan));whole=min(W,int(elapsed/step));rem=max(0.,elapsed-whole*step)
    reserved=whole*step/2+max(0.,rem-step/2)
    read_time=whole*step/10+min(step/10,max(0.,rem-step/2))
    reads=whole+int(whole<W and rem>=step*.6)
    return reserved,read_time,reads

@njit(cache=True)
def run(times,ptr,locations,marks,policy,packed,delay,record=False):
    (kernels,transition,H,J,constant,coefficient,first,second,periods,ticks,initial,slack0,
     W,P,horizon,dwell,low,high,tick)=packed
    kind=int(policy[0]);q=initial.copy();slack=slack0;step=P/W
    mask=np.zeros(W,np.uint64);seen=np.zeros(W,np.int32);stage=np.zeros(W,np.uint8)
    pending=np.zeros(W,np.bool_);listed=np.zeros(W,np.bool_);active=np.empty(W,np.int32);active_n=0
    total_ticks=int(round(horizon/tick));time_tick=0;idx=0;passes=0;updates=0;writes=0;reads=0
    bus=0.;reservation=0.;epoch_id=0;previous_count=-1;minimum_likelihood=1.;max_count=0;partial=0.
    trace=np.zeros((total_ticks+1,9)) if record else np.zeros((1,9));tr=0
    a=int(policy[1]);ms=policy[3];cap=policy[4];growth=policy[5];zero=int(policy[6])
    if kind==4:
        m=1+2*W*ms/(((low+high)/2)*horizon)
        a=accepted._floor_action(min(horizon*m*(m-1)/(2*ms*W),cap),periods)
    failed=False;failure_time=horizon;computation_failure=0
    while time_tick<total_ticks:
        now=time_tick*tick;remaining=total_ticks-time_tick
        if kind<2:
            a,slack,_,_,_=accepted._choose(q,slack,remaining,H,J,constant,coefficient,first,second,ticks,tick,W,dwell,low,high)
        elif kind==2:a=int(policy[1])
        elif kind==3:a=int(policy[1] if now<horizon/2 else policy[2])
        end=(time_tick+ticks[a])*tick;limit=min(end,horizon);scan=end-P;epoch_id+=1;count=0
        # Every active word's latch/commit is processed before its next group,
        # or at this interval's end. These operations cannot create E_cap.
        while idx<len(times) and times[idx]<=limit:
            t=times[idx]
            for e in range(ptr[idx],ptr[idx+1]):
                w=locations[e]
                if not listed[w]:listed[w]=True;active[active_n]=w;active_n+=1
                count+=advance(w,t,scan,step,delay,epoch_id,mask,seen,stage,pending,epoch_id)
            # All bits of each word, and all words of the group, change atomically.
            hit=False
            for e in range(ptr[idx],ptr[idx+1]):
                w=locations[e];mask[w]^=marks[e]
                if mask[w] and mask[w]&(mask[w]-np.uint64(1)):hit=True
            idx+=1
            if hit:failed=True;failure_time=t;limit=t;break
        # Flush all other words to the same stop time, including pending writes.
        kept=0;started_writes=0;partial_write_bus=0.
        for j in range(active_n):
            w=active[j]
            count+=advance(w,limit,scan,step,delay,epoch_id,mask,seen,stage,pending,epoch_id)
            completion=scan+(w+1)*step
            if stage[w]==1 and pending[w]:
                started_writes+=int(limit>=completion-4e-8)
                partial_write_bus+=min(2e-8,max(0.,limit-(completion-4e-8)))
            if mask[w]!=0 or pending[w]:active[kept]=w;kept+=1
            else:listed[w]=False
        active_n=kept
        r,rt,nread=read_reservation(scan,limit,W,step)
        reservation+=r;bus+=rt+count*2e-8+partial_write_bus;reads+=nread;writes+=count
        partial=r/(P/2) if limit<end else 0.
        max_count=max(max_count,count)
        if record:
            trace[tr]=np.array([now,periods[a],limit,count,slack,q[len(q)//2:].sum(),active_n,int(failed),reservation]);tr+=1
        if limit>=end:passes+=1
        if failed:break
        if end>horizon:break
        updates+=int(kind<2 or kind==4)
        if kind<2:
            q,likelihood=accepted._observe(q,a,count,kind==0,kernels,transition)
            if not np.isfinite(q).all() or likelihood<=0:
                computation_failure=1;break
            minimum_likelihood=min(minimum_likelihood,likelihood)
        elif kind==4:
            a=accepted._analog_next(count,previous_count,a,ms,cap,growth,zero,periods,W,horizon)
            previous_count=count
        time_tick+=ticks[a] if kind!=4 else int(round((end-now)/tick))
    return np.array([int(failed),failure_time,passes,partial,reads,writes,bus,reservation,updates,max_count,minimum_likelihood,computation_failure]),trace[:tr]
