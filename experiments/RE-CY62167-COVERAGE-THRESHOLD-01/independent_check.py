#!/usr/bin/env python3
"""Independent exact-rational integration/check. Does not import primary extractor/calculator."""
from __future__ import annotations
import argparse,csv,json
from decimal import Decimal,getcontext
from fractions import Fraction
from math import comb
from pathlib import Path

def F(s): return Fraction(Decimal(s))
def dec(q,prec=70):
    getcontext().prec=prec; return Decimal(q.numerator)/Decimal(q.denominator)
def main():
    raise SystemExit('DISABLED_UNQUALIFIED_DREG: see PREEXECUTION_AMENDMENT.md; independent integrals NOT_RUN')
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--rate',required=True);ap.add_argument('--primary',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text()); rows=list(csv.DictReader(Path(a.rate).open(newline='',encoding='utf-8'))); p=json.loads(Path(a.primary).read_text())
    if len(rows)!=288: raise SystemExit('expected 288 bins')
    I1=Fraction(0);I2=Fraction(0); total=0
    from datetime import datetime,timedelta
    t0=datetime.fromisoformat(cfg['slice']['start_utc'])
    for i,r in enumerate(rows):
        t=datetime.fromisoformat(r['timestamp_utc']); expected=t0+timedelta(seconds=300*i)
        if t!=expected: raise SystemExit('timestamp mismatch')
        rr=F(r['r_per_bit_s-1']); d=F(r['duration_s'])
        if rr<0 or d!=300: raise SystemExit('rate/duration contract failure')
        I1+=rr*d; I2+=rr*rr*d; total+=int(r['duration_s'])
    if total!=86400: raise SystemExit('horizon duration mismatch')
    W=cfg['slice']['words']; n=cfg['slice']['data_bits_per_word']; tau=Fraction(1)
    ae=Fraction(W*comb(n,2))*tau*I2; be=Fraction(31*W)*I1/tau
    apv=Decimal(p['a_upper']); bpv=Decimal(p['b_upper_s-1']); aed=dec(ae); bed=dec(be)
    if apv<aed or bpv<bed: raise SystemExit('primary outward bound is below exact rational result')
    eps=Decimal(cfg['slice']['epsilon_analysis'])
    checks={'rows_288':len(rows)==288,'duration_86400':total==86400,'primary_a_outward':apv>=aed,'primary_b_outward':bpv>=bed,'delta_zero_logic':(eps-apv>=0)==(p['reporting'][0]['model_certificate_status']=='SUFFICIENT'),'negative_slack_preserved':all((Decimal(x['signed_slack'])<0)==(x['delta_cov_upper_required_max'] is None) for x in p['reporting']),'wrong_normalization_detectable':True}
    wrong=I1/F(str(cfg['slice']['data_bits_total']))
    checks['wrong_normalization_detectable']=wrong!=I1
    if not all(checks.values()): raise SystemExit(checks)
    out={'checks':checks,'I1_exact_decimal':str(dec(I1)),'I2_exact_decimal_s-1':str(dec(I2)),'a_exact_decimal':str(aed),'b_exact_decimal_s-1':str(bed),'primary_a_minus_exact':str(apv-aed),'primary_b_minus_exact':str(bpv-bed),'status':'PASS'}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
