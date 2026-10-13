"""Early timing ledger: requirements != established processor bounds.

No timing constant is inferred from QEMU or native wall time. The raw FIFO
counterexample is a necessary throughput argument for ONE declared transport.
"""
import json
from fractions import Fraction as F
from pathlib import Path
HERE=Path(__file__).resolve().parent

def raw_tail_lower(events=2000,source_spacing_ns=20,record_bits=130,width=32,period_ns=20):
    # Source events at i*20 ns, starting with loss rising, alternating.
    # Optimistic packed beats across record boundaries; no address/CPU/CDC.
    # Allow the first completed data beat at time 0 (more optimistic still).
    beats=(events*record_bits+width-1)//width
    final_beat=F(beats-1)*period_ns
    last_source=F(events-1)*source_spacing_ns
    return max(F(0),final_beat-last_source)

def calculate():
    hi=F('1.00001')
    U=lambda t:F(t)*hi+F('.5')
    # SAME downstream candidate/frame mechanism only. A new bridge must
    # establish these interfaces, not merely inherit the old STA report.
    suffix=U(36)+U(3*1568-320)+U(8)
    external_loss_prefix=U(4*20)
    history_available=F(10000)-suffix-external_loss_prefix
    old_history=F('531869457677237/102498975000')
    tail=raw_tail_lower()
    record_beats=(130+31)//32
    record_tail=F((2000*record_beats-1)*20)-(2000-1)*20
    ledger=[
      {'stage':'external stable loss -> loss_slow','ns_upper':str(external_loss_prefix),'status':'conditional reused component; source stability required'},
      {'stage':'history staging/FIFO/PS request/CPU state update/publication','ns_upper':None,'status':'UNKNOWN; combined allocation below, not old 5189 ns'},
      {'stage':'candidate/beacon/freeze suffix incl local loss veto','ns_upper':str(suffix),'status':'conditional on unchanged downstream lease and flight'},
      {'stage':'ARM load/store/OCM/cache/arbitration','ns_upper':None,'status':'UNKNOWN; instruction count is not cycles'},
      {'stage':'PS AXI read/write and barriers -> PL shadow commit','ns_upper':None,'status':'UNKNOWN; no finite bound inferred from AXI protocol'},
      {'stage':'polling/interrupt interference','ns_upper':None,'status':'candidate dedicated-core assumptions not yet platform configured'}]
    return {'status':'early checkpoint, NOT full ARM timing acceptance',
      'reaction_limit_ns':10000,'candidate_limit_ns':1000,'ledger':ledger,
      'available_for_history_CPU_PSPL_ns':str(history_available),
      'old_RTL_history_ns':str(old_history),
      'old_residual_ns':str(history_available-old_history),
      'raw_32bit_50MHz':{'source_events':2000,'source_period_ns':20,
        'source_duration_ns':39980,'rises':1000,'ordinary_recoveries':1000,'no_ERR_needed':True,
        'quota_check':'1000 ordinary recoveries <=1000; 1000 rises <=1001; 2000 transitions <=2002',
        'bits_per_event':130,'packed_total_beats':(2000*130+31)//32,
        'packed_tail_lower_ns':str(tail),'padded_record_beats':record_beats,
        'padded_tail_lower_ns':str(record_tail),
        'excludes':['CPU time','read address/response overhead','CDC','candidate publication'],
        'result':'cannot meet 10 us on this permitted history; not impossibility of ARM or compressed transport'},
      'application':{'unchanged_boundary_requirements_ns':[320,320,100],
         'response_limit_ns':3000,'bus_any_1ms_limit':'0.8',
         'new_AXI_master_included':False,
         'price_claim':False,'mean_traffic':'joint >=100 us; mean read/write <=1000/s each'},
      'CPU_wcet_ns':None,'CPU_load_percent':None,'PSPL_upper_ns':None,
      'modified_top_LUT_FF_BRAM':None,'modified_top_STA':None}

def main():
    r=calculate();p=HERE/'outputs/budget.json';p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
if __name__=='__main__':main()
