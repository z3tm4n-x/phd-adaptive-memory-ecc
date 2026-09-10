"""Directed Decimal enclosures of EVERY stored production HMM coefficient.

The target is the finite positive quadrature law, not the exact physical scan.
Physical/quadrature approximation is a separate coupling ledger. Decimal exp
is correctly rounded; one outward adjacent Decimal on each endpoint encloses it.
No mesh-agreement or observed row residual is used as a rounding proof.
"""
from __future__ import annotations
from decimal import Decimal as D, Context, ROUND_FLOOR, ROUND_CEILING, getcontext
from fractions import Fraction
import json,time
import numpy as np
from model import load_config,scan_basis,kernels_for_rate,rate_grid,ROOT

getcontext().prec=90
LC=Context(prec=55,rounding=ROUND_FLOOR);UC=Context(prec=55,rounding=ROUND_CEILING)
class I:
    __slots__=('l','u')
    def __init__(self,l=0,u=None):
        self.l=l if isinstance(l,D) else D(str(l));self.u=self.l if u is None else (u if isinstance(u,D) else D(str(u)))
    def __add__(self,b):
        if not isinstance(b,I):b=I(b)
        return I(LC.add(self.l,b.l),UC.add(self.u,b.u))
    __radd__=__add__
    def __neg__(self):return I(-self.u,-self.l)
    def __sub__(self,b):return self+-toI(b)
    def __rsub__(self,b):return toI(b)+-self
    def __mul__(self,b):
        b=toI(b)
        if self.l>=0 and b.l>=0:return I(LC.multiply(self.l,b.l),UC.multiply(self.u,b.u))
        lows=[LC.multiply(x,y) for x in (self.l,self.u) for y in (b.l,b.u)]
        ups=[UC.multiply(x,y) for x in (self.l,self.u) for y in (b.l,b.u)]
        return I(min(lows),max(ups))
    __rmul__=__mul__
    def __truediv__(self,b):
        b=toI(b)
        if b.l<=0:raise ArithmeticError('Interval denominator not positive')
        return self*I(LC.divide(D(1),b.u),UC.divide(D(1),b.l))
    def __pow__(self,n):
        v=I(1)
        for _ in range(n):v=v*self
        return v
    def exp(self):
        # Context.exp uses correctly rounded nearest; widening is explicit.
        a=LC.exp(self.l);b=UC.exp(self.u)
        return I(LC.next_minus(a),UC.next_plus(b))
    def center(self):return float((self.l+self.u)/2)

def toI(x):return x if isinstance(x,I) else I(x)
def zeros(shape):
    a=np.empty(shape,object)
    for ix in np.ndindex(shape):a[ix]=I(0)
    return a

def eye(n):
    a=zeros((n,n))
    for i in range(n):a[i,i]=I(1)
    return a

def matmul(a,b):
    out=zeros((a.shape[0],b.shape[1]))
    for i in range(a.shape[0]):
        for k in range(a.shape[1]):
            if a[i,k].u==0:continue
            for j in range(b.shape[1]):
                if b[k,j].u!=0:out[i,j]=out[i,j]+a[i,k]*b[k,j]
    return out

def interval_basis(cfg):
    P=I(cfg['memory']['pass_seconds']);W=cfg['memory']['words'];shift=I(1)/I(2*W)
    rates=[I(cfg['environment']['b_low']),I(cfg['environment']['b_high'])]
    cc=cfg['controller'];out=zeros((3,2,6))
    def F(x):
        if x.u<=shift.l:return I(0)
        if x.l<shift.u:return I(0,(x-shift).u)*(I(0,(x-shift).u))/2
        return (x-shift)**2/2
    def fun(mc,mk):
        ec=(-mc).exp();ek=(-mk).exp();pc=1-ec;pk=1-ek
        return [ec*ek,ec*pk,pc*ek,pc*pk,ec*mk,pc*mk]
    F1=F(I(1))
    for z in range(2):
        b0,b1=rates[z],rates[1-z]
        mk=P*b0*F1;out[0,z]=fun(P*b0-mk,mk)
        m=cc['one_switch_midpoints']
        for j in range(m):
            u=I(2*j+1)/I(2*m);mk=P*(b0*F(u)+b1*(F1-F(u)));mc=P*(b0*u+b1*(1-u))-mk
            f=fun(mc,mk)
            for k in range(6):out[1,z,k]=out[1,z,k]+f[k]/m
        m=cc['two_switch_midpoints']
        for i in range(m):
            x=I(2*i+1)/I(2*m);Fx=F(x)
            for j in range(m):
                y=I(2*j+1)/I(2*m);e=x+(1-x)*y;Fe=F(e)
                mk=P*(b0*Fx+b1*(Fe-Fx)+b0*(F1-Fe));mc=P*(b0*x+b1*(e-x)+b0*(1-e))-mk
                f=fun(mc,mk);weight=2*(1-x)/(m*m)
                for k in range(6):out[2,z,k]=out[2,z,k]+weight*f[k]
    return out

