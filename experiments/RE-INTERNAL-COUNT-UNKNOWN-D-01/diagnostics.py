"""Own-history traces, controller timings and independent small-model checks."""
from __future__ import annotations
import csv,json,time
import numpy as np
from numba import njit
import model,engine,verification
from upstream import known_sim

@njit(cache=True)
def toy_batch(n,seed,pay):
    data=np.empty((n,2));W=pay[13];state=np.full(W,-1,np.int8);et=np.empty(W);pos=np.empty(W,np.int32);dirty=np.empty(W,np.int32);trace=np.empty((0,18))
    for i in range(n):
        t,w,b=known_sim._stream(seed+i,pay[15],10.,pay[11],pay[12],W,32)
        for k in range(2):data[i,k]=engine.run_bank(t,w,b,k==0,pay,state,et,pos,dirty,trace,False)[0]
    return data

@njit(cache=True)
def replay(trace,pay,learning,repetitions):
    K,T,J,f,z,V,s0,rates,periods,ticks,tick,lo,hi,W,P,H,threshold,backup=pay
    checksum=0.
    for _ in range(repetitions):
        q=np.zeros((len(rates),6));q[:,:2]=.5;s=s0.copy();scores=np.zeros(len(rates));rej=np.zeros(len(rates),np.bool_);active=np.ones(len(rates),np.bool_)
        for row in trace:
            rem=int(round((H-row[0])/tick))
            a=model.choose(rem,q,s,active,T,J,f,z,V,ticks,tick,rates,lo,hi,W,backup)
            if abs(periods[a]-row[1])>1e-10:raise AssertionError('controller replay changed action')
            model.spend(a,rem,q,s,active,T,J,f,z,V,ticks,tick,rates,lo,hi,W,backup)
            if row[2]<H-1e-10:model.observe(a,int(row[3]),q,scores,rej,active,K,learning,threshold)
            checksum+=periods[a]
    return checksum

def write(path,columns,rows):
    with path.open('w',newline='') as file:
        writer=csv.writer(file);writer.writerow(columns);writer.writerows(rows)

def run():
    cfg=model.config();out=model.ROOT/'outputs';out.mkdir(exist_ok=True);b=model.build();summaries=[];excerpts=[];timings=[]
    for D in cfg['simulation']['dwell_seconds']:
        for enabled in (True,False):
            outcome,trace=engine.trace(b,D,cfg['simulation']['trace_seed'],enabled);name='learning' if enabled else 'frozen'
            write(out/f'trace_{D}_{name}.csv',engine.TRACE_COLUMNS,trace)
            changed=np.flatnonzero(trace[:,4]!=trace[:,5]);different=np.flatnonzero((trace[:,9]>=0)&(trace[:,8]!=trace[:,9]))
            action_changes=np.flatnonzero(trace[:,8]!=trace[:,1]);indexes=sorted(set([0,len(trace)-1]+changed[:15].tolist()+different[:20].tolist()+action_changes[:15].tolist()))
            for ix in indexes:excerpts.append([D,name,int(ix)]+trace[ix].tolist())
            summaries.append(dict(dwell=D,policy=name,failure=bool(outcome[0]),passes=int(outcome[1]),first_shrink_time=float(outcome[8]),final_cell_mask=int(outcome[7]),
                                  set_changes=len(changed),immediate_action_changes_due_to_contraction=len(different)))
            replay(trace,engine.payload(b),enabled,1);samples=[]
            for _ in range(5):
                start=time.perf_counter_ns();replay(trace,engine.payload(b),enabled,10)
                samples.append((time.perf_counter_ns()-start)/(10*len(trace)))
            timings.append(dict(dwell=D,policy=name,controller_decisions_in_trace=len(trace),ns_per_update_and_choice_median=float(np.median(samples)),
                                ns_per_update_and_choice_min=float(min(samples)),ns_per_update_and_choice_max=float(max(samples)),
                                note='warm compiled CPU replay of its own physical trace; not hardware WCET'))
    write(out/'trace_excerpt.csv',['dwell','policy','source_row']+engine.TRACE_COLUMNS,excerpts)
    write(out/'controller_cost.csv',list(timings[0]),[list(x.values()) for x in timings])
    toy=verification.toy_bank();actual=toy_batch(100000,cfg['simulation']['small_oracle_seed'],engine.payload(toy));checks=[]
    oracle=verification.PhysicalOracle(toy,10).run(True)['F']
    for k in range(2):
        estimate=float(actual[:,k].mean());se=(oracle*(1-oracle)/len(actual))**.5
        if abs(estimate-oracle)>5*se:raise AssertionError('small independent event/oracle discrepancy')
        checks.append(dict(policy='learning' if k==0 else 'frozen',trials=len(actual),estimate=estimate,oracle=oracle,standard_error=se))
    # Deterministic physical sentinels exercise features random rare events can miss.
    pay=engine.payload(toy);state=lambda: (np.full(2,-1,np.int8),np.empty(2),np.empty(2,np.int32),np.empty(2,np.int32))
    q,s,_,_,ac=toy.initial();a=model.choose(60,q,s,ac,*model.controller_args(toy));first_end=toy.periods[a]
    t=np.array([.1,.2]);w=np.array([0,0],np.int32);bits=np.array([1,1],np.int8);tr=np.empty((7,18))
    same=engine.run_bank(t,w,bits,True,pay,*state(),tr,True)
    assert same[0]==0 and tr[0,3]==0
    bits=np.array([1,2,1],np.int8);different=engine.run_bank(np.array([.1,.2,.3]),np.array([0,0,0],np.int32),bits,True,pay,*state(),tr,True)
    assert different[0]==1 and abs(different[5]-.2)<1e-12
    late=first_end-toy.cfg['memory']['pass_seconds']*.25
    pending=engine.run_bank(np.array([late]),np.array([0],np.int32),np.array([1],np.int8),True,pay,*state(),tr,True)
    assert tr[0,3]==0 and tr[0,17]==1 and tr[1,3]==1
    M=len(b.rates);qbytes=M*6*8;scalar_vectors=M*2*8;flags=M*2
    table_bytes=sum(x.nbytes for x in [b.kernels,b.transition,b.pending,b.first,b.second,b.value,b.rates,b.periods,b.ticks,b.slack0,b.errors])
    data=dict(traces=summaries,small_MC=checks,sentinels=['same_bit_cancellation_is_not_a_correction','first_passage_is_irreversible','post_scan_pending_is_carried'],
              node_count=M,filter_probability_and_moment_bytes=qbytes,slack_and_logscore_bytes=scalar_vectors,flag_bytes=flags,
              total_persistent_controller_array_bytes=qbytes+scalar_vectors+flags,temporary_six_vector_bytes=48,
              immutable_table_bytes=table_bytes,value_table_bytes=b.value.nbytes,warm_build_seconds=b.build_seconds,
              execution_window_seconds=min(cfg['periods_seconds'])-cfg['memory']['pass_seconds'],
              memory_scope='raw numeric arrays; Python/interpreter/compiler/array-header memory is additional; tables are not included in the 6M filter coordinates')
    (out/'diagnostic_summary.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2));return data
if __name__=='__main__':run()
