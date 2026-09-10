"""Independent, killed joint CTMC oracle on a SMALL actual SEC memory.

State = (environment, clean/one-error mask). Same-bit toggles return a dirty
word to clean; a different-bit toggle is absorbed permanently. The oracle
neither calls the auxiliary scan kernel nor the pair-reward helper.
"""
from __future__ import annotations
from functools import lru_cache
import copy
import json
import numpy as np
from scipy.linalg import expm
from core import load_config,build_model


class ExactOracle:
    def __init__(self,cfg,dwell):
        self.cfg=cfg;self.w=cfg['memory']['words'];self.n=cfg['memory']['bits_per_word']
        self.p=cfg['memory']['pass_seconds'];self.dwell=dwell
        self.masks=1<<self.w;self.S=2*self.masks
        rates=[cfg['environment']['b_low'],cfg['environment']['b_high']]
        self.G=np.zeros((self.S,self.S))
        for z in range(2):
            for mask in range(self.masks):
                i=z*self.masks+mask
                self.G[i,(1-z)*self.masks+mask]+=1/dwell
                self.G[i,i]-=1/dwell+rates[z]
                for word in range(self.w):
                    dirty=(mask>>word)&1
                    rate=rates[z]/self.w/(self.n if dirty else 1)
                    self.G[i,z*self.masks+(mask^(1<<word))]+=rate
        self.initial=np.zeros(self.S);self.initial[0]=self.initial[self.masks]=0.5

    @lru_cache(maxsize=128)
    def flow(self,duration):
        if duration< -1e-12: raise ValueError('negative CTMC duration')
        return expm(self.G*max(0.,duration))

    @lru_cache(maxsize=128)
    def kernel(self,period,horizon=None):
        h=period if horizon is None else min(period,horizon)
        wait=period-self.p
        # An unnormalized joint matrix in (count, initial state, current state).
        V=np.zeros((self.w+1,self.S,self.S));V[0]=self.flow(min(h,wait))
        if h<=wait: return V
        previous=wait
        for word in range(self.w):
            reset=wait+(word+1)*self.p/self.w
            if reset>h+1e-12: break
            V=V@self.flow(round(reset-previous,14));new=np.zeros_like(V)
            for c in range(word+1):
                for state in range(self.S):
                    z,mask=divmod(state,self.masks);dirty=(mask>>word)&1
                    dest=z*self.masks+(mask&~(1<<word))
                    new[c+dirty,:,dest]+=V[c,:,state]
            V=new;previous=reset
        if h>previous+1e-13: V=V@self.flow(round(h-previous,14))
        return V

    def evaluate(self,model,epsilon,enabled=True,max_nodes=100000):
        tick=self.cfg['controller']['time_tick_seconds']
        total=int(round(self.cfg['horizon_seconds']/tick))
        slack=epsilon-model.error['whole_horizon_delta']-float(model.initial@model.value[-1])
        if slack<0: return {'initial_certificate':False,'initial_slack':slack}
        # actual is SUBPROBABILITY. It is never normalized after observation.
        stack=[(0,model.initial,slack,self.initial,0.,[])]
        fail=survive=cost_survive=cost_stop=0.;nodes=0;witness=[]
        while stack:
            t,q,s,actual,passes,history=stack.pop();nodes+=1
            if nodes>max_nodes: raise RuntimeError('oracle tree exceeds declared node limit')
            remaining=total-t
            a,snew,D=model.choose(t,q,s);dt=min(remaining,int(model.ticks[a]))
            period=float(model.periods[a]);h=dt*tick
            K=self.kernel(period,h)
            branch=np.einsum('i,cij->cj',actual,K)
            live=float(branch.sum());lost=float(actual.sum())-live
            if lost< -1e-11: raise ArithmeticError('negative absorbed mass')
            fail+=max(0,lost)
            cost_stop+=passes*max(0,lost)
            if t+dt>=total:
                survive+=live
                completed=1 if model.ticks[a]<=remaining else 0
                cost_survive+=(passes+completed)*live
                cost_stop+=(passes+completed)*live
                if len(witness)<15: witness.append({'history':history,'last_period':period,'survival_mass':live})
                continue
            for count in range(self.w+1):
                mass=float(branch[count].sum())
                if mass==0: continue
                qnew,likelihood=model.observe(q,a,count,enabled)
                stack.append((t+dt,qnew,snew,branch[count],passes+1,
                              history+[(round(t*tick,8),period,count,round(float(qnew[model.cfg['controller']['pending_cap']+1:].sum()),8))]))
        return dict(initial_certificate=True,first_passage=fail,survival=survive,
                    mass_residual=fail+survive-1,exact_tree_nodes=nodes,
                    passes_conditional_survival=cost_survive/survive,
                    complete_passes_stop_lower=cost_stop,epsilon=epsilon,
                    safety_margin=epsilon-fail,trace_samples=witness)


def run():
    cfg=copy.deepcopy(load_config())
    # Oracle-only stress case: few actual words, nonnegligible scan phase and
    # repeated toggles. Production inputs remain untouched.
    cfg['memory']['words']=2;cfg['memory']['pass_seconds']=0.12
    cfg['environment']['b_low']=0.04;cfg['environment']['b_high']=0.45
    cfg['horizon_seconds']=6.
    dwell=3.;model=build_model(cfg,dwell,cache=False);oracle=ExactOracle(cfg,dwell)
    results=[]
    for eps in [0.15,0.19]:
        for enabled in [True,False]:
            row=oracle.evaluate(model,eps,enabled)
            row['counts_enabled']=enabled;results.append(row)
    # Explicit first-pass transition: summing over counter values does not
    # reset words dirtied after their individual scan credit.
    K=oracle.kernel(0.5)
    live=oracle.initial@K.sum(axis=0)
    residual_dirty=sum(live[i] for i in range(oracle.S) if i%oracle.masks!=0)
    checks={'initial_backup':float(model.initial@model.value[-1]),
            'positive_post_pass_dirty_mass':float(residual_dirty),
            'first_pass_absorbed':float(1-live.sum()),
            'kernel_substochastic_max':float(K.sum(axis=(0,2)).max()),
            'settings':cfg,'results':results}
    from pathlib import Path
    p=Path(__file__).resolve().parent/'outputs'/'small_exact_oracle.json'
    p.write_text(json.dumps(checks,indent=2))
    print(json.dumps({k:v for k,v in checks.items() if k not in ['settings','results']},indent=2))
    for r in results: print({k:v for k,v in r.items() if k!='trace_samples'})
    return checks

if __name__=='__main__': run()
