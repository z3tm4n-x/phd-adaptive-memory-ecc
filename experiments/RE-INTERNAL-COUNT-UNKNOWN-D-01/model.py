"""Own-count filtering with one unknown, mission-constant switching rate.

Per rate: four probabilities Pr(Z,K=0/>0) and two moments E[K 1{Z=z}].
These are auxiliary-arrival statistics, not a posterior conditioned on survival.
See derivation.md for the physical coupling and stopped risk-potential proof.
"""
from __future__ import annotations
import json
import math
import time
from pathlib import Path
from dataclasses import dataclass
import numpy as np
from numba import njit

ROOT=Path(__file__).resolve().parent

def config():
    return json.loads((ROOT/'config.json').read_text())

def rate_grid(cfg):
    if cfg['controller']['grid_intervals']!=32:
        raise ValueError('The production continuum certificate is pinned to 32 cells')
    return (32.+9.*np.arange(33))**2/(3000.*32**2)

@njit(cache=True)
def moments(h,a,low,high):
    if h==0.:
        return np.zeros(2),np.zeros(2)
    k=2*a;x=k*h;mean=(low+high)/2;d=(high-low)/2
    A=-math.expm1(-x)/k
    if x<.2:
        term=.5;B=term
        for j in range(1,24):
            term*=-x/(j+2);B+=term
        B*=h*h
    else:
        B=(h-A)/k
    first=np.array([max(0.,mean*h-d*A),mean*h+d*A])
    base=mean*mean*h*h+2*d*d*B
    second=np.array([max(0.,base-2*mean*d*h*A),base+2*mean*d*h*A])
    return first,second

def positive_exponential(Q,duration):
    if duration==0.: return np.eye(len(Q))
    rate=float(-np.min(np.diag(Q)))
    s=max(0,int(math.ceil(math.log2(rate*duration))))
    mu=rate*duration/(2**s)
    B=np.maximum(np.eye(len(Q))+Q/rate,0.)
    term=np.eye(len(Q));weight=math.exp(-mu);result=weight*term
    for k in range(1,65):
        term=term@B;weight*=mu/k;result+=weight*term
    for _ in range(s): result=result@result
    result/=result.sum(axis=1)[:,None]
    return result

def idle(duration,a,low,high):
    # State: z+2*1{at least one observed arrival}.
    Q=np.zeros((4,4))
    for c in range(2):
        for z,b in enumerate((low,high)):
            i=z+2*c;Q[i,1-z+2*c]=a;Q[i,i]=-a
            if c==0: Q[i,z+2]=b;Q[i,i]-=b
    return positive_exponential(Q,duration)[:2].reshape(2,2,2)

def scan_basis(cfg):
    """Positive 0/1/2-switch quadratures, independent of switching rate.

    Six components: C0K0,C0K+,C+K0,C+K+, E[K;C0],E[K;C+].
    K is unbounded; its zero probability and first moment are retained exactly
    for each quadrature path. There is no pending-count truncation.
    """
    w=cfg['memory']['words'];P=cfg['memory']['pass_seconds']
    low=cfg['environment']['b_low'];high=cfg['environment']['b_high']
    n1=cfg['controller']['one_switch_midpoints'];n2=cfg['controller']['two_switch_midpoints']
    def F(x): return np.maximum(np.asarray(x)-.5/w,0.)**2/2
    f1=float(F(1.));u=(np.arange(n1)+.5)/n1
    v=(np.arange(n2)+.5)/n2;x,y=np.meshgrid(v,v,indexing='ij');x=x.ravel();y=y.ravel();v2=x+(1-x)*y
    out=np.zeros((2,3,6))
    for z in range(2):
        b0,b1=(low,high) if z==0 else (high,low)
        for order in range(3):
            if order==0:
                pend=np.array([P*b0*f1]);obs=np.array([P*b0])-pend;weight=np.ones(1)
            elif order==1:
                pend=P*(b0*F(u)+b1*(f1-F(u)))
                obs=P*(b0*u+b1*(1-u))-pend;weight=np.full(n1,1/n1)
            else:
                pend=P*(b0*F(x)+b1*(F(v2)-F(x))+b0*(f1-F(v2)))
                obs=P*(b0*x+b1*(v2-x)+b0*(1-v2))-pend;weight=2*(1-x)/(n2*n2)
            if np.min(pend)<0 or np.min(obs)<0: raise ArithmeticError('negative Poisson mean')
            ec=np.exp(-obs);ek=np.exp(-pend);pc=-np.expm1(-obs);pk=-np.expm1(-pend)
            terms=np.array([ec*ek,ec*pk,pc*ek,pc*pk,pend*ec,pend*pc]).T
            out[z,order]=weight@terms
    return out

