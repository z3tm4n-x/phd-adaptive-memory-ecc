"""Directed-decimal enclosures of every production observation coefficient.

This encloses the finite quadrature law and the exact idle CTMC. Analytic TV
bounds separately pay for quadrature versus the physical CTMC. Decimal exp is
correctly rounded; adjacent decimal values enclose it. Residuals are not proof.
"""
from decimal import Decimal,Context,ROUND_FLOOR,ROUND_CEILING,ROUND_HALF_EVEN
import csv,json,time,math
import numpy as np
import model
DOWN=Context(prec=60,rounding=ROUND_FLOOR)
UP=Context(prec=60,rounding=ROUND_CEILING)
NEAR=Context(prec=60,rounding=ROUND_HALF_EVEN)
class I:
    __slots__=('lo','hi')
    def __init__(self,x=0,hi=None):
        if isinstance(x,I):self.lo=x.lo;self.hi=x.hi;return
        self.lo=x if isinstance(x,Decimal) else Decimal(str(x));self.hi=self.lo if hi is None else hi
    def __add__(self,b):
        b=I(b);return I(DOWN.add(self.lo,b.lo),UP.add(self.hi,b.hi))
    __radd__=__add__
    def __neg__(self):return I(self.hi.copy_negate(),self.lo.copy_negate())
    def __sub__(self,b):return self+(-I(b))
    def __rsub__(self,b):return I(b)+(-self)
    def __mul__(self,b):
        b=I(b)
        if self.lo>=0 and b.lo>=0:return I(DOWN.multiply(self.lo,b.lo),UP.multiply(self.hi,b.hi))
        p=[DOWN.multiply(x,y) for x in (self.lo,self.hi) for y in (b.lo,b.hi)]
        q=[UP.multiply(x,y) for x in (self.lo,self.hi) for y in (b.lo,b.hi)]
        return I(min(p),max(q))
    __rmul__=__mul__
    def __truediv__(self,b):
        b=I(b)
        if b.lo<=0<=b.hi:raise ZeroDivisionError('interval contains zero')
        return self*I(DOWN.divide(Decimal(1),b.hi),UP.divide(Decimal(1),b.lo))
    def __rtruediv__(self,b):return I(b)/self
    def exp(self):return I(DOWN.next_minus(NEAR.exp(self.lo)),UP.next_plus(NEAR.exp(self.hi)))
    def positive(self):
        if self.hi<0:raise ArithmeticError('strictly negative interval')
        return I(max(Decimal(0),self.lo),max(Decimal(0),self.hi))
    def square(self):return self*self

def zeros(shape):
    out=np.empty(shape,object)
    for idx in np.ndindex(shape):out[idx]=I(0)
    return out

def eye(n):
    out=zeros((n,n))
    for i in range(n):out[i,i]=I(1)
    return out

def mm(a,b):
    out=zeros((a.shape[0],b.shape[1]))
    for i in range(a.shape[0]):
        for k in range(a.shape[1]):
            if a[i,k].hi==0:continue
            for j in range(b.shape[1]):
                if b[k,j].hi:out[i,j]=out[i,j]+a[i,k]*b[k,j]
    return out

def scale(a,c):
    out=zeros(a.shape)
    for idx in np.ndindex(a.shape):out[idx]=a[idx]*c
    return out

def plus(a,b):
    out=zeros(a.shape)
    for idx in np.ndindex(a.shape):out[idx]=a[idx]+b[idx]
    return out

def interval_idle(duration,a,lo,hi):
    rate=hi+a
    s=max(0,int(math.ceil(math.log2(float(rate.hi*duration.hi)))))
    mu=rate*duration/(2**s)
    if not 0<mu.lo<=mu.hi<=1:raise ArithmeticError('invalid uniformization scaling')
    B=zeros((4,4))
    for cat in range(2):
        for z,b in enumerate((lo,hi)):
            i=z+2*cat;B[i,1-z+2*cat]=a/rate
            if cat==0:B[i,z+2]=b/rate;B[i,i]=(hi-b)/rate
            else:B[i,i]=hi/rate
    term=eye(4);weight=(-mu).exp();E=scale(term,weight)
    for n in range(1,65):
        term=mm(term,B);weight=weight*mu/n;E=plus(E,scale(term,weight))
    tail=weight*mu/65/(1-mu/66)
    for idx in np.ndindex(E.shape):E[idx]=I(E[idx].lo,UP.add(E[idx].hi,tail.hi))
    for _ in range(s):E=mm(E,E)
    return E[:2].reshape(2,2,2)

