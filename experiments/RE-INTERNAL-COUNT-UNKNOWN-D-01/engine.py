"""Physical marked-event evaluation of the unknown-D policies.

The control payload deliberately has no true D or true environmental state.
The retained set is represented by a 32-bit cell mask, never by a fitted D.
The chronological lazy scanner shares the accepted simulator's physical
algorithm; verification.py also supplies a separately enumerated scanner and
an independently constructed killed CTMC.
"""
from __future__ import annotations
import math
import numpy as np
from numba import njit
import model
from upstream import known_sim,known_core

TRACE_COLUMNS=['start','period','end','own_count','cell_mask_before','cell_mask_after',
               'active_nodes_before','active_nodes_after','next_period','previous_set_local_period',
               'min_active_slack_before','min_active_slack_after','max_potential_after',
               'min_PrH_after','max_PrH_after','min_pending_mean','max_pending_mean','physical_pending_words']
RESULT_COLUMNS=['failure','passes','busy_seconds','reads','writes','stop_time','updates',
                'cell_mask','first_shrink_time','empty_set','final_active_nodes','trace_rows']


def payload(bank):
    c=bank.cfg
    return (bank.kernels,bank.transition,bank.pending,bank.first,bank.second,bank.value,
            bank.slack0,bank.rates,bank.periods,bank.ticks,c['controller']['time_tick_seconds'],
            c['environment']['b_low'],c['environment']['b_high'],c['memory']['words'],
            c['memory']['pass_seconds'],c['horizon_seconds'],
            math.log(c['controller']['continuous_transfer_factor']/c['controller']['beta'])+c['controller']['test_log_margin'],
            int(np.flatnonzero(bank.periods==c['controller']['backup_period_seconds'])[0]))

@njit(cache=True)
def cell_mask(rejected,learning):
    mask=np.int64(0)
    for j in range(len(rejected)-1):
        if not learning or not(rejected[j] and rejected[j+1]): mask|=np.int64(1)<<j
    return mask

@njit(cache=True)
def run_bank(times,locations,eventbits,learning,pay,bitstate,error_time,position,dirty,trace,record):
    kernels,T,J,m1,m2,V,slack0,rates,periods,ticks,tick,low,high,words,P,H,threshold,backup=pay
    M=len(rates);q=np.zeros((M,6));q[:,:2]=.5;slack=slack0.copy()
    scores=np.zeros(M);rejected=np.zeros(M,np.bool_);required=np.ones(M,np.bool_)
    total_ticks=int(round(H/tick));now=0;event_index=0;ndirty=0;passes=0;updates=0;row=0
    failed=False;stopped=H;partial_busy=0.;first_shrink=H;empty=False
    while now<total_ticks:
        remaining=total_ticks-now;t=now*tick
        aa=model.choose(remaining,q,slack,required,T,J,m1,m2,V,ticks,tick,rates,low,high,words,backup)
        before_mask=cell_mask(rejected,learning);before_n=np.sum(required);before_slack=0.
        required_before=required.copy() if record else required
        if record and before_n: before_slack=np.min(slack[required])
        model.spend(aa,remaining,q,slack,required,T,J,m1,m2,V,ticks,tick,rates,low,high,words,backup)
        full_end=t+periods[aa];end=min(H,full_end);scan_start=full_end-P;count=0
        while event_index<len(times) and times[event_index]<end-1e-12:
            e=times[event_index];w=locations[event_index];bit=eventbits[event_index]
            if bitstate[w]>=0:
                reset=scan_start+(w+1)*P/words
                if error_time[w]<reset<=e:
                    count+=1;bitstate[w]=bit;error_time[w]=e
                elif bitstate[w]==bit:
                    k=position[w];last=dirty[ndirty-1];dirty[k]=last;position[last]=k;ndirty-=1;bitstate[w]=-1
                else:
                    failed=True;stopped=e;partial_busy=max(0.,min(P,e-scan_start));break
            else:
                bitstate[w]=bit;error_time[w]=e;position[w]=ndirty;dirty[ndirty]=w;ndirty+=1
            event_index+=1
        if failed: break
        if full_end>H+1e-10:
            partial_busy=max(0.,min(P,H-scan_start));break
        k=0
        while k<ndirty:
            w=dirty[k];reset=scan_start+(w+1)*P/words
            if error_time[w]<reset:
                count+=1;last=dirty[ndirty-1];dirty[k]=last;position[last]=k;ndirty-=1;bitstate[w]=-1
            else: k+=1
        passes+=1;nexttick=now+ticks[aa]
        if nexttick<total_ticks:
            model.observe(aa,count,q,scores,rejected,required,kernels,learning,threshold);updates+=1
        after_mask=cell_mask(rejected,learning)
        if after_mask!=before_mask and first_shrink==H: first_shrink=full_end
        empty=empty or not np.any(required)
        if record:
            nr=total_ticks-nexttick;nextperiod=-1.;fullperiod=-1.;potential=0.;after_slack=0.
            if nr>0:
                nxt=model.choose(nr,q,slack,required,T,J,m1,m2,V,ticks,tick,rates,low,high,words,backup)
                nextperiod=periods[nxt]
                # Same updated observations and carried budgets, but retain
                # the PREVIOUS admissible set. This is a local diagnostic,
                # never a replay of the separate frozen-policy experiment.
                if after_mask!=before_mask:
                    previous_a=model.choose(nr,q,slack,required_before,T,J,m1,m2,V,ticks,tick,rates,low,high,words,backup)
                    fullperiod=periods[previous_a]
                if np.any(required):
                    after_slack=np.min(slack[required])
                    for j in range(M):
                        if required[j]:
                            pv=(q[j,0]+q[j,2])*V[j,nr,0]+(q[j,1]+q[j,3])*V[j,nr,1]+q[j,4]*V[j,nr,2]+q[j,5]*V[j,nr,3]+slack[j]
                            potential=max(potential,pv)
            trace[row,0]=t;trace[row,1]=periods[aa];trace[row,2]=full_end;trace[row,3]=count
            trace[row,4]=before_mask;trace[row,5]=after_mask;trace[row,6]=before_n;trace[row,7]=np.sum(required)
            trace[row,8]=nextperiod;trace[row,9]=fullperiod;trace[row,10]=before_slack;trace[row,11]=after_slack
            trace[row,12]=potential;trace[row,13]=np.min(q[:,1]+q[:,3]);trace[row,14]=np.max(q[:,1]+q[:,3])
            trace[row,15]=np.min(q[:,4]+q[:,5]);trace[row,16]=np.max(q[:,4]+q[:,5]);trace[row,17]=ndirty;row+=1
        now=nexttick
    for k in range(ndirty): bitstate[dirty[k]]=-1
    nops=int(math.floor(partial_busy/(P/(8*words))+1e-9))
    reads=passes*4*words+(nops+1)//2;writes=passes*4*words+nops//2
    return np.array([1. if failed else 0.,float(passes),passes*P+partial_busy,float(reads),float(writes),stopped,
                     float(updates),float(cell_mask(rejected,learning)),first_shrink,1. if empty else 0.,float(np.sum(required)),float(row)])