def poisson_tail3(mu):
    term=math.exp(-mu)*mu**3/6;total=term
    for j in range(4,132): term*=mu/j;total+=term
    return total

def scan_from_basis(cfg,a,basis):
    nu=cfg['memory']['pass_seconds']*a
    p0=math.exp(-nu);weights=(p0,p0*nu,p0*nu*nu/2)
    out=np.zeros((2,2,6))
    for z in range(2):
        for n in range(3): out[z,z^(n%2)]+=weights[n]*basis[z,n]
        out[z,z,0]+=poisson_tail3(nu)
    return out

def combine(idle_matrix,scan):
    # kernel[y, old-probability-state, new six statistics]
    birth=np.zeros((2,2,6))
    for c0 in range(2):
        for c1 in range(2):
            y=min(1,c0+c1)
            for z in range(2):
                for mid in range(2):
                    for zz in range(2):
                        weight=idle_matrix[z,c0,mid]
                        birth[y,z,zz]+=weight*scan[mid,zz,2*c1]
                        birth[y,z,2+zz]+=weight*scan[mid,zz,2*c1+1]
                        birth[y,z,4+zz]+=weight*scan[mid,zz,4+c1]
    out=np.zeros((2,4,6))
    out[:,:2]=birth
    out[1,2:]=birth.sum(axis=0)
    return out

def model_error(cfg,a):
    cc=cfg['controller'];P=cfg['memory']['pass_seconds'];w=cfg['memory']['words']
    hi=cfg['environment']['b_high'];lo=cfg['environment']['b_low'];v=(hi-lo)*P;nu=P*a
    p1=math.exp(-nu)*nu;p2=p1*nu/2
    per=dict(omitted_switches=poisson_tail3(nu),
             one_switch_quadrature=p1*(4*v+4*v*v)/(24*cc['one_switch_midpoints']**2),
             two_switch_quadrature=p2*(40*v+40*v*v)/(24*cc['two_switch_midpoints']**2),
             finite_word_smoothing=P*(hi+nu*(hi-lo))/(4*w*w))
    N=int(cfg['horizon_seconds']/min(cfg['periods_seconds']))
    return N*sum(per.values()),per

def arithmetic_ledger(cfg):
    cc=cfg['controller'];H=cfg['horizon_seconds'];W=cfg['memory']['words']
    high=cfg['environment']['b_high'];mu=high*cfg['memory']['pass_seconds']/2
    N=int(H/min(cfg['periods_seconds']));Nb=int(math.ceil(H/cc['backup_period_seconds']))
    u=2.**-53;g=lambda j:j*u/(1-j*u);kap=cc['kernel_relative_error_contract']
    Vmax=(H+cc['backup_period_seconds'])*(mu*high+high*high*cc['backup_period_seconds']/2)/W
    Rsum=H*(mu*high+high*high*max(cfg['periods_seconds'])/2)/W
    eta=math.expm1(4*N*(kap+g(128)))
    eV=8*(g(512*Nb)+Nb*kap)*Vmax
    terms=dict(filter=(2*N*Vmax+Rsum)*eta,value=2*N*eV,
               arithmetic=N*g(4096)*(4*Vmax+2*Rsum)+N*1e-13,
               positive_kernel=N*8*kap,
               slack_accumulation=g(2*N)*(cfg['epsilon']+Rsum+2*N*Vmax),
               slack_comparisons=N*g(32)*(cfg['epsilon']+Rsum+2*N*Vmax),underflow=1e-100)
    total=sum(terms.values())
    ll=4*N*(kap+g(128))+2*g(4*N+256)*N*80
    return dict(terms=terms,total=total,reserved=cc['numerical_allowance'],
                covered=total<cc['numerical_allowance'],loglikelihood_error_bound=ll,
                likelihood_margin_covered=2*ll<cc['test_log_margin'],Vmax=Vmax,Rsum=Rsum,
                coefficient_contract=kap,elementary_functions_max_ulp=4)

