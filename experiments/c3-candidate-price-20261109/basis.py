"""One unchanged fixed competitor and the two pre-registered price thresholds."""
import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXP=HERE.parent
FIXED=EXP/'c1-common-geo-20261109'
SOURCE={
    'six.json':'b9caa156a1a0ca19ade679013c618b793b1e63fe910b6f79aa26004d41da6b65',
    'coverage.json':'ed7efbba7bbb92b6c34b9440eaaeb7742b44578fa22e77dd069f21cdd71d2d72'}


def verified(name):
    data=(FIXED/name).read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(data).hexdigest()!=SOURCE[name]:raise ValueError('Changed fixed input '+name)
    return json.loads(data)


def basis():
    previous=verified('six.json');coverage=verified('coverage.json')
    selected=next(r for r in previous['rows'] if r['W']==65536 and F(r['epsilon'])==F(1,1000))
    candidate=selected['candidate'];assert candidate['k']==4
    W=selected['W'];T=F(previous['T']);D=F(previous['D']);eps=F(selected['epsilon'])
    low=F(selected['necessary']['bus_lower_s']);upper=F(candidate['price']['bus']['upper_s'])
    assert 0<low<=upper and F(candidate['risk']['total'])<=eps
    b=F(coverage['b_s_inv']);B=F(coverage['B_s_inv']);g=F(previous['growth_s_inv2']);a=(B-b)/2
    duration=a/g;exc=a*duration/2;mu=F(W*39,D)*(300*b+exc)
    assert duration<300 and exc<F(previous['F']) and a<F('28.855')
    return {'T_s':T,'W':W,'D':D,'epsilon':eps,'q_fixed_upper':candidate['risk']['total'],
            'b':b,'B':B,'g':g,'F':F(previous['F']),'J_cap':F('28.855'),
            'fixed_class_lower_s':low,'fixed_candidate_upper_s':upper,
            'fixed_class_lower_percent':100*low/T,'fixed_candidate_upper_percent':100*upper/T,
            'sufficient_half_s':low/2,'sufficient_half_percent':50*low/T,
            'exclusion_half_s':upper/2,'exclusion_half_percent':50*upper/T,
            'maximum_word_visits':F(selected['necessary']['maximum_reads_upper']),
            'common_app_upper_s':F(candidate['price']['bus']['app_s']['upper']),
            'common_init_upper_s':F(candidate['price']['bus']['init_upper_s']),
            'peak':selected['peak'],'management_guaranteed_progress_ns':F(selected['management_progress_ns']),
            'late_ramp_300s':{'duration_s':duration,'excess_exposure':exc,'mu_full_bank_singleton':mu,
                'prob_no_parent':math.exp(-float(mu))},
            'fixed_provenance':'c0176b4837b5310378fb4218f2d549aeb4c991e9','source_sha256_LF':SOURCE}


def write_json(name,data,check):
    value=json.dumps(data,default=str,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    path=HERE/name
    if check:
        if path.read_text(encoding='utf-8')!=value:raise ValueError('Mismatch: '+name)
    else:path.write_text(value,encoding='utf-8',newline='\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    data=basis();write_json('basis.json',data,args.check)
    print('Half-price endpoints in bus seconds:',float(data['sufficient_half_s']),float(data['exclusion_half_s']))
