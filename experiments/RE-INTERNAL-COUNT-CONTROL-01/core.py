"""Finite auxiliary-count filter and a whole-horizon risk-budget controller.

The auxiliary system counts pending ARRIVALS, not physical erroneous bits.
Its observations coincide with real corrections up to the first repeated hit
of ANY bit of an uncleared word. This deliberately pessimistic coupling also
charges harmless same-bit cancellations. No hidden survival flag enters the
controller. See derivation.md before interpreting a normalized filter vector.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
import math
import time
from pathlib import Path
from decimal import Decimal, localcontext
import numpy as np


ROOT=Path(__file__).resolve().parent

def load_config():
    return json.loads((ROOT/'config.json').read_text())


def moments(t: float, dwell: float, low: float, high: float):
    """E[integrated rate], E[integrated rate**2], for each start mode."""
    if t < 0: raise ValueError('negative exposure')
    if t == 0: return np.zeros(2),np.zeros(2)
    k=2/dwell; x=k*t; m=(low+high)/2; d=(high-low)/2
    A=-math.expm1(-x)/k
    if x<0.2:
        term=0.5; B=term
        for j in range(1,18):
            term *= -x/(j+2); B += term
        B*=t*t
    else: B=(t-A)/k
    first=np.array([m*t-d*A,m*t+d*A])
    base=m*m*t*t+2*d*d*B
    second=np.array([base-2*m*d*t*A,base+2*m*d*t*A])
    return np.maximum(first,0),np.maximum(second,0)


def poisson_tail(k: int, mu):
    """Positive Poisson tail series, for the scan means (all <= 1.2).

    Terms through k+127 are retained. The neglected tail is below 1e-200
    for the present bounded means; no subtractive survival-function call.
    """
    mu=np.asarray(mu,dtype=float)
    if np.any(mu>1.2) or k<1: raise ValueError('tail series outside declared range')
    term=np.exp(-mu)
    for j in range(1,k+1): term=term*mu/j
    total=term.copy()
    for j in range(k+1,k+128):
        term=term*mu/j;total=total+term
    return total


def arithmetic_ledger(cfg: dict,dwell: float):
    """A priori IEEE-754 error reserve; not a residual-as-proof argument.

    The elementary exp/expm1 calls are assumed accurate to <=4 ulp; changing
    that contract requires rebuilding the ledger. See derivation.md for the
    operation-count, stochastic-product and filter projective bounds.
    """
    cc=cfg['controller'];S=2*(cc['pending_cap']+1);d=2*(cc['count_cap']+1)
    w=cfg['memory']['words'];p=cfg['memory']['pass_seconds'];H=cfg['horizon_seconds']
    hi=cfg['environment']['b_high'];tb=cc['backup_period_seconds'];u=2.**-53
    g=lambda n:n*u/(1-n*u)
    N=int(H/min(cfg['periods_seconds']));Nb=int(math.ceil(H/tb))
    F=2**max(0,int(math.ceil(math.log2((hi+1/dwell)*(max(cfg['periods_seconds'])-p)))))
    M=cc['two_switch_midpoints']**2
    etaK=4*(F*g(40*d+1000)+(F-1)*g(d+10)+g(6*M+8*(cc['count_cap']+1)**2+500))
    Vmax=(H+tb)*(cc['pending_cap']*hi+hi*hi*tb/2)/w
    Rsum=H*(cc['pending_cap']*hi+hi*hi*max(cfg['periods_seconds'])/2)/w
    eq=math.expm1(4*N*g(4*S+20))
    eV=2*Nb*g(16*S+500)*max(Vmax,1e-12)
    terms=dict(kernel_coupling=N*etaK,
               filtering=(2*N*Vmax+Rsum)*eq,
               value_recursion=2*N*eV,
               action_arithmetic=N*g(2000)*(4*Vmax+2*Rsum)+N*1e-13,
               underflow_and_series=1e-100)
    bound=sum(terms.values())
    return dict(terms=terms,total_bound=bound,reserve=cc['numerical_allowance'],
                covered=bound<=cc['numerical_allowance'],elementary_function_ulp_assumption=4)


def poisson_capped(mu: np.ndarray, cap: int):
    """Columns 0..cap-1 are exact counts; cap is their overflow bin."""
    mu=np.atleast_1d(mu).astype(float)
    out=np.empty((len(mu),cap+1)); out[:,0]=np.exp(-mu)
    for i in range(1,cap): out[:,i]=out[:,i-1]*mu/i
    out[:,cap]=poisson_tail(cap,mu)
    return out


def positive_exponential(Q: np.ndarray, duration: float):
    """Uniformization with nonnegative arithmetic and dyadic squaring.

    The series is stopped at 32 at Poisson mean <= 1; missing mass < 5e-37.
    Small row normalization is charged to the numerical allowance, not used
    as an empirical certificate. See the explicit rounding ledger.
    """
    dim=len(Q)
    if duration==0: return np.eye(dim)
    rate=max(float(-Q.diagonal().min()),0)
    if rate==0: return np.eye(dim)
    squarings=max(0,int(math.ceil(math.log2(rate*duration))))
    mu=rate*duration/(2**squarings)
    B=np.eye(dim)+Q/rate
    if B.min() < -1e-14: raise ArithmeticError('invalid uniformization matrix')
    B=np.maximum(B,0)
    with localcontext() as c:
        c.prec=80; weight=float((-Decimal.from_float(mu)).exp())
    term=np.eye(dim); result=weight*term
    for j in range(1,33):
        term=term@B; weight*=mu/j; result+=weight*term
    for _ in range(squarings): result=result@result
    result=np.maximum(result,0)
    result/=result.sum(axis=1,keepdims=True)
    return result


def idle_kernel(duration: float, dwell: float, rates: np.ndarray, count_cap: int):
    """(start mode, capped arrival count, end mode)."""
    dim=2*(count_cap+1); Q=np.zeros((dim,dim)); a=1/dwell
    for count in range(count_cap+1):
        for z in range(2):
            i=2*count+z; Q[i,2*count+1-z]+=a; Q[i,i]-=a
            if count<count_cap:
                Q[i,2*(count+1)+z]+=rates[z]; Q[i,i]-=rates[z]
    E=positive_exponential(Q,duration)
    return E[:2].reshape(2,count_cap+1,2)


def scan_exact_small(words: int, p: float, dwell: float, rates: np.ndarray, C: int, K: int):
    """Independent-in-time piecewise-exact finite count kernel for a small W.

    Within phase j, fraction j/W of uniform word marks is already scanned.
    Sparse uniformization implements environment jumps and two capped counts.
    """
    result=np.zeros((2,2,C+1,K+1)); a=1/dwell; rate=max(rates)+a
    h=p/words; mu=rate*h
    if mu>1: raise ValueError('small oracle uniformization needs smaller substeps')
    for z0 in range(2):
        v=np.zeros((2,C+1,K+1));v[z0,0,0]=1
        for j in range(words):
            f=j/words
            current=v.copy(); weight=math.exp(-mu); new=weight*current
            for order in range(1,40):
                nxt=np.zeros_like(current)
                for z in range(2):
                    rc=rates[z]*(1-f)/rate; rk=rates[z]*f/rate
                    # The diagonal term includes self-jumps at a capped count.
                    nxt[z]+=(1-a/rate-rc-rk)*current[z]
                    nxt[1-z]+=a/rate*current[z]
                    nxt[z,1:,:]+=rc*current[z,:-1,:]
                    nxt[z,-1,:]+=rc*current[z,-1,:]
                    nxt[z,:,1:]+=rk*current[z,:,:-1]
                    nxt[z,:,-1]+=rk*current[z,:,-1]
                current=nxt;weight*=mu/order;new+=weight*current
            v=new
        result[z0]=v
    return result.transpose(0,2,1,3)


def scan_kernel(cfg: dict, dwell: float):
    """Joint observed/pending counts during one R2-U pass.

    For production, integrate paths with 0, 1, 2 environment switches; charge
    omitted switch paths, deterministic quadrature and finite-word smoothing.
    """
    cc=cfg['controller']; C=cc['count_cap'];K=cc['pending_cap']
    w=cfg['memory']['words'];p=cfg['memory']['pass_seconds']
    rates=np.array([cfg['environment']['b_low'],cfg['environment']['b_high']])
    if w<=16: return scan_exact_small(w,p,dwell,rates,C,K)
    nu=p/dwell; prob0=math.exp(-nu);prob1=prob0*nu;prob2=prob1*nu/2
    tail=float(poisson_tail(3,nu))
    # Integral of a shifted linear scan fraction. Its primitive differs from
    # the exact discrete-word primitive by at most P/(8 W^2).
    shift=0.5/w
    def F(u): return np.maximum(np.asarray(u)-shift,0)**2/2
    F1=float(F(1))
    kernel=np.zeros((2,C+1,2,K+1))
    def add(start, end, weight, pending, total):
        pc=poisson_capped(np.maximum(total-pending,0),C)
        pk=poisson_capped(np.maximum(pending,0),K)
        weights=np.broadcast_to(weight,(len(pc),))
        kernel[start,:,end,:]+=(pc*weights[:,None]).T@pk
    m1=cc['one_switch_midpoints'];u=(np.arange(m1)+0.5)/m1
    m2=cc['two_switch_midpoints'];vv=(np.arange(m2)+0.5)/m2
    x,y=np.meshgrid(vv,vv,indexing='ij');x=x.ravel();y=y.ravel()
    second=x+(1-x)*y
    for z in range(2):
        b0,b1=rates[z],rates[1-z]
        add(z,z,prob0,np.array([b0*p*F1]),np.array([b0*p]))
        pending=p*(b0*F(u)+b1*(F1-F(u)))
        total=p*(b0*u+b1*(1-u))
        add(z,1-z,prob1/m1,pending,total)
        pending=p*(b0*F1+(b1-b0)*(F(second)-F(x)))
        total=p*(b0+(b1-b0)*(second-x))
        add(z,z,prob2*2*(1-x)/(m2*m2),pending,total)
        # A specified replacement law for omitted paths; never silently drop
        # probability mass. The full omitted mass is charged in delta.
        kernel[z,0,z,0]+=tail
    kernel/=kernel.sum(axis=(1,2,3))[:,None,None,None]
    return kernel


def error_ledger(cfg: dict, dwell: float):
    cc=cfg['controller'];p=cfg['memory']['pass_seconds'];w=cfg['memory']['words']
    high=cfg['environment']['b_high'];low=cfg['environment']['b_low']
    nu=p/dwell; v=(high-low)*p
    p1=math.exp(-nu)*nu;p2=p1*nu/2
    nmax=int(math.floor(cfg['horizon_seconds']/min(cfg['periods_seconds'])))
    if w<=16:
        omitted=quad1=quad2=smoothing=0.0
    else:
        omitted=float(poisson_tail(3,nu))
        # L1 distribution bounds, conservatively used directly as TV bounds.
        quad1=p1*(4*v+4*v*v)/(24*cc['one_switch_midpoints']**2)
        quad2=p2*(40*v+40*v*v)/(24*cc['two_switch_midpoints']**2)
        smoothing=p*(high+nu*(high-low))/(4*w*w)
    # K=cap is retained; only K>cap can change the next observed count.
    pending_tail=float(poisson_tail(cc['pending_cap']+1,high*p/2))
    components=dict(omitted_switch_paths=omitted,midpoint_one_switch=quad1,
                    midpoint_two_switch=quad2,discrete_scan_smoothing=smoothing,
                    pending_overflow=pending_tail)
    delta=nmax*sum(components.values())+cc['numerical_allowance']
    rounding=arithmetic_ledger(cfg,dwell)
    if w>16 and not rounding['covered']: raise ArithmeticError('numerical reserve insufficient')
    return dict(per_pass=components,max_complete_passes=nmax,arithmetic=rounding,
                numerical_allowance=cc['numerical_allowance'],whole_horizon_delta=delta)


def combine(idle: np.ndarray, scan: np.ndarray, C: int, K: int):
    """K_tau[y, old state, new state], old/new state = z*(K+1)+k."""
    base=np.zeros((C+1,2,2,K+1))
    for i in range(C+1):
        for j in range(C+1):
            y=min(C,i+j)
            base[y]+=np.einsum('ab,bck->ack',idle[:,i,:],scan[:,j,:,:])
    S=2*(K+1);out=np.zeros((C+1,S,S))
    for z in range(2):
        for k in range(K+1):
            for y0 in range(C+1):
                y=min(C,k+y0)
                out[y,z*(K+1)+k,:]+=base[y0,z].reshape(-1)
    return out


@dataclass
class Model:
    cfg: dict
    dwell: float
    kernels: np.ndarray
    transition: np.ndarray
    reward: np.ndarray
    value: np.ndarray
    error: dict
    periods: np.ndarray
    ticks: np.ndarray
    build_seconds: float

    @property
    def initial(self):
        q=np.zeros(self.kernels.shape[2]);K=self.cfg['controller']['pending_cap']
        q[0]=q[K+1]=0.5;return q

    def choose(self,tick: int,q: np.ndarray,slack: float):
        remaining=len(self.value)-1-tick
        if remaining<=0: raise ValueError('horizon exhausted')
        current=float(q@self.value[remaining]);K=self.cfg['controller']['pending_cap']
        for a in range(len(self.periods)-1,-1,-1):
            dt=min(remaining,int(self.ticks[a]))
            if self.ticks[a]>remaining:
                r=reward_vector(dt*self.cfg['controller']['time_tick_seconds'],self.cfg,self.dwell)
                delta=float(q@r)-current
            else:
                delta=float(q@(self.reward[a]+self.transition[a]@self.value[remaining-dt]))-current
            allowance=slack*dt/remaining
            if delta <= allowance+1e-13:
                return a,max(0.,slack-delta),delta
        raise ArithmeticError('backup lost feasibility')

    def observe(self,q: np.ndarray,a: int,count: int,enabled=True):
        T=self.kernels[a,min(count,self.cfg['controller']['count_cap'])] if enabled else self.transition[a]
        out=q@T;likelihood=float(out.sum())
        if likelihood<=0: raise ArithmeticError('zero auxiliary likelihood')
        return out/likelihood,likelihood


def reward_vector(duration: float,cfg: dict,dwell: float):
    first,second=moments(duration,dwell,cfg['environment']['b_low'],cfg['environment']['b_high'])
    K=cfg['controller']['pending_cap'];w=cfg['memory']['words']
    return np.array([(k*first[z]+0.5*second[z])/w for z in range(2) for k in range(K+1)])


def build_model(cfg: dict,dwell: float,cache=True):
    start=time.perf_counter();C=cfg['controller']['count_cap'];K=cfg['controller']['pending_cap']
    S=2*(K+1);p=cfg['memory']['pass_seconds'];periods=np.array(cfg['periods_seconds'],float)
    tick=cfg['controller']['time_tick_seconds'];ticks=np.rint(periods/tick).astype(np.int64)
    if np.max(np.abs(periods-ticks*tick))>1e-10: raise ValueError('non-grid action')
    rates=np.array([cfg['environment']['b_low'],cfg['environment']['b_high']])
    scan=scan_kernel(cfg,dwell)
    kernels=np.array([combine(idle_kernel(t-p,dwell,rates,C),scan,C,K) for t in periods])
    transition=kernels.sum(axis=1)
    row_error=float(np.max(np.abs(transition.sum(axis=2)-1)))
    if row_error>1e-10: raise ArithmeticError(f'kernel mass error {row_error}')
    reward=np.array([reward_vector(t,cfg,dwell) for t in periods])
    total_ticks=int(round(cfg['horizon_seconds']/tick));value=np.zeros((total_ticks+1,S))
    backup=int(np.flatnonzero(periods==cfg['controller']['backup_period_seconds'])[0])
    nb=int(ticks[backup])
    for rem in range(1,total_ticks+1):
        if rem<nb: value[rem]=reward_vector(rem*tick,cfg,dwell)
        else: value[rem]=reward[backup]+transition[backup]@value[rem-nb]
    ledger=error_ledger(cfg,dwell);ledger['observed_row_sum_error']=row_error
    model=Model(cfg,dwell,kernels,transition,reward,value,ledger,periods,ticks,time.perf_counter()-start)
    if cache:
        (ROOT/'cache').mkdir(exist_ok=True)
        np.savez_compressed(ROOT/'cache'/f'model_{dwell}.npz',kernels=kernels,transition=transition,reward=reward,value=value)
    return model


def main():
    cfg=load_config();rows=[]
    for dwell in cfg['environment']['mean_dwell_seconds']:
        model=build_model(cfg,dwell)
        base=float(model.initial@model.value[-1]);eps=0.1
        slack=eps-model.error['whole_horizon_delta']-base
        a,_,_=model.choose(0,model.initial,slack)
        rows.append(dict(dwell=dwell,initial_backup_bound=base,initial_slack=slack,
                         first_action=float(model.periods[a]),build_seconds=model.build_seconds,
                         kernel_bytes=model.kernels.nbytes,value_bytes=model.value.nbytes,
                         error=model.error))
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs'/'kernel_certificate.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows,indent=2))

if __name__=='__main__': main()