@njit(cache=True)
def value_tables(rates,periods,ticks,kernels,total_ticks,tick,low,high,words,backup):
    M=len(rates);A=len(periods)
    transition=np.zeros((M,A,2,2));pending=np.zeros_like(transition)
    first=np.empty((M,A,2));second=np.empty_like(first)
    V=np.zeros((M,total_ticks+1,4))
    for j in range(M):
        for a in range(A):
            m1,m2=moments(periods[a],rates[j],low,high)
            first[j,a]=m1/words;second[j,a]=m2/(2*words)
            for z in range(2):
                for zz in range(2):
                    for y in range(2):
                        transition[j,a,z,zz]+=kernels[j,a,y,z,zz]+kernels[j,a,y,z,2+zz]
                        pending[j,a,z,zz]+=kernels[j,a,y,z,4+zz]
        nb=ticks[backup]
        for r in range(1,total_ticks+1):
            if r<nb:
                m1,m2=moments(r*tick,rates[j],low,high)
                V[j,r,:2]=m2/(2*words);V[j,r,2:]=m1/words
            else:
                for z in range(2):
                    c=second[j,backup,z]
                    for zz in range(2):
                        c+=transition[j,backup,z,zz]*V[j,r-nb,zz]+pending[j,backup,z,zz]*V[j,r-nb,2+zz]
                    V[j,r,z]=c;V[j,r,2+z]=first[j,backup,z]
    return transition,pending,first,second,V

@dataclass
class Bank:
    cfg: dict
    rates: np.ndarray
    kernels: np.ndarray
    transition: np.ndarray
    pending: np.ndarray
    first: np.ndarray
    second: np.ndarray
    value: np.ndarray
    slack0: np.ndarray
    periods: np.ndarray
    ticks: np.ndarray
    errors: np.ndarray
    build_seconds: float

    def initial(self):
        q=np.zeros((len(self.rates),6));q[:,:2]=.5
        return q,self.slack0.copy(),np.zeros(len(q)),np.zeros(len(q),np.bool_),np.ones(len(q),np.bool_)


def build(cfg=None):
    cfg=cfg or config();start=time.perf_counter();rates=rate_grid(cfg)
    P=cfg['memory']['pass_seconds'];low=cfg['environment']['b_low'];high=cfg['environment']['b_high']
    periods=np.array(cfg['periods_seconds'],float);tick=cfg['controller']['time_tick_seconds']
    ticks=np.rint(periods/tick).astype(np.int64);basis=scan_basis(cfg)
    kernels=np.empty((len(rates),len(periods),2,4,6))
    for j,a in enumerate(rates):
        scan=scan_from_basis(cfg,a,basis)
        for k,h in enumerate(periods): kernels[j,k]=combine(idle(h-P,a,low,high),scan)
    residual=np.max(np.abs(kernels[:,:,:,:,:4].sum(axis=(2,4))-1))
    if residual>1e-12 or kernels.min()<0: raise ArithmeticError('invalid probability kernels')
    total=int(round(cfg['horizon_seconds']/tick));backup=int(np.flatnonzero(periods==cfg['controller']['backup_period_seconds'])[0])
    T,J,m1,m2,V=value_tables(rates,periods,ticks,kernels,total,tick,low,high,cfg['memory']['words'],backup)
    errs=np.array([model_error(cfg,a)[0] for a in rates])
    G=cfg['controller']['continuous_transfer_factor'];beta=cfg['controller']['beta']/G
    budget=cfg['epsilon']/G-beta-errs-cfg['controller']['numerical_allowance']
    slack=budget-.5*(V[:,-1,0]+V[:,-1,1])
    if slack.min()<0: raise ValueError('common backup not certified')
    ledger=arithmetic_ledger(cfg)
    if not ledger['covered'] or not ledger['likelihood_margin_covered']:
        raise ArithmeticError('declared numerical allowance is insufficient')
    return Bank(cfg,rates,kernels,T,J,m1,m2,V,slack,periods,ticks,errs,time.perf_counter()-start)

