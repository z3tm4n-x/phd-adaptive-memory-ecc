"""Independent exact integer/fraction checks; no RTL or old timing helpers."""
from fractions import Fraction as F
import json
from pathlib import Path

def calculate():
    horizon=315576000
    fast_min=4*F(99999,100000) # ns
    # Arbitrary initial phase and total endpoint spread <=0.5 ns; two extra edges.
    max_edges=int((horizon*10**9+F(1,2))/fast_min)+2
    assert max_edges < 2**57 < 2**64-1
    # A smaller counter isn't repaired by simply assuming fewer ERRs.
    assert max_edges > 2**16-1
    return {'horizon_s':horizon,'fast_min_ns':str(fast_min),
      'max_edges_upper':max_edges,'minimal_bits_for_this_bound':max_edges.bit_length(),
      'implemented_bits':64,'saturation_unreachable_within_horizon':True,
      'assumptions':['qualified generation=0 at mission start, no runtime reset',
        'common xi>=0.99999 ns and endpoint spread<=0.5 ns',
        'at most one coalesced generation increment per fast edge'],
      'extra_unavailability_from_saturation_in_this_domain_s':0,
      'not_claimed':['unbounded mission duration','composed LOW pipeline equivalence',
        'availability of external input or hardware outside its contract'],
      'theory_input':'71fa4680d1e737bb1fb3b0cce31ee24cec410f4a',
      'application_envelope':{'joint_burst':1,'joint_rate_per_s':10000,
        'mean_read_per_s':1000,'mean_write_per_s':1000,
        'means_scope':'mission and quiet components expanded by 3 us'},
      'unconfirmed_ns':{'candidate_preparation_to_freeze':None,'joint_ERR_loss_to_rule_veto':None,
        'full_top_din':None,'full_top_dout':None},
      'component_deadlines_ns':{'R':str(92*F(100001,100000)+F(1,2)),
        'E':str(148*F(100001,100000)+F(1,2)),
        'read32':str(184*F(100001,100000)+1),
        'observed_write32':str(216*F(100001,100000)+1)}}

if __name__=='__main__':
    data=calculate()
    Path(__file__).with_name('contract.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))
