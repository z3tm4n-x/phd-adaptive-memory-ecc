"""Actual-bit marked-event simulation; auxiliary kernels never generate counts.

Lazy individual-word checks follow the accepted RES-003 scanner algorithm.
An independent explicit chronological scanner in tests audits this common path.
"""
from __future__ import annotations
import math
import numpy as np
from numba import njit
from model import choose,observe,retained
from known_reference import known_choose,known_observe


@njit(cache=True)
def stream(seed,H,D,lo,hi,W,n=32):
    np.random.seed(seed);capacity=int(2*hi*H+2000)
    ts=np.empty(capacity);ws=np.empty(capacity,np.int32);bs=np.empty(capacity,np.int8)
    z=0 if np.random.random()<.5 else 1;t=0.;k=0
    while t<H:
        end=min(H,t+np.random.exponential(D));rate=lo if z==0 else hi
        e=t+np.random.exponential(1/rate)
        while e<end:
            if k>=capacity:raise ValueError('Event buffer exceeded, no truncation allowed')
            ts[k]=e;ws[k]=np.random.randint(W);bs[k]=np.random.randint(n);k+=1
            e+=np.random.exponential(1/rate)
        t=end;z=1-z
    return ts[:k],ws[:k],bs[:k]


@njit(cache=True)
def floor_action(raw,periods):
    a=0
    for i in range(len(periods)):
        if periods[i]<=raw+1e-12:a=i
    return a


@njit(cache=True)
def analogue(count,previous,a,Ms,cap,growth,periods,W,H):
    if count==previous:return a
    tau=periods[a]
    if count==0:raw=tau*growth
    else:
        m=1+2*W*Ms*tau/(count*H);raw=H*m*(m-1)/(2*Ms*W)
    return floor_action(min(raw,cap,tau*growth),periods)


