"""Rational composition at the T135-r4 cutpoints; no scientific recalculation.

The old calculator remains byte-identical. This file closes the previously
implicit eligibility edge and post-response four-phase recycling premise.
"""
import argparse,json,sys
from fractions import Fraction as F
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from integrated.bounds import calculate as inherited,encode,upper

THEORY='fa4b4c150e668422e36a6c7a0e30810b26604e7c'

def calculate():
    r=inherited()
    app=r['application']
    app['inbound_to_app_waiting_ns']=app.pop('inbound_ns')
    app['inbound_to_eligible_ns']=app['inbound_to_app_waiting_ns']+upper(4)
    assert app['inbound_to_eligible_ns']==F('177.001760')<320
    # From a destination consumption: ACK up (3 source sync + detect +
    # registered send drop), request down (3 destination sync + request +
    # acknowledge), ACK down (3 source sync + occupied clear).
    # These are DIGITAL progress premises of the same XPM contract as
    # prove_transport.py, not a bound on analog metastability duration.
    ack_slow_fast=upper(9*20+5*4)
    ack_fast_slow=upper(9*4+5*20)
    # Four-phase wrappers are also checked with a 320ns watchdog on both
    # 5:1 digital clock orientations. Leave a further conservative tail for
    # three synchronous FWFT queues (4 slow ticks each) and credit release.
    watchdog=upper(320)
    assert max(ack_slow_fast,ack_fast_slow)<watchdog
    recycle=watchdog+upper(3*4*20+20)
    tail=F(1000)
    assert recycle<tail
    next_arrival=F(100000)
    assert app['response_with_10pct_ns']+tail<next_arrival
    app['post_response_recycling']={
        'slow_to_fast_wrapper_ns':ack_slow_fast,
        'fast_to_slow_wrapper_ns':ack_fast_slow,
        'wrapper_watchdog_ns':watchdog,
        'three_FWFT_and_credit_composition_ns':recycle,
        'allocated_tail_ns':tail,
        'next_envelope_arrival_min_ns':next_arrival,
        'remaining_after_response_and_tail_ns':next_arrival-app['response_with_10pct_ns']-tail,
        'premise':'all earlier packets consumed; no next external arrival; initialized continuous clocks; FWFT contract',
        'not_inferred_from':'two credits alone'}
    r['unchanged_theory_inputs']['T135_r4']=THEORY
    r['status']='conditional all-history digital composition; physical phase proof separate'
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args()
    s=json.dumps(encode(calculate()),indent=2,ensure_ascii=False)+'\n'
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(s)
    print(s)
