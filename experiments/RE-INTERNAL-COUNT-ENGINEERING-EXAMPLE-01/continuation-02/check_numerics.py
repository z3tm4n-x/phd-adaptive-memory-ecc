"""Addressed controller transplant checks, not a new theorem."""
import json,math,copy
import numpy as np
from scipy.linalg import expm
from reference import ROOT,config,core,accepted,sr_ledger,packed

def main():
    c=config();D=60;lo=c['environment']['b_low'];hi=c['environment']['b_high'];rng=np.random.default_rng(721664)
    # Block moment ODE, independent of the accepted scalar closed form.
    Q=np.array([[-1/D,1/D],[1/D,-1/D]]);B=np.diag([lo,hi]);A=np.zeros((6,6))
    A[:2,:2]=Q;A[2:4,2:4]=Q;A[4:,4:]=Q;A[2:4,:2]=B;A[4:,2:4]=2*B
    maximum=0.
    for duration in [1e-8,.01,.2,.5,1,60,300,1800]:
        direct=expm(A*duration);m,s=core.moments(duration,D,lo,hi)
        for z in range(2):
            expected1=direct[2:4,z].sum();expected2=direct[4:,z].sum()
            maximum=max(maximum,abs(m[z]-expected1)/max(1,hi*duration),abs(s[z]-expected2)/max(1,(hi*duration)**2))
    assert maximum<1e-10
    model=core.build_model(c,D,cache=False);p=accepted.pack(model,c['epsilon'][0]);matches=0;posterior_checks=0
    for _ in range(100):
        q=rng.dirichlet(np.ones(26));rem=int(rng.integers(1,len(model.value)));slack=float(rng.uniform(0,.1))
        # Baseline state may not admit backup because arbitrary q; compare both errors.
        try:
            actual=accepted._choose(q,slack,rem,p.H,p.J,p.constant,p.coefficient,p.first,p.second,p.ticks,p.tick,p.words,p.dwell,p.low,p.high)[0]
        except ValueError:actual=-1
        selected=-1;V=math.fsum(float(q[i])*float(model.value[rem,i]) for i in range(26))
        for a in range(len(model.periods)-1,-1,-1):
            dt=min(rem,int(model.ticks[a]))
            reward=core.reward_vector(dt*p.tick,c,D) if model.ticks[a]>rem else model.reward[a]
            future=np.zeros(26) if model.ticks[a]>rem else model.transition[a]@model.value[rem-dt]
            value=math.fsum(float(q[i])*(float(reward[i])+float(future[i])) for i in range(26))-V
            if value<=slack*dt/rem+1e-13:selected=a;break
        assert selected==actual;matches+=1
    for enabled in [False,True]:
        q=p.initial.copy()
        for i in range(1000):
            a=i%len(p.periods);count=[0,1,4,12,32,100][i%6]
            actual,likelihood=accepted._observe(q,a,count,enabled,p.kernels,p.transition)
            matrix=p.kernels[a,min(count,32)] if enabled else p.transition[a]
            raw=np.array([math.fsum(float(q[k])*float(matrix[k,j]) for k in range(26)) for j in range(26)])
            expected=raw/math.fsum(raw)
            assert np.max(np.abs(actual-expected))<1e-13 and np.isfinite(actual).all()
            q=actual;posterior_checks+=1
    finer=copy.deepcopy(c);finer['controller']['one_switch_midpoints']*=2;finer['controller']['two_switch_midpoints']*=2
    refined=core.build_model(finer,D,cache=False)
    difference=float(np.abs(model.kernels-refined.kernels).sum(axis=(1,3)).max())
    original_quadrature=model.error['per_pass']['midpoint_one_switch']+model.error['per_pass']['midpoint_two_switch']
    assert difference<2*original_quadrature
    result=dict(moment_block_exponential_scaled_error=maximum,independent_action_expression_matches=matches,posterior_updates_against_fsum=posterior_checks,sr_arithmetic=sr_ledger(c),refined_grid_kernel_row_l1_difference=difference,initial_potential_refined=float(refined.initial@refined.value[-1]),initial_potential_original=float(model.initial@model.value[-1]),shared='accepted kernels/reward and numpy/scipy; decision expression independent but not full independent policy implementation',scope='finite addressed checks plus conditional SR arithmetic ledger, not platform WCET/physical proof')
    (ROOT/'outputs/numerical_checks.json').write_text(json.dumps(result,indent=2)+'\n',newline='\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
