"""Own-count HMM and uniform-in-D risk controller.

For each fixed generator retain four probabilities on (Z, K==0) and two
pending-arrival first moments. Only zero/positive OWN correction counts are
used. This is an auxiliary law, not the physical posterior given survival.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import math
import time
import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parent


def load_config():
    return json.loads((ROOT/'config.json').read_text())


def rate_grid(cfg):
    if cfg['controller']['grid_intervals'] != 32:
        raise ValueError('Production continuum witness is pinned to 32 cells')
    return (32.0 + 9.0*np.arange(33))**2/(3000.0*32**2)


@njit(cache=True)
def moments(h, a, low, high):
    if h == 0.0:
        return np.zeros(2), np.zeros(2)
    k=2*a; x=k*h; mean=(low+high)/2; d=(high-low)/2
    A=-math.expm1(-x)/k
    if x < .2:
        term=.5; B=term
        for j in range(1,24):
            term *= -x/(j+2); B += term
        B *= h*h
    else:
        B=(h-A)/k
    base=mean*mean*h*h+2*d*d*B
    return (np.array([max(0.,mean*h-d*A),mean*h+d*A]),
            np.array([max(0.,base-2*mean*d*h*A),base+2*mean*d*h*A]))


def tail3(nu):
    term=math.exp(-nu)*nu**3/6; total=term
    for j in range(4,80):
        term*=nu/j; total+=term
    return total


def scan_basis(cfg):
    """Six nonnegative functionals, conditional on 0/1/2 switches in a pass.

    Functionals: C0K0,C0K+,C+K0,C+K+,C0*K,C+*K. No pending-count cap.
    Conditional quadrature is independent of the generator rate.
    """
    p=cfg['memory']['pass_seconds']; w=cfg['memory']['words']; cc=cfg['controller']
    rates=[cfg['environment']['b_low'],cfg['environment']['b_high']]
    shift=.5/w
    F=lambda x: np.maximum(np.asarray(x)-shift,0.)**2/2
    def functional(mc,mk):
        ec=np.exp(-mc); ek=np.exp(-mk)
        pc=-np.expm1(-mc); pk=-np.expm1(-mk)
        return np.array([ec*ek,ec*pk,pc*ek,pc*pk,ec*mk,pc*mk]).T
    n1=cc['one_switch_midpoints']; u=(np.arange(n1)+.5)/n1
    n2=cc['two_switch_midpoints']; v=(np.arange(n2)+.5)/n2
    x,y=np.meshgrid(v,v,indexing='ij'); x=x.ravel(); y=y.ravel(); e=x+(1-x)*y
    basis=np.zeros((3,2,6)); F1=float(F(1.))
    for z in range(2):
        b0,b1=rates[z],rates[1-z]
        mk=np.array([p*b0*F1]); mc=np.array([p*b0])-mk
        basis[0,z]=functional(mc,mk)[0]
        mk=p*(b0*F(u)+b1*(F1-F(u)))
        mc=p*(b0*u+b1*(1-u))-mk
        basis[1,z]=functional(mc,mk).mean(axis=0)
        # Sum nonnegative segment contributions, avoiding differences of rates.
        mk=p*(b0*F(x)+b1*(F(e)-F(x))+b0*(F1-F(e)))
        mc=p*(b0*x+b1*(e-x)+b0*(1-e))-mk
        weights=2*(1-x)/(n2*n2)
        basis[2,z]=weights@functional(mc,mk)
    return basis


def idle_kernel(h, a, low, high):
    """Positive uniformization on (arrival zero/positive, Z), 64 terms."""
    if h < -1e-12: raise ValueError('pass longer than action')
    if h <= 0: return np.eye(4)[:2].reshape(2,2,2)
    # Extended precision removes dyadic-power amplification of rounded ratios.
    # The exported binary64 coefficients are independently enclosed in Decimal.
    h=np.longdouble(str(h)); a=np.longdouble(str(a))
    low=np.longdouble(str(low)); high=np.longdouble(str(high))
    rate=high+a; squarings=max(0,int(math.ceil(math.log2(rate*h))))
    mu=rate*h/(2**squarings)
    B=np.zeros((4,4),dtype=np.longdouble)
    for c in range(2):
        for z,b in enumerate((low,high)):
            r=2*c+z; B[r,2*c+1-z]=a/rate
            if c==0:
                B[r,2+z]=b/rate; B[r,r]=(high-b)/rate
            else: B[r,r]=high/rate
    weight=np.exp(-mu); term=np.eye(4,dtype=np.longdouble); out=weight*term
    for j in range(1,65):
        term=term@B; weight*=mu/j; out+=weight*term
    for _ in range(squarings): out=out@out
    out/=out.sum(axis=1)[:,None]
    return np.asarray(out[:2].reshape(2,2,2),dtype=float)


def kernels_for_rate(cfg, a, basis):
    p=cfg['memory']['pass_seconds']; nu=a*p
    weights=np.array([math.exp(-nu),math.exp(-nu)*nu,math.exp(-nu)*nu*nu/2])
    scan=np.zeros((2,2,6))  # start,end,functional
    for n in range(3):
        for z in range(2): scan[z,z^(n%2)]+=weights[n]*basis[n,z]
    for z in range(2): scan[z,z,0]+=tail3(nu)
    if cfg['memory']['words']<=16:
        from small_reference import exact_aux_scan
        scan=exact_aux_scan(cfg,a)
    out=[]
    for h in cfg['periods_seconds']:
        idle=idle_kernel(h-p,a,cfg['environment']['b_low'],cfg['environment']['b_high'])
        born=np.zeros((2,2,6)) # birth-observation,start,destination statistics
        for z in range(2):
            for mid in range(2):
                for zz in range(2):
                    f=scan[mid,zz]; i0=idle[z,0,mid]; i1=idle[z,1,mid]
                    born[0,z,zz]+=i0*f[0]; born[0,z,2+zz]+=i0*f[1]
                    born[0,z,4+zz]+=i0*f[4]
                    born[1,z,zz]+=i0*f[2]+i1*(f[0]+f[2])
                    born[1,z,2+zz]+=i0*f[3]+i1*(f[1]+f[3])
                    born[1,z,4+zz]+=i0*f[5]+i1*(f[4]+f[5])
        K=np.zeros((2,4,6)); K[:,:2,:]=born
        K[1,2:,:]=born.sum(axis=0) # any old pending arrival forces positive C
        # Exact row normalization is charged to the arithmetic ledger.
        for i in range(4): K[:,i,:]/=K[:,i,:4].sum()
        out.append(K)
    return np.array(out)


def model_error(cfg,a):
    cc=cfg['controller']; p=cfg['memory']['pass_seconds']; w=cfg['memory']['words']
    hi=cfg['environment']['b_high']; lo=cfg['environment']['b_low']; nu=a*p; v=(hi-lo)*p
    p1=math.exp(-nu)*nu; p2=p1*nu/2
    terms=dict(omitted_switches=tail3(nu),
               midpoint_one=p1*(4*v+4*v*v)/(24*cc['one_switch_midpoints']**2),
               midpoint_two=p2*(40*v+40*v*v)/(24*cc['two_switch_midpoints']**2),
               finite_word_smoothing=p*(hi+nu*(hi-lo))/(4*w*w))
    N=int(cfg['horizon_seconds']/min(cfg['periods_seconds']))
    if w<=16:terms={k:0.0 for k in terms}
    return N*sum(terms.values()),terms


def arithmetic_ledger(cfg):
    u=2.**-53; g=lambda n:n*u/(1-n*u); cc=cfg['controller']
    N=int(cfg['horizon_seconds']/min(cfg['periods_seconds'])); H=cfg['horizon_seconds']
    W=cfg['memory']['words']; hi=cfg['environment']['b_high']; P=cfg['memory']['pass_seconds']
    tb=cc['backup_period_seconds']; Nb=int(math.ceil(H/tb)); kap=cc['kernel_relative_error_contract']
    mu=hi*P/2
    Vmax=(H+tb)*(mu*hi+hi*hi*tb/2)/W
    Rsum=H*(mu*hi+hi*hi*max(cfg['periods_seconds'])/2)/W
    eta=math.expm1(4*N*(kap+g(128)))
    etaV=8*(g(512*Nb)+Nb*kap)*Vmax
    terms=dict(filtering=(2*N*Vmax+Rsum)*eta,
               value_recursion=2*N*etaV,
               action_arithmetic=N*g(4096)*(4*Vmax+2*Rsum)+N*1e-13,
               positive_kernel=N*8*kap,
               slack_accumulation=g(2*N)*(cfg['epsilon']+Rsum+2*N*Vmax),
               slack_comparisons=N*g(32)*(cfg['epsilon']+Rsum+2*N*Vmax),
               absolute_reward=N*g(1024)*hi*hi*max(cfg['periods_seconds'])**2/W,
               underflow=1e-100)
    # Logs have bounded arguments because every permitted row has positive support.
    log_error=4*N*(kap+g(128))+2*g(4*N+256)*N*80
    return dict(terms=terms,total=sum(terms.values()),reserve=cc['numerical_allowance'],
                kernel_relative_contract=kap,filter_relative_bound=eta,
                test_log_error=log_error,test_log_margin=cc['test_log_margin'],
                covered=sum(terms.values())<cc['numerical_allowance'],
                elementary_function_ulp_contract=4)


@njit(cache=True)
def build_values(rates, periods, ticks, kernels, total, tick, backup, low, high, words):
    M=len(rates); A=len(periods)
    reward=np.zeros((M,A,4)); T=np.zeros((M,A,2,2)); J=np.zeros_like(T)
    for j in range(M):
        for a in range(A):
            m1,m2=moments(periods[a],rates[j],low,high)
            reward[j,a,:2]=m2/(2*words); reward[j,a,2:]=m1/words
            for z in range(2):
                for zz in range(2):
                    for y in range(2):
                        T[j,a,z,zz]+=kernels[j,a,y,z,zz]+kernels[j,a,y,z,2+zz]
                        J[j,a,z,zz]+=kernels[j,a,y,z,4+zz]
    V=np.zeros((M,total+1,4)); nb=ticks[backup]
    for j in range(M):
        for r in range(1,total+1):
            if r<nb:
                m1,m2=moments(r*tick,rates[j],low,high)
                V[j,r,:2]=m2/(2*words); V[j,r,2:]=m1/words
            else:
                V[j,r,2:]=reward[j,backup,2:]
                for z in range(2):
                    v=reward[j,backup,z]
                    for zz in range(2):
                        v+=T[j,backup,z,zz]*V[j,r-nb,zz]+J[j,backup,z,zz]*V[j,r-nb,2+zz]
                    V[j,r,z]=v
    return reward,T,J,V


@dataclass
class Bank:
    cfg: dict
    rates: np.ndarray
    kernels: np.ndarray
    reward: np.ndarray
    transition: np.ndarray
    pending: np.ndarray
    value: np.ndarray
    slack: np.ndarray
    model_delta: np.ndarray
    periods: np.ndarray
    ticks: np.ndarray
    build_seconds: float
    arithmetic: dict

    @property
    def initial(self):
        q=np.zeros((len(self.rates),6)); q[:,:2]=.5; return q


def build_bank(cfg=None,rates=None):
    cfg=cfg or load_config(); start=time.perf_counter()
    rates=rate_grid(cfg) if rates is None else np.asarray(rates,float)
    basis=scan_basis(cfg); K=np.array([kernels_for_rate(cfg,a,basis) for a in rates])
    periods=np.array(cfg['periods_seconds'],float); tick=cfg['controller']['time_tick_seconds']
    ticks=np.rint(periods/tick).astype(np.int64); total=int(round(cfg['horizon_seconds']/tick))
    backup=int(np.flatnonzero(periods==cfg['controller']['backup_period_seconds'])[0])
    r,T,J,V=build_values(rates,periods,ticks,K,total,tick,backup,
                        cfg['environment']['b_low'],cfg['environment']['b_high'],cfg['memory']['words'])
    deltas=np.array([model_error(cfg,a)[0] for a in rates]); cc=cfg['controller']
    threshold=cfg['epsilon']/cc['continuous_transfer_factor']
    beta=cc['beta']/cc['continuous_transfer_factor']
    slack=threshold-beta-deltas-cc['numerical_allowance']-.5*(V[:,-1,0]+V[:,-1,1])
    ledger=arithmetic_ledger(cfg)
    if not ledger['covered']: raise ArithmeticError(f'Arithmetic reserve not covered: {ledger}')
    if min(slack)<0: raise ValueError('Common initial backup is not certified')
    return Bank(cfg,rates,K,r,T,J,V,slack,deltas,periods,ticks,time.perf_counter()-start,ledger)


@njit(cache=True)
def retained(rejected):
    m=len(rejected); active=np.zeros(m,np.bool_)
    for j in range(m-1):
        if not (rejected[j] and rejected[j+1]):
            active[j]=True; active[j+1]=True
    return active


@njit(cache=True)
def observe(q,logs,rejected,a,count,kernels,threshold,learn):
    y=0 if count==0 else 1; M=len(q); new=np.zeros_like(q)
    for j in range(M):
        for d in range(6):
            for s in range(4): new[j,d]+=q[j,s]*kernels[j,a,y,s,d]
        lik=new[j,:4].sum()
        if lik<=0: raise ValueError('Nonpositive own-count likelihood')
        new[j]/=lik; logs[j]+=math.log(lik)
    maximum=logs.max(); mix=0.
    for j in range(M):
        logs[j]-=maximum; mix+=math.exp(logs[j])
    logmix=math.log(mix/M)
    if learn:
        for j in range(M):
            if logmix-logs[j]>threshold: rejected[j]=True
    return new


@njit(cache=True)
def action_delta(q,j,a,remaining,reward,T,J,V,ticks,tick,words,rates,low,high):
    p0=q[j,0]+q[j,2]; p1=q[j,1]+q[j,3]; k0=q[j,4]; k1=q[j,5]
    val=p0*V[j,remaining,0]+p1*V[j,remaining,1]+k0*V[j,remaining,2]+k1*V[j,remaining,3]
    dt=min(remaining,ticks[a]); nr=remaining-dt
    if ticks[a]>remaining:
        m1,m2=moments(dt*tick,rates[j],low,high)
        one=(k0*m1[0]+k1*m1[1]+.5*(p0*m2[0]+p1*m2[1]))/words
        return one-val,one,val
    one=p0*reward[j,a,0]+p1*reward[j,a,1]+k0*reward[j,a,2]+k1*reward[j,a,3]
    f0=0.;f1=0.
    for zz in range(2):
        f0+=T[j,a,0,zz]*V[j,nr,zz]+J[j,a,0,zz]*V[j,nr,2+zz]
        f1+=T[j,a,1,zz]*V[j,nr,zz]+J[j,a,1,zz]*V[j,nr,2+zz]
    return one+p0*f0+p1*f1-val,one,val


@njit(cache=True)
def choose(q,slack,active,remaining,reward,T,J,V,ticks,tick,words,rates,low,high,backup):
    # Every retained fixed generator carries ITS OWN slack; D is never switched.
    if not active.any(): return backup,slack.copy(),-1
    chosen=-1; bind=-1
    for a in range(len(ticks)-1,-1,-1):
        dt=min(remaining,ticks[a]); feasible=True
        for j in range(len(q)):
            if active[j]:
                d,_,_=action_delta(q,j,a,remaining,reward,T,J,V,ticks,tick,words,rates,low,high)
                if d>slack[j]*dt/remaining+1e-13:
                    feasible=False;bind=j;break
        if feasible: chosen=a;break
    if chosen<0: raise ValueError('Certified backup lost')
    out=slack.copy()
    for j in range(len(q)):
        if active[j]:
            d,_,_=action_delta(q,j,chosen,remaining,reward,T,J,V,ticks,tick,words,rates,low,high)
            out[j]=max(0.,slack[j]-d)
    return chosen,out,bind


def controller_args(bank):
    cfg=bank.cfg
    return (bank.reward,bank.transition,bank.pending,bank.value,bank.ticks,
            cfg['controller']['time_tick_seconds'],cfg['memory']['words'],bank.rates,
            cfg['environment']['b_low'],cfg['environment']['b_high'],
            int(np.flatnonzero(bank.periods==cfg['controller']['backup_period_seconds'])[0]))


def main():
    b=build_bank(); cc=b.cfg['controller']; threshold=b.cfg['epsilon']/cc['continuous_transfer_factor']
    rows=[dict(D=1/float(a),initial_backup=.5*float(b.value[j,-1,0]+b.value[j,-1,1]),
               model_delta=float(b.model_delta[j]),initial_slack=float(b.slack[j]),
               grid_risk_limit=threshold) for j,a in enumerate(b.rates)]
    out=dict(rows=rows,arithmetic=b.arithmetic,build_seconds=b.build_seconds,
             kernel_bytes=b.kernels.nbytes,value_bytes=b.value.nbytes,
             max_row_error=float(np.max(abs(b.kernels[:,:,:,:,:4].sum(axis=(2,4))-1))))
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs'/'reserve_certificate.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
    print('backup range',min(r['initial_backup'] for r in rows),max(r['initial_backup'] for r in rows))
    print('minimum slack',b.slack.min())

if __name__=='__main__': main()
