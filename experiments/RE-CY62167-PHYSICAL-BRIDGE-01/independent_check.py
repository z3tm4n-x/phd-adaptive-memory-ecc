#!/usr/bin/env python3
from __future__ import annotations
import json
from decimal import Decimal, getcontext
from pathlib import Path

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'outputs'

def pop(x): return x.bit_count()
def require(x,msg):
    if not x: raise AssertionError(msg)

def bitmask_d3(n=6):
    safe=[0]+[1<<i for i in range(n)]
    tested=0
    for e in safe:
        for m in range(1<<n):
            if pop(m)>=3:
                tested+=1
                require(pop(e^m)>1, f'counterexample {e=} {m=}')
    return tested

def observation_projection(parent_marks, data_mask):
    # Bounded witness: current controlled interface observes data-cell toggles only.
    return [mark & data_mask for mark in parent_marks if (mark & data_mask)!=0]

def nonidentifiability_fixture():
    # 6 data + 3 parity toy codeword. Registered data projection is identical,
    # but m1 contains an atomic hidden triple-parity event.
    data_mask=(1<<6)-1
    parity_triplet=(1<<6)|(1<<7)|(1<<8)
    visible=[1<<0, 1<<2]
    m0=list(visible)
    m1=list(visible)+[parity_triplet]
    o0=observation_projection(m0,data_mask)
    o1=observation_projection(m1,data_mask)
    require(o0==o1,'hidden parity process changed registered data projection')
    require(pop(parity_triplet)==3,'hidden event is not D3')
    return {'same_registered_data_projection':True,'hidden_D3_in_m1':True,'visible_projection':[hex(x) for x in o0]}

def threshold_check():
    getcontext().prec=40
    eps=Decimal('0.001'); u=Decimal('0.0003098119451681036')
    d=eps-u
    require(d==Decimal('0.0006901880548318964'),'threshold mismatch')
    require(u+d==eps,'union threshold direction')
    return {'u_reg':str(u),'epsilon':str(eps),'delta_crit':str(d)}

def main():
    result={'passed':True,'bitmask_d3_cases':bitmask_d3(),'nonidentifiability_fixture':nonidentifiability_fixture(),'threshold':threshold_check()}
    (OUT/'independent_check.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
