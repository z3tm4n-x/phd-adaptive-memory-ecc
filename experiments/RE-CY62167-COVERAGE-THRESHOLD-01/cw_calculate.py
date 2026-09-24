"""Exact rational integrals for the declared finite CSV rate representation."""
import argparse, csv, hashlib, json
from datetime import datetime,timedelta,timezone
from fractions import Fraction as F
from pathlib import Path

HERE=Path(__file__).resolve().parent
Q=10**40

def dec(k):
    sign='-' if k<0 else '';k=abs(k)
    return f'{sign}{k//Q}.{k%Q:040d}'

def enc(x):
    x=F(x);k=x.numerator*Q//x.denominator
    return {'exact':str(x),'lower':dec(k),'upper':dec(k if F(k,Q)==x else k+1)}

def query(a,b,delta,coverage=F(0)):
    if a<0 or b<0 or coverage<0:raise ValueError('negative bound coefficient/coverage')
    if not 0<=delta<1:raise ValueError('Delta must satisfy 0 <= Delta < tau=1')
    u=min(F(1),a+b*delta);s=F(1,1000)-u
    return {'delta_s':str(delta),'U_upper':enc(u),'signed_slack':enc(s),'coverage_upper':str(coverage),'sufficient':u+coverage<=F(1,1000)}

def load(path):
    rows=list(csv.DictReader(Path(path).open(newline='')))
    if len(rows)!=288:raise ValueError('expected 288 complete rows; stub/incomplete input rejected')
    start=datetime(2026,1,19,4,tzinfo=timezone.utc);rates=[]
    for i,row in enumerate(rows):
        if datetime.fromisoformat(row['timestamp_utc'])!=start+timedelta(seconds=300*i):raise ValueError('timestamp gap/duplicate/order/window')
        for k,v in [('duration_s','300'),('shield_mm','10'),('sigma_model','main_loglog'),('direction_scenario','central_mean'),('scenario','DREG'),('mapping','W32_seq')]:
            if row[k]!=v:raise ValueError('fixed contract '+k)
        nu=F(row['nu_C_bit_DREG_s_1']);r=F(row['r_bit_s_1'])
        if nu<0 or r<0 or F(row['r_D_DREG_s_1'])!=0:raise ValueError('negative rate or direct hazard misused')
        if r*16777216!=nu:raise ValueError('normalization: sum data-bit stream / 2^24 exactly once')
        rates.append(r)
    return rates

def calculate(path):
    r=load(path);I1=sum((300*x for x in r),F(0));I2=sum((300*x*x for x in r),F(0))
    a=524288*496*I2;b=31*524288*I1
    au=F(enc(a)['upper']);bu=F(enc(b)['upper']);eps=F(1,1000)
    domain={'delta_domain':'0 <= Delta < 1 s','coverage_domain':'0 <= delta_cov_upper <= 0.001-min(1,a_upper+b_upper*Delta), only if signed_slack >= 0','equality_allowed':True,'nonempty':au<=eps}
    if au>eps:domain.update(zero_coverage='EMPTY',delta_limit_s=None)
    elif bu==0:domain.update(zero_coverage='ALL_DELTA_IN_STRICT_DOMAIN',delta_limit_s=None,delta_supremum_s='1',supremum_attained=False)
    else:
        t=(eps-au)/bu;domain.update(zero_coverage='Delta <= exact_threshold AND Delta < 1',delta_limit_s=enc(t),delta_supremum_s=str(min(F(1),t)),supremum_attained=t<1)
    config=json.loads((HERE/'calculation_config.json').read_text())
    return {'selected_rate_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'N_w':524288,'bits_per_word':32,'N_data_bits':16777216,'tau_s':'1','H_s':86400,'I1':enc(I1),'I2_s_1':enc(I2),'a':enc(a),'b_s_1':enc(b),'a_upper':str(au),'b_upper_s_1':str(bu),'coefficient_quantum':'1e-40','arithmetic_scope':'exact declared decimal rate; no certified error of unavailable historical matrix or ideal real-valued transport','domain':domain,'probes':[query(au,bu,F(d)) for d in config['delta_probes_s']],'registered_model_status':'SUFFICIENT_ON_REPORTED_DOMAIN' if au<=eps else 'SUFFICIENT_BOUND_NOT_PASSED','physical_coverage_upper':None,'device_policy_status':'NOT_ESTABLISHED'}

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='op',required=True)
    c=sub.add_parser('calculate');c.add_argument('--input',type=Path,required=True);c.add_argument('--output',type=Path,required=True)
    q=sub.add_parser('query');q.add_argument('--a',required=True);q.add_argument('--b',required=True);q.add_argument('--delta',required=True);q.add_argument('--coverage',default='0')
    args=ap.parse_args()
    if args.op=='query':print(json.dumps(query(F(args.a),F(args.b),F(args.delta),F(args.coverage))));return
    result=calculate(args.input);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['I1','I2_s_1','a','b_s_1','domain','registered_model_status']},indent=2))

if __name__=='__main__':main()
