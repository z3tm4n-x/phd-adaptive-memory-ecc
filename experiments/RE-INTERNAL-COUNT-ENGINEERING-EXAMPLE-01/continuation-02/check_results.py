"""Independent trial-level checker: no imports from analysis/engine/controller."""
from pathlib import Path
import json,math
from statistics import fmean,stdev
import numpy as np
from scipy.special import bdtr,bdtrc,stdtrit

ROOT=Path(__file__).resolve().parent
def cp_bisect(k,n,a):
    def solve(fn,target):
        lo=0.;hi=1.
        for _ in range(60):
            mid=(lo+hi)/2
            if fn(mid)<target:lo=mid
            else:hi=mid
        return (lo+hi)/2
    low=0. if k==0 else solve(lambda p:bdtrc(k-1,n,p),a/2)
    high=1. if k==n else solve(lambda p:bdtrc(k,n,p),1-a/2)
    return low,high

def main():
    cfg=json.loads((ROOT/'config.json').read_text());summary=json.loads((ROOT/'outputs/analysis.json').read_text())
    alpha=cfg['statistics']['family_alpha']/cfg['statistics']['family_size'];errors=[];checks=0
    def equal(a,b,label,tol=2e-9):
        nonlocal checks
        checks+=1
        if not math.isclose(a,b,rel_tol=tol,abs_tol=tol):errors.append([label,a,b])
    for case,group in summary['results'].items():
        z=np.load(ROOT/'outputs'/f'test_{case}.npz');r=z['rows'];n=len(r)
        equal(n,cfg['simulation']['validation_trials'],'N')
        assert len(set(z['event_sha256']))==n
        for j,row in enumerate(group['policies']):
            k=sum(int(v) for v in r[:,j,0]);equal(k,row['failures'],'failures')
            lo,hi=cp_bisect(k,n,alpha);equal(lo,row['family_low'],'CP low');equal(hi,row['family_high'],'CP high')
            alive=[i for i in range(n) if r[i,j,0]==0]
            equal(fmean(r[i,j,7] for i in alive),row['survivor_reservation_s'],'own survivor resource')
            equal(fmean(r[:,j,7]),row['stop_reservation_s'],'stop resource')
            # Every service read is a full 39-position word, not 4 byte accesses.
            assert np.all(r[:,j,4]>=r[:,j,2]*cfg['memory']['words'])
            assert np.all(r[:,j,6]<=r[:,j,7]+1e-7)
        for j,row in enumerate(group['pairs'],1):
            counts=[0,0,0,0];x=[];y=[]
            for i in range(n):
                p=int(r[i,0,0]);q=int(r[i,j,0]);counts[2*p+q]+=1
                if p==q==0:x.append(float(r[i,0,7]));y.append(float(r[i,j,7]))
            for field,value in zip(['both_survive','only_comparator_fails','only_proposed_fails','both_fail'],counts):equal(value,row[field],field)
            lower_plus,upper_plus=cp_bisect(counts[2],n,alpha/2)
            lower_minus,upper_minus=cp_bisect(counts[1],n,alpha/2)
            equal(lower_plus-upper_minus,row['risk_difference_low'],'paired CP low');equal(upper_plus-lower_minus,row['risk_difference_high'],'paired CP high')
            d=[p-q for p,q in zip(x,y)];mean=fmean(d);quant=float(stdtrit(len(d)-1,1-alpha/2));radius=quant*stdev(d)/math.sqrt(len(d))
            equal(mean-radius,row['reservation_difference_low'],'resource lower');equal(mean+radius,row['reservation_difference_high'],'resource upper')
            denominator=fmean(y);ratio=fmean(x)/denominator;influence=[-(p-ratio*q)/denominator for p,q in zip(x,y)]
            radius=quant*stdev(influence)/math.sqrt(len(x))
            equal(1-ratio-radius,row['G_low'],'G low');equal(1-ratio+radius,row['G_high'],'G high')
    # Analytic endpoints reject a zero-upper mutation on zero events.
    lo,hi=cp_bisect(0,20000,alpha);assert lo==0 and hi>0
    equal(hi,1-(alpha/2)**(1/20000),'zero event endpoint')
    result=dict(checks=checks,errors=errors,independent_path='binomial-tail bisection vs beta quantile; scalar statistics vs numpy paired reductions',shared_dependencies='published trial records and scipy special functions; not independent RNG/physical law',zero_upper_mutation_rejected=hi>0)
    (ROOT/'outputs/independent_statistics.json').write_text(json.dumps(result,indent=2)+'\n',newline='\n')
    print(json.dumps(result,indent=2));assert not errors

if __name__=='__main__':main()
