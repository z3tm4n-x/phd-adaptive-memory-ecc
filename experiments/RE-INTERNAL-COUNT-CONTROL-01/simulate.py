"""Exact marked-event simulation of actual 32-bit SEC words.

This simulator never generates observations from the auxiliary filter. Each
controller receives counts from its own actual sequential checks. Common
external marked streams are permitted only as paired random numbers.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
from numba import njit
from core import Model


@dataclass
class Packed:
    kernels: np.ndarray
    transition: np.ndarray
    H: np.ndarray
    J: np.ndarray
    constant: np.ndarray
    coefficient: np.ndarray
    first: np.ndarray
    second: np.ndarray
    periods: np.ndarray
    ticks: np.ndarray
    initial: np.ndarray
    slack: float
    words: int
    pass_seconds: float
    horizon: float
    dwell: float
    low: float
    high: float
    tick: float


def pack(model: Model,epsilon=0.1):
    K=model.cfg['controller']['pending_cap'];L=K+1
    H=np.empty((len(model.periods),2,2));J=np.empty_like(H)
    for a in range(len(model.periods)):
        for z in range(2):
            for zz in range(2):
                row=model.transition[a,z*L,zz*L:(zz+1)*L]
                H[a,z,zz]=row.sum();J[a,z,zz]=row@np.arange(L)
    constant=np.column_stack([model.value[:,0],model.value[:,L]])
    coefficient=np.column_stack([model.value[:,1]-model.value[:,0],model.value[:,L+1]-model.value[:,L]])
    first=np.column_stack([model.reward[:,1]-model.reward[:,0],model.reward[:,L+1]-model.reward[:,L]])
    second=np.column_stack([model.reward[:,0],model.reward[:,L]])
    slack=epsilon-model.error['whole_horizon_delta']-float(model.initial@model.value[-1])
    if slack<0: raise ValueError('initial budget has no certified backup')
    cfg=model.cfg
    return Packed(model.kernels,model.transition,H,J,constant,coefficient,first,second,
                  model.periods,model.ticks,model.initial,slack,cfg['memory']['words'],
                  cfg['memory']['pass_seconds'],cfg['horizon_seconds'],model.dwell,
                  cfg['environment']['b_low'],cfg['environment']['b_high'],cfg['controller']['time_tick_seconds'])


@njit(cache=True)
def _moments(t,dwell,low,high):
    k=2/dwell;x=k*t;m=(low+high)/2;d=(high-low)/2
    A=-math.expm1(-x)/k
    if x<.2:
        term=.5;B=term
        for j in range(1,18): term*=-x/(j+2);B+=term
        B*=t*t
    else: B=(t-A)/k
    base=m*m*t*t+2*d*d*B
    return m*t-d*A,m*t+d*A,max(0.,base-2*m*d*t*A),base+2*m*d*t*A


@njit(cache=True)
def _stats(q):
    L=len(q)//2;p0=p1=k0=k1=0.
    for k in range(L):
        p0+=q[k];k0+=k*q[k];p1+=q[L+k];k1+=k*q[L+k]
    return p0,p1,k0,k1


@njit(cache=True)
def _choose(q,slack,remaining,H,J,constant,coefficient,first,second,ticks,tick,words,dwell,low,high):
    p0,p1,k0,k1=_stats(q)
    val=p0*constant[remaining,0]+p1*constant[remaining,1]+k0*coefficient[remaining,0]+k1*coefficient[remaining,1]
    for a in range(len(ticks)-1,-1,-1):
        dt=min(remaining,ticks[a]);nextrem=remaining-dt
        if ticks[a]>remaining:
            m0,m1,s0,s1=_moments(dt*tick,dwell,low,high)
            one=(k0*m0+k1*m1+.5*(p0*s0+p1*s1))/words
            D=one-val
        else:
            one=p0*second[a,0]+p1*second[a,1]+k0*first[a,0]+k1*first[a,1]
            future0=H[a,0,0]*constant[nextrem,0]+H[a,0,1]*constant[nextrem,1]+J[a,0,0]*coefficient[nextrem,0]+J[a,0,1]*coefficient[nextrem,1]
            future1=H[a,1,0]*constant[nextrem,0]+H[a,1,1]*constant[nextrem,1]+J[a,1,0]*coefficient[nextrem,0]+J[a,1,1]*coefficient[nextrem,1]
            D=one+p0*future0+p1*future1-val
        if D<=slack*dt/remaining+1e-13:
            return a,max(0.,slack-D),D,one,val
    raise ValueError('lost backup')


@njit(cache=True)
def _observe(q,a,count,enabled,kernels,transition):
    y=min(count,kernels.shape[1]-1);S=len(q);new=np.zeros(S)
    for i in range(S):
        for j in range(S):
            new[j]+=q[i]*(kernels[a,y,i,j] if enabled else transition[a,i,j])
    likelihood=new.sum()
    if likelihood<=0: raise ValueError('zero likelihood')
    new/=likelihood
    return new,likelihood


@njit(cache=True)
def _floor_action(raw,periods):
    a=0
    for j in range(len(periods)):
        if periods[j]<=raw+1e-12: a=j
    return a


@njit(cache=True)
def _analog_next(count,previous_count,current_a,ms,cap,growth,zero_mode,periods,words,horizon):
    # SOURCE (10) then (9); ambiguity of the source cross-reference is explicit.
    tau=periods[current_a]
    if count==previous_count: return current_a
    if count==0:
        raw=tau if zero_mode==0 else tau*growth
    else:
        m2=1+2*words*ms*tau/(count*horizon)
        raw=horizon*m2*(m2-1)/(2*ms*words)
    raw=min(raw,cap,tau*growth)
    return _floor_action(raw,periods)


@njit(cache=True)
def _stream(seed,horizon,dwell,low,high,words,bits_per_word):
    np.random.seed(seed)
    capacity=int(2*high*horizon+2000)
    times=np.empty(capacity);locations=np.empty(capacity,np.int32);bits=np.empty(capacity,np.int8)
    z=0 if np.random.random()<.5 else 1;t=0.;count=0
    while t<horizon:
        end=min(horizon,t+np.random.exponential(dwell))
        rate=low if z==0 else high
        e=t+np.random.exponential(1/rate)
        while e<end:
            if count>=capacity: raise ValueError('event buffer exceeded; do not truncate a trial')
            times[count]=e;locations[count]=np.random.randint(words);bits[count]=np.random.randint(bits_per_word);count+=1
            e+=np.random.exponential(1/rate)
        t=end;z=1-z
    return times[:count],locations[:count],bits[:count]


@njit(cache=True)
def _run(times,locations,eventbits,kind,first_a,second_a,ms,cap,growth,zero_mode,
         kernels,transition,H,J,constant,coefficient,first,second,periods,ticks,initial,slack0,
         words,pass_seconds,horizon,dwell,low,high,tick,
         bitstate,error_time,position,active,trace,record):
    # kinds: 0 proposed, 1 count-disabled, 2 Fixed, 3 Precomputed, 4 PA-DOM adaptation
    q=initial.copy();slack=slack0;total_ticks=int(round(horizon/tick))
    time_tick=0;event_index=0;active_n=0;passes=0;updates=0;row=0;sum_reward=0.
    previous_count=-1
    if kind==4:
        rate=(low+high)/2;m=1+2*words*ms/(rate*horizon)
        raw=horizon*m*(m-1)/(2*ms*words)
        current_a=_floor_action(min(raw,cap),periods)
    else: current_a=first_a
    failure=False;failure_time=horizon;partial_busy=0.
    while time_tick<total_ticks:
        t=time_tick*tick;remaining=total_ticks-time_tick
        qbefore=q;sbefore=slack;D=one=val=0.
        if kind<=1:
            current_a,slack,D,one,val=_choose(q,slack,remaining,H,J,constant,coefficient,first,second,ticks,tick,words,dwell,low,high)
            sum_reward+=one
        elif kind==2: current_a=first_a
        elif kind==3: current_a=first_a if t<horizon/2-1e-10 else second_a
        tau=periods[current_a];full_end=t+tau;end=min(horizon,full_end);scan_start=full_end-pass_seconds
        count=0
        while event_index<len(times) and times[event_index]<end-1e-12:
            e=times[event_index];w=locations[event_index];bit=eventbits[event_index]
            if bitstate[w]>=0:
                reset=scan_start+(w+1)*pass_seconds/words
                if error_time[w]<reset<=e:
                    # An actual correction already happened in this pass.
                    count+=1;bitstate[w]=bit;error_time[w]=e
                elif bitstate[w]==bit:
                    # A harmless repeat inversion; it is not an observation.
                    idx=position[w];last=active[active_n-1]
                    active[idx]=last;position[last]=idx;active_n-=1;bitstate[w]=-1
                else:
                    failure=True;failure_time=e;partial_busy=max(0.,min(pass_seconds,e-scan_start));break
            else:
                bitstate[w]=bit;error_time[w]=e;position[w]=active_n;active[active_n]=w;active_n+=1
            event_index+=1
        if failure: break
        if full_end>horizon+1e-10:
            partial_busy=max(0.,min(pass_seconds,horizon-scan_start));break
        # Flush only those words whose individual check occurred AFTER the
        # remaining inversion. Early-scanned words can still be dirty now.
        idx=0
        while idx<active_n:
            w=active[idx];reset=scan_start+(w+1)*pass_seconds/words
            if error_time[w]<reset:
                count+=1;last=active[active_n-1];active[idx]=last;position[last]=idx;active_n-=1;bitstate[w]=-1
            else: idx+=1
        passes+=1
        nexttick=time_tick+ticks[current_a]
        likelihood=1.
        if kind<=1 and nexttick<total_ticks:
            q,likelihood=_observe(q,current_a,count,kind==0,kernels,transition);updates+=1
        if kind==4 and nexttick<total_ticks:
            next_a=_analog_next(count,previous_count,current_a,ms,cap,growth,zero_mode,periods,words,horizon)
            previous_count=count;updates+=1
        else: next_a=current_a
        if record and row<len(trace):
            pb0,pb1,kb0,kb1=_stats(qbefore);pa0,pa1,ka0,ka1=_stats(q)
            upcoming=-1.
            if kind<=1 and nexttick<total_ticks:
                aa,_,_,_,_=_choose(q,slack,total_ticks-nexttick,H,J,constant,coefficient,first,second,ticks,tick,words,dwell,low,high)
                upcoming=periods[aa]
            elif kind==4: upcoming=periods[next_a]
            trace[row,0]=t;trace[row,1]=tau;trace[row,2]=full_end;trace[row,3]=count
            trace[row,4]=pb1;trace[row,5]=pa1;trace[row,6]=kb0+kb1;trace[row,7]=ka0+ka1
            trace[row,8]=sbefore;trace[row,9]=slack;trace[row,10]=D;trace[row,11]=one
            trace[row,12]=val+sbefore;trace[row,13]=likelihood;trace[row,14]=upcoming
            trace[row,15]=sum_reward;trace[row,16]=active_n;row+=1
        current_a=next_a;time_tick=nexttick
    for j in range(active_n): bitstate[active[j]]=-1
    # Declared within-word operation order: (read,write) for four addresses.
    op_seconds=pass_seconds/(8*words)
    partial_ops=int(math.floor(partial_busy/op_seconds+1e-9))
    reads=passes*4*words+(partial_ops+1)//2;writes=passes*4*words+partial_ops//2
    busy=passes*pass_seconds+partial_busy
    return np.array([(1.0 if failure else 0.0),float(passes),busy,float(reads),float(writes),failure_time,float(updates),sum_reward,float(row)])


def args(p: Packed):
    return (p.kernels,p.transition,p.H,p.J,p.constant,p.coefficient,p.first,p.second,p.periods,p.ticks,p.initial,p.slack,
            p.words,p.pass_seconds,p.horizon,p.dwell,p.low,p.high,p.tick)


@njit(cache=True)
def _batch(n,seed,policies,kernels,transition,H,J,constant,coefficient,first,second,periods,ticks,initial,slack,
           words,pass_seconds,horizon,dwell,low,high,tick):
    output=np.empty((n,len(policies),8));bitstate=np.full(words,-1,np.int8)
    error_time=np.empty(words);position=np.empty(words,np.int32);active=np.empty(words,np.int32)
    trace=np.empty((0,17))
    for i in range(n):
        times,locations,bits=_stream(seed+i,horizon,dwell,low,high,words,32)
        for j in range(len(policies)):
            pol=policies[j]
            result=_run(times,locations,bits,int(pol[0]),int(pol[1]),int(pol[2]),pol[3],pol[4],pol[5],int(pol[6]),
                kernels,transition,H,J,constant,coefficient,first,second,periods,ticks,initial,slack,
                words,pass_seconds,horizon,dwell,low,high,tick,bitstate,error_time,position,active,trace,False)
            output[i,j]=result[:8]
    return output


def batch(p: Packed,n: int,seed: int,policies: list[list[float]]):
    return _batch(n,seed,np.array(policies,float),*args(p))


def run_trace(p: Packed,seed: int,kind=0):
    times,locations,bits=_stream(seed,p.horizon,p.dwell,p.low,p.high,p.words,32)
    trace=np.empty((int(p.horizon/min(p.periods))+1,17));state=np.full(p.words,-1,np.int8)
    result=_run(times,locations,bits,kind,2,2,0.01,300.,3.,1,*args(p),state,np.empty(p.words),
                np.empty(p.words,np.int32),np.empty(p.words,np.int32),trace,True)
    return result,trace[:int(result[8])]