@njit(cache=True)
def run(ts,ws,bs,kind,Ms,cap,growth,
        kernels,reward,T,J,V,initial,slack0,rates,periods,ticks,threshold,
        knownK,knownT,knownJ,knownR,knownV,knownQ,knownSlack,
        W,P,H,D,lo,hi,tick,state,errtime,position,dirty,trace,record):
    # 0 learning, 1 frozen; 2 Fixed; 3 Precomputed; 4 PA-DOM; 5 known-D.
    M=len(rates);q=initial.copy();slack=slack0.copy();logs=np.zeros(M)
    rejected=np.zeros(M,np.bool_);active=np.ones(M,np.bool_)
    qk=knownQ.copy();sk=knownSlack;total=int(round(H/tick));now=0;ei=0;nd=0
    passes=0;updates=0;prev=-1;partial=0.;failure=False;ftime=H;row=0
    first_exclusion=-1.;first_action_effect=-1.;empty_time=-1.;removed=0
    backup=2;a=backup
    if kind==4:
        rate=(lo+hi)/2;m=1+2*W*Ms/(rate*H)
        a=floor_action(min(H*m*(m-1)/(2*Ms*W),cap),periods)
    while now<total:
        rem=total-now;t=now*tick;before_active=active.copy() if record else active;binding=-1
        old_cells=0
        if kind<=1:
            for jj in range(M-1):
                if not(rejected[jj] and rejected[jj+1]):old_cells|=1<<jj
        if kind<=1:
            a,slack,binding=choose(q,slack,active,rem,reward,T,J,V,ticks,tick,W,rates,lo,hi,backup)
        elif kind==2:a=2
        elif kind==3:a=3 if t<H/2-1e-10 else 2
        elif kind==5:a,sk=known_choose(qk,sk,rem,knownT,knownJ,knownR,knownV,ticks,W,D,lo,hi)
        end_full=t+periods[a];end=min(H,end_full);start=end_full-P;count=0
        while ei<len(ts) and ts[ei]<end-1e-12:
            e=ts[ei];w=ws[ei];bit=bs[ei]
            if state[w]>=0:
                reset=start+(w+1)*P/W
                if errtime[w]<reset<=e:
                    count+=1;state[w]=bit;errtime[w]=e
                elif state[w]==bit:
                    index=position[w];last=dirty[nd-1];dirty[index]=last;position[last]=index
                    nd-=1;state[w]=-1
                else:
                    failure=True;ftime=e;partial=max(0.,min(P,e-start));break
            else:
                state[w]=bit;errtime[w]=e;position[w]=nd;dirty[nd]=w;nd+=1
            ei+=1
        if failure:break
        if end_full>H+1e-10:
            partial=max(0.,min(P,H-start));break
        i=0
        while i<nd:
            w=dirty[i];reset=start+(w+1)*P/W
            if errtime[w]<reset:
                count+=1;last=dirty[nd-1];dirty[i]=last;position[last]=i;nd-=1;state[w]=-1
            else:i+=1
        passes+=1;nexttick=now+ticks[a];nxt=a;local_full=-1.;local_narrow=-1.
        if kind<=1 and nexttick<total:
            q=observe(q,logs,rejected,a,count,kernels,threshold,kind==0);updates+=1
            if kind==0:
                active=retained(rejected)
                newremoved=M-active.sum()
                new_cells=0
                for jj in range(M-1):
                    if not(rejected[jj] and rejected[jj+1]):new_cells|=1<<jj
                if new_cells!=old_cells and first_exclusion<0:first_exclusion=end_full
                if not active.any() and empty_time<0:empty_time=end_full
                if record and new_cells!=old_cells:
                    # A valid same-history comparison at the instant of removal.
                    # Before removal all formerly active constraints have valid slack.
                    af,_,_=choose(q,slack,before_active,total-nexttick,reward,T,J,V,ticks,tick,W,rates,lo,hi,backup)
                    an,_,_=choose(q,slack,active,total-nexttick,reward,T,J,V,ticks,tick,W,rates,lo,hi,backup)
                    local_full=periods[af];local_narrow=periods[an]
                    if an!=af and first_action_effect<0:first_action_effect=end_full
                removed=newremoved
        elif kind==4 and nexttick<total:
            nxt=analogue(count,prev,a,Ms,cap,growth,periods,W,H);prev=count;updates+=1
        elif kind==5 and nexttick<total:
            qk=known_observe(qk,a,count,knownK);updates+=1
        if record and row<len(trace):
            mask_before=old_cells;mask_after=0
            for jj in range(M-1):
                if not(rejected[jj] and rejected[jj+1]):mask_after|=1<<jj
            upcoming=-1.;slo=0.;shi=0.
            if kind<=1:
                slo=1e99;shi=-1e99
                for jj in range(M):
                    if active[jj]:slo=min(slo,slack[jj]);shi=max(shi,slack[jj])
                if nexttick<total:
                    aa,_,_=choose(q,slack,active,total-nexttick,reward,T,J,V,ticks,tick,W,rates,lo,hi,backup)
                    upcoming=periods[aa]
            elif kind==4:upcoming=periods[nxt]
            trace[row,0]=end_full;trace[row,1]=periods[a];trace[row,2]=count
            trace[row,3]=mask_before;trace[row,4]=mask_after;trace[row,5]=upcoming
            trace[row,6]=slo;trace[row,7]=shi;trace[row,8]=passes;trace[row,9]=nd
            trace[row,10]=local_full;trace[row,11]=local_narrow
            trace[row,12]=q[0,1]+q[0,3];trace[row,13]=q[-1,1]+q[-1,3]
            trace[row,14]=binding;trace[row,15]=sk
            bmin=1e99;bmax=-1e99
            if kind<=1:
                for jj in range(M):
                    if active[jj]:
                        vv=V[jj,max(0,total-nexttick)]
                        bb=(q[jj,0]+q[jj,2])*vv[0]+(q[jj,1]+q[jj,3])*vv[1]+q[jj,4]*vv[2]+q[jj,5]*vv[3]+slack[jj]
                        bmin=min(bmin,bb);bmax=max(bmax,bb)
            trace[row,16]=bmin;trace[row,17]=bmax;row+=1
        a=nxt;now=nexttick
    for i in range(nd):state[dirty[i]]=-1
    ops=int(math.floor(partial/(P/(8*W))+1e-9))
    final_cells=0
    for jj in range(M-1):
        if not(rejected[jj] and rejected[jj+1]):final_cells|=1<<jj
    return np.array([(1.0 if failure else 0.0),float(passes),passes*P+partial,
                     float(passes*4*W+(ops+1)//2),float(passes*4*W+ops//2),
                     ftime,float(updates),float(final_cells),first_exclusion,empty_time,float(row)])


@njit(cache=True)
def batch_core(n,seed,policies,kernels,reward,T,J,V,initial,slack0,rates,periods,ticks,threshold,
               knownK,knownT,knownJ,knownR,knownV,knownQ,knownSlack,W,P,H,D,lo,hi,tick):
    out=np.empty((n,len(policies),10));state=np.full(W,-1,np.int8);err=np.empty(W)
    pos=np.empty(W,np.int32);dirty=np.empty(W,np.int32);trace=np.empty((0,18))
    for i in range(n):
        ts,ws,bs=stream(seed+i,H,D,lo,hi,W)
        for j in range(len(policies)):
            pol=policies[j]
            r=run(ts,ws,bs,int(pol[0]),pol[1],pol[2],pol[3],kernels,reward,T,J,V,initial,slack0,rates,
                  periods,ticks,threshold,knownK,knownT,knownJ,knownR,knownV,knownQ,knownSlack,
                  W,P,H,D,lo,hi,tick,state,err,pos,dirty,trace,False)
            out[i,j]=r[:10]
    return out


def pack_args(bank,known,D):
    cfg=bank.cfg;cc=cfg['controller'];K,T,J,r,V,q,s,delta=known
    return (bank.kernels,bank.reward,bank.transition,bank.pending,bank.value,bank.initial,bank.slack,bank.rates,
            bank.periods,bank.ticks,math.log(cc['continuous_transfer_factor']/cc['beta'])+cc['test_log_margin'],
            K,T,J,r,V,q,s,cfg['memory']['words'],cfg['memory']['pass_seconds'],cfg['horizon_seconds'],float(D),
            cfg['environment']['b_low'],cfg['environment']['b_high'],cc['time_tick_seconds'])


def batch(bank,known,D,n,seed,policies):
    return batch_core(n,seed,np.asarray(policies,float),*pack_args(bank,known,D))


def trace_run(bank,known,D,seed,kind=0):
    cfg=bank.cfg;W=cfg['memory']['words'];H=cfg['horizon_seconds']
    ts,ws,bs=stream(seed,H,D,cfg['environment']['b_low'],cfg['environment']['b_high'],W)
    trace=np.empty((int(H/min(bank.periods))+1,18));state=np.full(W,-1,np.int8)
    r=run(ts,ws,bs,kind,.12,5.,3.,*pack_args(bank,known,D),state,np.empty(W),np.empty(W,np.int32),np.empty(W,np.int32),trace,True)
    return r,trace[:int(r[-1])]
