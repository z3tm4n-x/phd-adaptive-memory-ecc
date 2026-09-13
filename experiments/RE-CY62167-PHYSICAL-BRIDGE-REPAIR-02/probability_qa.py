#!/usr/bin/env python3
"""Deterministic arithmetic QA for the enlarged arrival-event bounds. No CY rates."""
from decimal import Decimal, getcontext
import json
from pathlib import Path
getcontext().prec=60

mu=Decimal('0.01')
p=Decimal(1)-(-mu).exp()
q_interval=Decimal(3)*p*p-Decimal(2)*p*p*p
p_distinct_two_intervals=Decimal(1)-(Decimal(1)-q_interval)**2
pair_upper=Decimal(3)*Decimal(2)*mu*mu
rmw_mu=Decimal('0.004')
rmw_distinct_arrival=Decimal(1)-(-rmw_mu).exp()
rmw_upper=rmw_mu
assert p_distinct_two_intervals <= pair_upper
assert rmw_distinct_arrival <= rmw_upper
# Periodic all-check window exposure over two 300-s constant-rate blocks.
phases=[Decimal(j+1)/Decimal(10) for j in range(8)]
D=Decimal('.07'); total=Decimal(0)
for phase in phases:
    for k in range(600):
        a=phase+Decimal(k); b=min(a+D,Decimal(600))
        total += max(Decimal(0), min(b,Decimal(300))-a)
        total += Decimal(2)*max(Decimal(0), b-max(a,Decimal(300)))
duty=Decimal(len(phases))*D*(Decimal(300)+Decimal(2)*Decimal(300))
assert total <= duty
out={
 "event_label":"distinct_arrival_event_probability",
 "synthetic_n_bits":3,
 "synthetic_mu_per_bit_per_interval":str(mu),
 "synthetic_intervals":2,
 "distinct_arrival_event_probability":str(p_distinct_two_intervals),
 "pair_union_upper":str(pair_upper),
 "rmw_distinct_arrival_probability":str(rmw_distinct_arrival),
 "rmw_union_upper":str(rmw_upper),
 "aligned_300s_all_check_exposure":str(total),
 "aligned_300s_duty_exposure":str(duty),
 "physical_input":None
}
out["physical_input"]="NO"
Path('outputs/probability_qa.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,indent=2,sort_keys=True))