@njit(cache=True)
def delta_for(j,a,remaining,q,T,J,m1,m2,V,ticks,tick,rates,low,high,words):
    p0=q[j,0]+q[j,2];p1=q[j,1]+q[j,3];k0=q[j,4];k1=q[j,5]
    cur=p0*V[j,remaining,0]+p1*V[j,remaining,1]+k0*V[j,remaining,2]+k1*V[j,remaining,3]
    dt=min(remaining,ticks[a]);nr=remaining-dt
    if ticks[a]>remaining:
        f,s=moments(dt*tick,rates[j],low,high)
        reward=(k0*f[0]+k1*f[1]+.5*(p0*s[0]+p1*s[1]))/words
        return reward-cur
    reward=p0*m2[j,a,0]+p1*m2[j,a,1]+k0*m1[j,a,0]+k1*m1[j,a,1]
    for z in range(2):
        fut=0.
        for zz in range(2):
            fut+=T[j,a,z,zz]*V[j,nr,zz]+J[j,a,z,zz]*V[j,nr,2+zz]
        reward+=(p0 if z==0 else p1)*fut
    return reward-cur

@njit(cache=True)
def choose(remaining,q,slack,active,T,J,m1,m2,V,ticks,tick,rates,low,high,words,backup):
    if not np.any(active): return backup
    for a in range(len(ticks)-1,-1,-1):
        dt=min(remaining,ticks[a]);ok=True
        for j in range(len(rates)):
            if active[j]:
                d=delta_for(j,a,remaining,q,T,J,m1,m2,V,ticks,tick,rates,low,high,words)
                if d>slack[j]*dt/remaining+1e-13:
                    ok=False;break
        if ok: return a
    raise ArithmeticError('backup lost feasibility')

@njit(cache=True)
def spend(a,remaining,q,slack,active,T,J,m1,m2,V,ticks,tick,rates,low,high,words,backup):
    for j in range(len(rates)):
        if active[j]:
            d=delta_for(j,a,remaining,q,T,J,m1,m2,V,ticks,tick,rates,low,high,words)
            slack[j]=max(0.,slack[j]-d)

@njit(cache=True)
def observe(a,count,q,scores,rejected,active,kernels,learning,threshold):
    y=0 if count==0 else 1;M=len(q);tmp=np.zeros(6)
    for j in range(M):
        tmp[:]=0.
        for old in range(4):
            for new in range(6): tmp[new]+=q[j,old]*kernels[j,a,y,old,new]
        lik=tmp[0]+tmp[1]+tmp[2]+tmp[3]
        if lik<=0: raise ArithmeticError('zero likelihood')
        for new in range(6): q[j,new]=tmp[new]/lik
        scores[j]+=math.log(lik)
    top=np.max(scores);total=0.
    for j in range(M): scores[j]-=top;total+=math.exp(scores[j])
    logmix=math.log(total/M)
    if learning:
        for j in range(M):
            if logmix-scores[j]>threshold: rejected[j]=True
        active[:]=False
        for j in range(M-1):
            if not(rejected[j] and rejected[j+1]): active[j]=True;active[j+1]=True
    else:
        active[:]=True

def controller_args(bank):
    c=bank.cfg
    return (bank.transition,bank.pending,bank.first,bank.second,bank.value,bank.ticks,
            c['controller']['time_tick_seconds'],bank.rates,c['environment']['b_low'],
            c['environment']['b_high'],c['memory']['words'],int(np.flatnonzero(bank.periods==1.)[0]))

if __name__=='__main__':
    bank=build();c=bank.cfg;G=c['controller']['continuous_transfer_factor']
    out=dict(build_seconds=bank.build_seconds,minimum_initial_slack=float(bank.slack0.min()),
             maximum_backup_cost=float(np.max(.5*(bank.value[:,-1,0]+bank.value[:,-1,1]))),
             max_model_error=float(bank.errors.max()),arithmetic=arithmetic_ledger(c),
             kernel_bytes=bank.kernels.nbytes,value_bytes=bank.value.nbytes,
             formal_continuum_limit=c['epsilon'],transfer_factor=G)
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs'/'initial_certificate.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