@njit(cache=True)
def mixed_batch(n,seed,true_d,pay,oldargs,ms,cap):
    words=pay[13];H=pay[15];low=pay[11];high=pay[12]
    data=np.full((n,6,12),np.nan)
    state=np.full(words,-1,np.int8);etime=np.empty(words);pos=np.empty(words,np.int32);dirty=np.empty(words,np.int32)
    newtrace=np.empty((0,18));oldtrace=np.empty((0,17))
    # original kinds: Fixed=2, Precomputed=3, PA-DOM=4, known-D RES003=0.
    kinds=np.array([2,3,4,0]);firsts=np.array([2,3,2,2]);seconds=np.array([2,2,2,2])
    for i in range(n):
        ts,ws,bs=known_sim._stream(seed+i,H,true_d,low,high,words,32)
        data[i,0]=run_bank(ts,ws,bs,True,pay,state,etime,pos,dirty,newtrace,False)
        data[i,1]=run_bank(ts,ws,bs,False,pay,state,etime,pos,dirty,newtrace,False)
        for k in range(4):
            r=known_sim._run(ts,ws,bs,kinds[k],firsts[k],seconds[k],ms,cap,3.,1,*oldargs,state,etime,pos,dirty,oldtrace,False)
            data[i,k+2,:7]=r[:7]
    return data

def known(dwell):
    return known_sim.pack(known_core.build_model(known_core.load_config(),dwell,cache=False))

def trace(bank,dwell,seed,learning=True):
    c=bank.cfg;w=c['memory']['words'];pay=payload(bank)
    ts,ws,bs=known_sim._stream(seed,c['horizon_seconds'],dwell,c['environment']['b_low'],c['environment']['b_high'],w,32)
    tr=np.empty((int(c['horizon_seconds']/min(c['periods_seconds']))+1,18))
    result=run_bank(ts,ws,bs,learning,pay,np.full(w,-1,np.int8),np.empty(w),np.empty(w,np.int32),np.empty(w,np.int32),tr,True)
    return result,tr[:int(result[-1])]
