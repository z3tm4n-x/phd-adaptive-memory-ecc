"""Resource dimensions; measured host speed is not embedded WCET."""
import json,time
import numpy as np
from reference import ROOT,packed,accepted,config

def main():
    p=packed();c=config();tables={name:int(getattr(p,name).nbytes) for name in p.__dataclass_fields__ if isinstance(getattr(p,name),np.ndarray)}
    for _ in range(5):accepted._choose(p.initial,p.slack,1000,p.H,p.J,p.constant,p.coefficient,p.first,p.second,p.ticks,p.tick,p.words,p.dwell,p.low,p.high)
    n=10000;start=time.perf_counter()
    for _ in range(n):
        q,lik=accepted._observe(p.initial,1,4,True,p.kernels,p.transition)
        accepted._choose(q,p.slack,1000,p.H,p.J,p.constant,p.coefficient,p.first,p.second,p.ticks,p.tick,p.words,p.dwell,p.low,p.high)
    seconds=time.perf_counter()-start
    result=dict(packed_table_bytes=tables,total_packed_array_bytes=sum(tables.values()),belief_bytes=26*8,scalar_state_note='slack, elapsed ticks, previous count/action and resource counters additional; implementation/runtime overhead not included',observation_coefficients_per_update=26**2,observation_table_read_bytes_per_update=26**2*8,observation_multiply_add_pairs_per_update=26**2,max_action_candidates=12,placement='separate protected control storage/cache, assumed correct; no shared buffer-bus traffic included',simple_policy_state='Fixed one period; Precomputed two periods + time comparison; PA-DOM scalar previous count/period and parameters; no belief tables',host_microbenchmark_repetitions=n,host_observe_choose_seconds=seconds,host_seconds_per_update=seconds/n,host_note='descriptive Python-to-Numba calls on current Windows host under concurrent tuning load; NOT WCET, embedded timing or whole controller cost',service_reservation_per_full_pass_s=p.pass_seconds/2,service_actual_read_bus_per_full_pass_s=p.words*2e-8,service_write_bus_per_ack_s=2e-8,peak_service_slot_fraction=.5,maximum_single_service_block_s=1e-7,application_workload='backlogged best-effort reads; release all unreserved slots; full-system queueing and application writes not modeled')
    (ROOT/'outputs/resource_accounting.json').write_text(json.dumps(result,indent=2)+'\n',newline='\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
