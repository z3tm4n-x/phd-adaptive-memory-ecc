#!/usr/bin/env python3
from __future__ import annotations
import itertools, json, math
from decimal import Decimal, getcontext
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'outputs'
OUT.mkdir(exist_ok=True)

U_REG=Decimal('0.0003098119451681036')
L_REG=Decimal('5.90925197663239e-10')
EPS=Decimal('0.001')
H_S=24*3600

def require(x,msg):
    if not x:
        raise AssertionError(msg)

def exhaustive_d3_n38_exact3():
    n=38
    count=0
    for e in [None]+list(range(n)):
        E=set() if e is None else {e}
        for mark in itertools.combinations(range(n),3):
            count += 1
            require(len(E.symmetric_difference(mark))>1,
                    f'D3 counterexample: E={E}, mark={mark}')
    return count

def find_two_toggle_cancellation():
    # Smallest explicit SEC-safe cancellation witness.
    E={0}; mark={0,1}; post=E.symmetric_difference(mark)
    require(len(E)<=1 and len(mark)==2 and len(post)<=1,'fixture malformed')
    return {'pre_errors':sorted(E),'toggle_mark':sorted(mark),'post_errors':sorted(post),'post_weight':len(post)}

def arithmetic_checks():
    getcontext().prec=40
    delta=EPS-U_REG
    require(delta>0,'selected registered upper already exceeds epsilon')
    require(U_REG+delta==EPS,'coverage threshold identity')
    require(U_REG+Decimal('0.0007')>EPS,'upper direction wrong')
    # Conditional translations only under a Poisson no-event law.
    eps_f=float(EPS); delta_f=float(delta)
    lam_q3=-math.log1p(-eps_f)/H_S
    lam_cov=-math.log1p(-delta_f)/H_S
    return {
      'registered_data_only_lower':str(L_REG),
      'registered_data_only_upper':str(U_REG),
      'epsilon_analysis':str(EPS),
      'delta_cov_critical':str(delta),
      'poisson_translation_only':{
        'q3_exclusion_rate_per_s':lam_q3,
        'q3_exclusion_rate_per_day':lam_q3*86400,
        'coverage_certificate_rate_per_s':lam_cov,
        'coverage_certificate_rate_per_day':lam_cov*86400,
      }
    }

def main():
    count=exhaustive_d3_n38_exact3()
    two=find_two_toggle_cancellation()
    ar=arithmetic_checks()
    result={
      'passed':True,
      'checks':[
        'D3_exactly3_all_SEC_safe_states_n38',
        'two_toggle_cancellation_counterexample',
        'coverage_union_threshold_direction',
        'conditional_poisson_threshold_translation'
      ],
      'd3':{
        'codeword_cells':38,
        'correctable_t':1,
        'safe_pre_states':39,
        'atomic_mark_distinct_cells':3,
        'enumerated_cases':count,
        'counterexamples':0,
        'analytic_extension':'for |M|>=3 and |E|<=1, |E symmetric_difference M| >= |M|-|E| >= 2'
      },
      'two_toggle_cancellation':two,
      'slice':{
        'source':'RE-CY62167-ECC-RISK-BRIDGE-01/risk_curves.csv@69e92fe36b3b7933cebccbedd457cc0309dd4d1c',
        'timestamp':'2026-01-19T04:00:00+00:00',
        'window':'24h','shield_mm':10.0,'sigma_model':'main_loglog','direction':'central_mean','direct_scenario':'DREG','tau_s':1.0,
        **ar
      }
    }
    (OUT/'checks.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__': main()
