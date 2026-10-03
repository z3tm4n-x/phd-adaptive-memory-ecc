"""Independent Decimal90 equations; selected finite interval E1 checks."""
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from functools import lru_cache
from types import SimpleNamespace
import json

import engine as e
from t80_joint_validate import validate as monitor_check


def dec(x):
    x=F(x)
    return D(x.numerator)/D(x.denominator)


def primitive(x,t):
    l=D('.001');rho=D('.048')
    if x<=l:
        v=min(t,x/(rho*l))
        return x*v-rho*l*v*v/2
    te=(x/l).ln()/rho;v1=min(t,te);v2=min(max(D(0),t-te),1/rho)
    return x/rho*(1-(-rho*v1).exp())+l*(v2-rho*v2*v2/2)


@lru_cache(maxsize=4096)
def e1_check(shield,g,ka,h,Q,u,v):
    p=e.calendar(e.context(shield,'ERR-only'),g)
    r0=(2*ka*p['Ps']+p['dE']+p['Gp']+p['f'])
    r1=F(h)+ka*p['Ps']+p['Gp']+p['f']
    assert r1>r0
    with localcontext() as ctx:
        ctx.prec=90
        a=dec(F(p['W']-1,p['W']));b=dec(p['b']);uu=dec(u);vv=dec(v)
        xs=sorted(set([F(0),p['b'],F('.001'),p['B']]+[p['B']*i/1024 for i in range(1,1024)]))
        todo=list(zip(xs[:-1],xs[1:]));checked=0;minimum=None
        while todo:
            lo,hi=todo.pop();xl,xh=dec(lo),dec(hi)
            mass=max(D(0),primitive(xl,dec(r1))-primitive(xl,dec(r0)))
            lhs=xh*xh*(-a*mass).exp();rhs=uu+vv*max(D(0),xl-b)
            gap=rhs-lhs
            if gap < -D('1e-75'):
                if hi-lo <= p['B']/65536:
                    raise AssertionError(('independent E1 failure',shield,g,ka,h,lo,hi,str(gap)))
                mid=(lo+hi)/2;todo.extend(((lo,mid),(mid,hi)))
            else:
                checked+=1;minimum=gap if minimum is None else min(minimum,gap)
        q=min(dec(p['S2']),uu*dec(p['T'])+vv*dec(p['FS']))
        assert abs(q-dec(Q))<D('1e-70')
    return checked


def verify(selected):
    counts=dict(monitor_risk_LOW_price_resource=0,ERR_equations=0,ERR_E1_cells=0)
    seen=set()
    with localcontext() as ctx:
        ctx.prec=90
        for row in selected:
            p=e.calendar(e.context(row['shield'],row['mode']),row['g'])
            p['Dstar']=row['Dstar']
            assert row['risk_upper']<=p['eps'] and row['resource_pass']
            if row['mode']!='ERR-only':
                m=e.window(p)
                r=dict(set_representative=p['set'],architecture=p['architecture'],margin=p['margin'],
                       kind='total_load',qratio=F(2),divisor=2,aM=F(10**6),wm=m['wm'],wp=m['wp'],
                       Delta_m=m['Delta_m'],hF_max=m['hF_max'],id=len(seen),**row)
                check=monitor_check(SimpleNamespace(records=[r]),[p])
                counts['monitor_risk_LOW_price_resource']+=check['points']
            else:
                Ps=dec(p['Ps']);Pl=row['ka']*Ps;T=dec(p['T']);b=dec(p['b']);B=dec(p['B'])
                Q=dec(row['Q']);beta=D(1)/(2*p['W']);cf=dec(p['cp'])/dec(p['gm'])
                err=dec(e.old.errors(p['q'],'ERR-only'));direct=dec(row['Dstar'])
                risk=err+direct+p['K']*B*Ps/p['W']+beta*min(Pl*dec(p['S2']),Ps*dec(p['S2'])+Pl*Q)
                assert abs(risk-dec(row['risk_upper']))<D('1e-75')
                E=dec(row['DE']);flags=E*(b+dec(p['rF'])+dec(p['rloss']))
                pq=min(D(1),err+direct+p['K']*b*Ps/p['W']+beta*Pl*b*b*T)
                x=(2*dec(p['cp'])+dec(p['sigmaX']))/T+dec(p['CX'])
                quiet=min(cf+x,cf/row['ka']+cf*min(D(1),E*(1+p['K'])/T+flags+pq)+x)
                TQ=D('.9')*T
                boundary=E*(1000+p['K']+1000*B*(Pl+dec(p['dE'])))/TQ
                xq=(2*dec(p['cp'])+dec(p['sigmaX']))*1000/TQ+dec(p['CX'])
                returning=min(cf+xq,cf/row['ka']+cf*min(D(1),boundary+flags+risk)+xq)
                for value,key in ((quiet,'quiet_upper'),(returning,'returns_upper')):
                    assert abs(value-dec(row[key]))<D('1e-70')
                counts['ERR_equations']+=3
                key=(row['shield'],row['g'],row['ka'],row['h'],row['Q'],row['u'],row['v'])
                if key not in seen and row['u'] is not None:
                    counts['ERR_E1_cells']+=e1_check(*key)
                    seen.add(key)
            if row['purpose']=='cost_threshold':assert row['objective']<=e.LIMIT
    return dict(precision=90,counts=counts,selected_rows=len(selected),
                independent_ERR_majorants=len(seen),success=True,
                comparison_tolerance_risk='1e-75',comparison_tolerance_price='1e-70',
                note='certificates use exact rational / outward T82 intervals; Decimal90 is a separate confirmation')
