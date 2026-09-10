"""Target-interface implementation of the accepted RES-003 known-D diagnostic.

Equations, caps, quadrature and action rule are retained from upstream core.py
7873e28e126ea02e03fc6c429ac0b4275e243cfb and simulate.py ee55c6bf... .
This readable adapter is NOT described as byte-identical upstream source.
It is compared against the pinned production certificates/traces in tests.
"""
from __future__ import annotations
import math
import numpy as np
from numba import njit
from model import moments


def poisson_tail(k,mu):
    mu=np.asarray(mu,dtype=float); term=np.exp(-mu)
    for j in range(1,k+1): term=term*mu/j
    out=term.copy()
    for j in range(k+1,k+128): term=term*mu/j;out+=term
    return out


def capped(mu,cap):
    mu=np.atleast_1d(mu);out=np.empty((len(mu),cap+1));out[:,0]=np.exp(-mu)
    for k in range(1,cap): out[:,k]=out[:,k-1]*mu/k
    out[:,cap]=poisson_tail(cap,mu)
    return out


def positive_exp(Q,h):
    d=len(Q);rate=-Q.diagonal().min()
    if h==0:return np.eye(d)
    n=max(0,int(math.ceil(math.log2(rate*h))));mu=rate*h/2**n
    B=np.maximum(np.eye(d)+Q/rate,0);weight=math.exp(-mu);term=np.eye(d);E=weight*term
    for k in range(1,33):term=term@B;weight*=mu/k;E+=weight*term
    for _ in range(n):E=E@E
    E=np.maximum(E,0);E/=E.sum(axis=1)[:,None]
    return E


def build_known(cfg,D):
    W=cfg['memory']['words'];P=cfg['memory']['pass_seconds'];H=cfg['horizon_seconds']
    lo=cfg['environment']['b_low'];hi=cfg['environment']['b_high'];rate=np.array([lo,hi]);a=1/D
    periods=np.array(cfg['periods_seconds'],float);ticks=np.rint(periods/.1).astype(np.int64)
    C=32;K=12;S=26;nu=P/D
    scan=np.zeros((2,C+1,2,K+1));shift=.5/W
    F=lambda u:np.maximum(np.asarray(u)-shift,0.)**2/2
    F1=float(F(1));u=(np.arange(512)+.5)/512
    v=(np.arange(128)+.5)/128;x,y=np.meshgrid(v,v,indexing='ij');x=x.ravel();y=y.ravel();e=x+(1-x)*y
    def add(z,zz,weight,pend,total):
        pc=capped(np.maximum(total-pend,0),C);pk=capped(np.maximum(pend,0),K)
        scan[z,:,zz,:]+=(pc*np.broadcast_to(weight,len(pc))[:,None]).T@pk
    p0=math.exp(-nu);p1=p0*nu;p2=p1*nu/2
    for z in range(2):
        b0,b1=rate[z],rate[1-z]
        add(z,z,p0,np.array([b0*P*F1]),np.array([b0*P]))
        add(z,1-z,p1/512,P*(b0*F(u)+b1*(F1-F(u))),P*(b0*u+b1*(1-u)))
        add(z,z,p2*2*(1-x)/128**2,P*(b0*F1+(b1-b0)*(F(e)-F(x))),P*(b0+(b1-b0)*(e-x)))
        scan[z,0,z,0]+=float(poisson_tail(3,nu))
    scan/=scan.sum(axis=(1,2,3))[:,None,None,None]
    kernels=[]
    for tau in periods:
        Q=np.zeros((66,66))
        for c in range(33):
            for z in range(2):
                i=2*c+z;Q[i,2*c+1-z]+=a;Q[i,i]-=a
                if c<32:Q[i,2*(c+1)+z]+=rate[z];Q[i,i]-=rate[z]
        idle=positive_exp(Q,tau-P)[:2].reshape(2,33,2)
        base=np.zeros((33,2,2,13))
        for i in range(33):
            for j in range(33):base[min(32,i+j)]+=np.einsum('ab,bck->ack',idle[:,i,:],scan[:,j,:,:])
        kk=np.zeros((33,S,S))
        for z in range(2):
            for k in range(13):
                for y0 in range(33):kk[min(32,k+y0),z*13+k]+=base[y0,z].reshape(-1)
        kernels.append(kk)
    kernels=np.array(kernels);trans=kernels.sum(axis=1)
    T=np.empty((12,2,2));J=np.empty_like(T);reward=np.zeros((12,4))
    for ai,tau in enumerate(periods):
        f,s=moments(tau,a,lo,hi);reward[ai,:2]=s/(2*W);reward[ai,2:]=f/W
        for z in range(2):
            for zz in range(2):
                row=trans[ai,z*13,zz*13:(zz+1)*13];T[ai,z,zz]=row.sum();J[ai,z,zz]=row@np.arange(13)
    V=_values(int(round(H/.1)),a,lo,hi,W,T,J,reward)
    # Identical original approximation ledger, including K>12 and its reserve.
    vv=(hi-lo)*P
    delta=int(H/min(periods))*(float(poisson_tail(3,nu))+
       p1*(4*vv+4*vv*vv)/(24*512**2)+p2*(40*vv+40*vv*vv)/(24*128**2)+
       P*(hi+nu*(hi-lo))/(4*W*W)+float(poisson_tail(13,hi*P/2)))+.0002
    slack=.1-delta-.5*(V[-1,0]+V[-1,1]);q=np.zeros(26);q[0]=q[13]=.5
    if slack<0:raise ValueError('Known-D backup not feasible')
    return kernels,T,J,reward,V,q,slack,delta


@njit(cache=True)
def _values(total,a,lo,hi,W,T,J,r):
    V=np.zeros((total+1,4))
    for rem in range(1,total+1):
        if rem<10:
            f,s=moments(rem*.1,a,lo,hi);V[rem,:2]=s/(2*W);V[rem,2:]=f/W
        else:
            V[rem,2:]=r[2,2:]
            for z in range(2):
                V[rem,z]=r[2,z]
                for zz in range(2):V[rem,z]+=T[2,z,zz]*V[rem-10,zz]+J[2,z,zz]*V[rem-10,zz+2]
    return V


@njit(cache=True)
def known_choose(q,slack,rem,T,J,r,V,ticks,W,D,lo,hi):
    p0=0.;p1=0.;k0=0.;k1=0.
    for k in range(13):p0+=q[k];p1+=q[13+k];k0+=k*q[k];k1+=k*q[13+k]
    val=p0*V[rem,0]+p1*V[rem,1]+k0*V[rem,2]+k1*V[rem,3]
    for a in range(len(ticks)-1,-1,-1):
        dt=min(rem,ticks[a]);nr=rem-dt
        if ticks[a]>rem:
            f,s=moments(.1*dt,1/D,lo,hi);cost=(k0*f[0]+k1*f[1]+.5*(p0*s[0]+p1*s[1]))/W
        else:
            cost=p0*r[a,0]+p1*r[a,1]+k0*r[a,2]+k1*r[a,3]
            for z in range(2):
                pp=p0 if z==0 else p1
                for zz in range(2):cost+=pp*(T[a,z,zz]*V[nr,zz]+J[a,z,zz]*V[nr,zz+2])
        delta=cost-val
        if delta<=slack*dt/rem+1e-13:return a,max(0.,slack-delta)
    raise ValueError('Known-D backup lost')


@njit(cache=True)
def known_observe(q,a,count,K):
    out=np.zeros(26);y=min(count,32)
    for i in range(26):
        for j in range(26):out[j]+=q[i]*K[a,y,i,j]
    return out/out.sum()
