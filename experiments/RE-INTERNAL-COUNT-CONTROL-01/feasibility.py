"""Deterministic whole-horizon brackets, not adaptive impossibility claims.

All decimal inputs are read as declared decimal quantities. 80-digit arithmetic
avoids cancellation in small-exposure Markov-modulated second moments.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
import mpmath as mp

ROOT = Path(__file__).resolve().parent

def brackets(cfg: dict, dwell: float, first: float, second: float | None = None):
    mp.mp.dps = 80
    M = lambda x: mp.mpf(str(x))
    w, n = cfg['memory']['words'], cfg['memory']['bits_per_word']
    p, h = M(cfg['memory']['pass_seconds']), M(cfg['horizon_seconds'])
    a = M(first); b = a if second is None else M(second)
    low, high = M(cfg['environment']['b_low']), M(cfg['environment']['b_high'])
    mean, var, k = (low+high)/2, (high-low)**2/4, 2/M(dwell)
    coefficient = M(n-1)/(2*n*w)
    def moment(t):
        return mean**2*t*t + 2*var*(t/k + mp.expm1(-k*t)/(k*k))
    mx = p*(w+1)/(2*w)
    mx2 = p*p*(w+1)*(2*w+1)/(6*w*w)
    boundary_t = a
    boundary_t2 = (a-p)**2 + 2*(a-p)*mx + mx2 + p*p - 2*p*mx + mx2
    step = k*p/w
    geom = mp.expm1(-k*p)/mp.expm1(-step)/w
    boundary_exp = mp.exp(-k*(a-p)-step)*geom + geom
    boundary_m2 = mean**2*boundary_t2 + 2*var*(boundary_t/k-(2-boundary_exp)/(k*k))
    if second is None:
        n1, n2 = h/a, M(0)
    else:
        n1, n2 = (h/2)/a, (h/2)/b
    assert n1 == int(n1) and n2 == int(n2)
    expected_q = coefficient*((n1-1)*moment(a)+n2*moment(b)+boundary_m2)
    q_max = coefficient*high**2*((n1-1)*a*a+n2*b*b+boundary_t2)
    max_word_dose = high*max(a,b)/w
    # Exactly two arrivals of distinct bit labels imply first passage. Products
    # are conditional on the environment path AND an exogenous schedule only.
    lower = -mp.expm1(-mp.exp(-max_word_dose)*q_max)*expected_q/q_max
    return float(lower), float(min(M(1), expected_q)), int(n1+n2), float(q_max)


def run(cfg: dict | None = None):
    cfg = cfg or json.loads((ROOT/'config.json').read_text())
    out = ROOT/'outputs'; out.mkdir(exist_ok=True)
    all_rows, audit, best = [], [], []
    for dwell in cfg['environment']['mean_dwell_seconds']:
        rows=[]
        for kind in ['Fixed','Precomputed']:
            for first in cfg['periods_seconds']:
                seconds = [None] if kind=='Fixed' else cfg['periods_seconds']
                for second in seconds:
                    lo, hi, passes, maxq = brackets(cfg,dwell,first,second)
                    row=dict(dwell=dwell,policy=kind,first=first,second=first if second is None else second,
                             first_passage_lower=lo,first_passage_upper=hi,passes=passes,all_high_Q=maxq)
                    rows.append(row); all_rows.append(row)
        for eps in cfg['epsilon']:
            feasible=[r for r in rows if r['first_passage_upper']<=eps]
            audit.append(dict(dwell=dwell,epsilon=eps,
                adaptive_feasibility='CONFIRMED_BY_FIXED' if feasible else 'UNRESOLVED_NOT_INFEASIBILITY',
                minimum_period_lower=rows[0]['first_passage_lower'],
                minimum_period_upper=rows[0]['first_passage_upper'],
                reason='nonempty sufficient set' if feasible else ('all Fixed fail lower bound; general adaptive class not ruled out' if all(r['first_passage_lower']>eps for r in rows if r['policy']=='Fixed') else 'sufficient certificate failed; feasibility unresolved')))
            for kind in ['Fixed','Precomputed']:
                fr=[r for r in feasible if r['policy']==kind]
                if not fr: continue
                chosen=min(fr,key=lambda r:(r['passes'],-r['first'],-r['second']))
                challengers=[r for r in rows if r['policy']==kind and r['passes']<chosen['passes']]
                optimal=all(r['first_passage_lower']>eps for r in challengers)
                best.append(dict(dwell=dwell,epsilon=eps,**{k:v for k,v in chosen.items() if k!='dwell'},
                                 optimal_in_declared_class=optimal,
                                 rejected_cheaper=len(challengers),
                                 cheapest_challenger_lower=min([r['first_passage_lower'] for r in challengers],default=1)))
    for filename, data in [('open_loop_brackets.csv',all_rows),('feasibility.csv',audit),('open_loop_optima.csv',best)]:
        with (out/filename).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    print(json.dumps({'audit':audit,'optima':best},indent=2))
    return audit,best

if __name__=='__main__': run()