def interval_basis(cfg):
    P=I(cfg['memory']['pass_seconds']);w=cfg['memory']['words'];low=I(cfg['environment']['b_low']);high=I(cfg['environment']['b_high']);shift=I(1)/(2*w)
    n1=cfg['controller']['one_switch_midpoints'];n2=cfg['controller']['two_switch_midpoints']
    def F(x):return (x-shift).positive().square()/2
    f1=F(I(1));basis=zeros((2,3,6))
    for z in range(2):
        b0,b1=(low,high) if z==0 else (high,low)
        for order in range(3):
            nodes=1 if order==0 else n1 if order==1 else n2*n2
            for ix in range(nodes):
                if order==0:
                    pend=P*b0*f1;total=P*b0;weight=I(1)
                elif order==1:
                    u=I(2*ix+1)/(2*n1);pend=P*(b0*F(u)+b1*(f1-F(u)))
                    total=P*(b0*u+b1*(1-u));weight=I(1)/n1
                else:
                    x=I(2*(ix//n2)+1)/(2*n2);y=I(2*(ix%n2)+1)/(2*n2);end=x+(1-x)*y
                    pend=P*(b0*F(x)+b1*(F(end)-F(x))+b0*(f1-F(end)))
                    total=P*(b0*x+b1*(end-x)+b0*(1-end));weight=2*(1-x)/(n2*n2)
                obs=total-pend
                if obs.lo<0 or pend.lo<0:raise ArithmeticError('Poisson mean enclosure crossed zero')
                ec=(-obs).exp();ek=(-pend).exp();pc=1-ec;pk=1-ek
                terms=(ec*ek,ec*pk,pc*ek,pc*pk,pend*ec,pend*pc)
                for k in range(6):basis[z,order,k]=basis[z,order,k]+weight*terms[k]
            print('interval scan basis',z,order,flush=True)
    return basis

def interval_scan(cfg,a,basis):
    nu=I(cfg['memory']['pass_seconds'])*a;p0=(-nu).exp();p1=p0*nu;p2=p1*nu/2
    weights=(p0,p1,p2);tail=1-p0-p1-p2
    if tail.lo<0:raise ArithmeticError('unresolved omitted switching mass')
    out=zeros((2,2,6))
    for z in range(2):
        for n in range(3):
            for k in range(6):out[z,z^(n%2),k]=out[z,z^(n%2),k]+weights[n]*basis[z,n,k]
        out[z,z,0]=out[z,z,0]+tail
    return out

def interval_combine(idle,scan):
    birth=zeros((2,2,6))
    for c0 in range(2):
        for c1 in range(2):
            y=min(1,c0+c1)
            for z in range(2):
                for mid in range(2):
                    for zz in range(2):
                        wt=idle[z,c0,mid]
                        for dest,src in ((zz,2*c1),(2+zz,2*c1+1),(4+zz,4+c1)):
                            birth[y,z,dest]=birth[y,z,dest]+wt*scan[mid,zz,src]
    out=zeros((2,4,6));out[:,:2]=birth
    for z in range(2):
        for k in range(6):out[1,z+2,k]=birth[0,z,k]+birth[1,z,k]
    return out

def continuum(cfg):
    rows=[];greatest=Decimal(0);G=I(cfg['controller']['continuous_transfer_factor'])
    for j in range(32):
        l=I((32+9*j)**2)/(3000*32**2);u=I((32+9*(j+1))**2)/(3000*32**2)
        exponent=cfg['horizon_seconds']*(u-l).square()/(8*l);fac=exponent.exp()
        if fac.hi>=G.lo:raise ArithmeticError('continuum gap exceeds declared transfer factor')
        greatest=max(greatest,fac.hi)
        rows.append(dict(cell=j,rate_low=str(l.lo),rate_high=str(u.hi),factor_lower=str(fac.lo),factor_upper=str(fac.hi),declared_factor=str(G.lo)))
    return rows,str(greatest)

def run():
    start=time.perf_counter();cfg=model.config();bank=model.build(cfg);basis=interval_basis(cfg)
    lo=I(cfg['environment']['b_low']);hi=I(cfg['environment']['b_high']);P=I(cfg['memory']['pass_seconds'])
    cap=Decimal(str(cfg['controller']['kernel_relative_error_contract']));rows=[];global_max=Decimal(0);positive_min=float('inf');structural=0
    for j in range(33):
        a=I((32+9*j)**2)/(3000*32**2);scan=interval_scan(cfg,a,basis)
        for action,h in enumerate(cfg['periods_seconds']):
            exact=interval_combine(interval_idle(I(h)-P,a,lo,hi),scan);relmax=Decimal(0)
            for idx in np.ndindex(exact.shape):
                v=Decimal.from_float(float(bank.kernels[(j,action)+idx]));en=exact[idx]
                if en.hi==0:
                    structural+=1
                    if v!=0:raise ArithmeticError('structural zero changed')
                    continue
                if en.lo<=0:raise ArithmeticError('coefficient positivity not resolved')
                err=UP.divide(max(UP.subtract(v,en.lo),UP.subtract(en.hi,v)),en.lo)
                relmax=max(relmax,err);positive_min=min(positive_min,float(v))
                if err>cap:raise ArithmeticError(f'coefficient contract failed at {(j,action)+idx}: {err}')
            global_max=max(global_max,relmax)
            rows.append(dict(node=j,dwell=1/bank.rates[j],period=h,max_relative_error_upper=str(relmax),contract=str(cap)))
        print('all interval coefficients checked at node',j,flush=True)
    continuum_rows,maxfactor=continuum(cfg);out=model.ROOT/'outputs';out.mkdir(exist_ok=True)
    for name,data in [('coefficient_witnesses.csv',rows),('continuum_witnesses.csv',continuum_rows)]:
        with (out/name).open('w',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=list(data[0]));wr.writeheader();wr.writerows(data)
    report=dict(status='DETERMINISTIC_ENCLOSURES_COMPLETED',decimal_digits=60,positive_coefficient_relative_error_upper=str(global_max),
                required_relative_contract=str(cap),minimum_positive_coefficient=positive_min,structural_zeros=structural,
                coefficient_count=int(bank.kernels.size),maximum_continuum_factor_upper=maxfactor,declared_continuum_factor=cfg['controller']['continuous_transfer_factor'],
                arithmetic=model.arithmetic_ledger(cfg),seconds=time.perf_counter()-start)
    (out/'numerical_certificate.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
    return report
if __name__=='__main__':run()
