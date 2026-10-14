"""Test-side collection; independent oracle expands EVERY original event.

This collector does not calculate policy timers or ERR association. It is a
convenient input generator; the actual RTL collector is checked separately.
"""
from dataclasses import dataclass
from oracle import Oracle

B_STARTED=1; B_HEALTHY=2; B_RECOVERY=4; B_EVENT_AT_END=8; B_FAULT=16
NAMES=("sequence base_generation end_generation end_tick start_tick "
       "first_err_source last_err_source first_err_tick last_err_tick "
       "last_recovery_tick event_count err_count flags reserved").split()

@dataclass
class Trace:
    start: int
    batches: list

def collect(start, groups, **oracle_parameters):
    healthy=True; gen=0; seq=0
    oracle=Oracle(**oracle_parameters); oracle.apply((start,0,0,1,0))
    result=[]
    for end,events in groups:
        seq+=1; first_gen=gen; errors=[]; recoveries=[]
        for tick,src,err,loss in events:
            gen+=1
            if healthy is False and not loss: recoveries.append(tick)
            healthy=not loss
            if err: errors.append((tick,src))
            oracle.apply((tick,gen,src,2|4*err|8*loss,0))
        at_end=bool(events and events[-1][0]==end)
        if end>oracle.now: oracle.apply((end,0,0,0,0))
        flags=B_STARTED | (B_HEALTHY if healthy else 0)
        if recoveries: flags|=B_RECOVERY
        if at_end: flags|=B_EVENT_AT_END
        values=(seq,first_gen,gen,end,start,
                errors[0][1] if errors else 0,errors[-1][1] if errors else 0,
                errors[0][0] if errors else 0,errors[-1][0] if errors else 0,
                recoveries[-1] if recoveries else 0,len(events),len(errors),flags,0)
        result.append((values,oracle.snapshot()))
    return result