def interval_idle(h,a,lo,hi):
    rate=hi+a;squarings=0
    while (rate*h/I(2**squarings)).u>1:squarings+=1
    mu=rate*h/I(2**squarings);B=zeros((4,4))
    for c in range(2):
        for z,b in enumerate((lo,hi)):
            r=2*c+z;B[r,2*c+1-z]=a/rate
            if c==0:
                B[r,2+z]=b/rate;B[r,r]=(hi-b)/rate if z==0 else I(0)
            else:B[r,r]=hi/rate
    wt=(-mu).exp();term=eye(4);E=term*wt
    for j in range(1,65):term=matmul(term,B);wt=wt*mu/j;E=E+term*wt
    # Uniformization Poisson tail: mu<=1; first omitted wt*mu/65, ratio<=1/66.
    tail=(wt*mu/65)/(1-mu/66)
    for ix in np.ndindex(E.shape):E[ix]=I(E[ix].l,UC.add(E[ix].u,tail.u))
    for _ in range(squarings):E=matmul(E,E)
    return E[:2].reshape(2,2,2)

def interval_kernel(cfg,j,basis):
    a=I((32+9*j)**2)/I(3000*32**2);P=I(cfg['memory']['pass_seconds']);nu=P*a
    p0=(-nu).exp();p1=p0*nu;p2=p1*nu/2
    # Exact omitted mass as positive tail series and a geometric remainder.
    term=p2*nu/3;tail=term
    for k in range(4,65):term=term*nu/k;tail=tail+term
    rest=(term*nu/65)/(1-nu/66);tail=I(tail.l,UC.add(tail.u,rest.u))
    scan=zeros((2,2,6))
    for n,weight in enumerate((p0,p1,p2)):
        for z in range(2):
            for f in range(6):scan[z,z^(n%2),f]=scan[z,z^(n%2),f]+weight*basis[n,z,f]
    for z in range(2):scan[z,z,0]=scan[z,z,0]+tail
    out=[];lo=I(cfg['environment']['b_low']);hi=I(cfg['environment']['b_high'])
    for h in cfg['periods_seconds']:
        idle=interval_idle(I(h)-P,a,lo,hi);born=zeros((2,2,6))
        for z in range(2):
            for mid in range(2):
                for zz in range(2):
                    f=scan[mid,zz];i0=idle[z,0,mid];i1=idle[z,1,mid]
                    born[0,z,zz]=born[0,z,zz]+i0*f[0]
                    born[0,z,2+zz]=born[0,z,2+zz]+i0*f[1]
                    born[0,z,4+zz]=born[0,z,4+zz]+i0*f[4]
                    born[1,z,zz]=born[1,z,zz]+i0*f[2]+i1*(f[0]+f[2])
                    born[1,z,2+zz]=born[1,z,2+zz]+i0*f[3]+i1*(f[1]+f[3])
                    born[1,z,4+zz]=born[1,z,4+zz]+i0*f[5]+i1*(f[4]+f[5])
        K=zeros((2,4,6));K[:,:2,:]=born
        for z in range(2):
            for d in range(6):K[1,2+z,d]=born[0,z,d]+born[1,z,d]
        out.append(K)
    return np.array(out,object)

def continuum(cfg):
    H=I(cfg['horizon_seconds']);bounds=[]
    for j in range(32):
        a=I((32+9*j)**2)/I(3000*32**2);b=I((32+9*(j+1))**2)/I(3000*32**2)
        factor=(H*(b-a)**2/(8*a)).exp()
        bounds.append(str(factor.u))
    upper=max(D(x) for x in bounds);limit=D(str(cfg['controller']['continuous_transfer_factor']))
    assert upper<limit
    return dict(proof='Holder plus linear interpolation error for exp on log-rate; ln(r)<= (r-1)/sqrt(r)',
                max_transfer_upper=str(upper),declared_factor=str(limit),cell_upper_bounds=bounds)

def verify(cfg=None):
    cfg=cfg or load_config();start=time.perf_counter();basis=interval_basis(cfg);fastbasis=scan_basis(cfg)
    maxrel=D(0);minpos=1.;count=0;maxwidth=D(0);rows=[]
    for j,a in enumerate(rate_grid(cfg)):
        exact=interval_kernel(cfg,j,basis);fast=kernels_for_rate(cfg,a,fastbasis);local=D(0)
        for ix in np.ndindex(fast.shape):
            f=D.from_float(float(fast[ix]));v=exact[ix]
            if v.u==0:
                assert f==0;continue
            if v.l<=0:raise ArithmeticError(f'Nonpositive enclosure {j} {ix}: {v.l} {v.u}')
            err=max(abs(f-v.l),abs(f-v.u))/v.l
            local=max(local,err);maxwidth=max(maxwidth,(v.u-v.l)/v.l)
            minpos=min(minpos,float(f));count+=1
        maxrel=max(maxrel,local);rows.append(dict(grid=j,D=1/float(a),max_relative_error=str(local)))
    assert maxrel<D(str(cfg['controller']['kernel_relative_error_contract']))
    result=dict(status='DIRECTED_DECIMAL_COEFFICIENT_ENCLOSURES_COMPLETED',precision=55,
                checked_positive_coefficients=count,max_relative_error=str(maxrel),min_positive_coefficient=minpos,
                max_relative_interval_width=str(maxwidth),contract=cfg['controller']['kernel_relative_error_contract'],
                rows=rows,continuum=continuum(cfg),seconds=time.perf_counter()-start)
    (ROOT/'outputs'/'numeric_witness.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','continuum')},indent=2),flush=True)
    return result

if __name__=='__main__':verify()
