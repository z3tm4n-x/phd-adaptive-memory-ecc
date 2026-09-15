#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json
from decimal import Decimal,localcontext
from math import comb
from pathlib import Path

def D(x): return Decimal(str(x))
def main():
    raise SystemExit('DISABLED_UNQUALIFIED_DREG: see PREEXECUTION_AMENDMENT.md; no numerical certificate released')
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--rate',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text()); prec=cfg['arithmetic_precision_decimal_digits']
    with localcontext() as c:
        c.prec=prec
        rows=list(csv.DictReader(Path(a.rate).open(newline='',encoding='utf-8')))
        expected=cfg['slice']['horizon_s']//cfg['slice']['bin_s']
        if len(rows)!=expected: raise SystemExit('incomplete selected input')
        I1=Decimal(0); I2=Decimal(0)
        for q in rows:
            rr=Decimal(q['r_per_bit_s-1']); dur=Decimal(q['duration_s'])
            if not rr.is_finite() or rr<0 or dur<=0: raise SystemExit('invalid selected input')
            I1 += rr*dur; I2 += rr*rr*dur
        W=Decimal(cfg['slice']['words']); n=cfg['slice']['data_bits_per_word']; tau=D(cfg['slice']['tau_s']); eps=Decimal(cfg['slice']['epsilon_analysis'])
        a0=W*Decimal(comb(n,2))*tau*I2; b0=Decimal(31)*W*I1/tau
        aa=c.next_plus(a0); bb=c.next_plus(b0)
        delta_crit=None
        if bb>0 and aa<=eps:
            dc=(eps-aa)/bb
            if dc>=0: delta_crit=min(dc,tau)
        reporting=[]
        for sd in cfg['reporting_delta_s']:
            de=Decimal(sd); raw=aa+bb*de; u=min(Decimal(1),c.next_plus(raw)); slack=eps-u
            reporting.append({'delta_s':sd,'u_model_upper':str(u),'signed_slack':str(slack),'delta_cov_upper_required_max':str(slack) if slack>=0 else None,'model_certificate_status':'SUFFICIENT' if slack>=0 and de<tau else 'INSUFFICIENT'})
        hist=Decimal(cfg['historical_ideal_union_upper_qa'])
        result={'I1':str(I1),'I2_s-1':str(I2),'a_upper':str(aa),'b_upper_s-1':str(bb),'epsilon_analysis':str(eps),'delta_crit_zero_coverage_s':str(delta_crit) if delta_crit is not None else None,'delta_executor_domain':'0 <= Delta < 1 s','reporting':reporting,'historical_ideal_union_upper_qa':str(hist),'pair_upper_ge_historical_ideal_union':bool(aa>=hist),'historical_difference':str(aa-hist),'physical_coverage_status':'NOT_ESTABLISHED','device_policy_status':'NOT_ESTABLISHED'}
        Path(a.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
