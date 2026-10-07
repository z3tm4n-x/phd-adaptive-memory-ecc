"""Uncertified candidate finder for a fixed two-state storage inequality.

This does NOT prove admission; every successful candidate must be enclosed
over full rectangles by the directed verifier, including Z=0 and q=q0.
"""
import math
import json
from fractions import Fraction as F
import joint as j


def z_lower(q,alpha,rho,h):
    ell=.001
    def linear(v):
        return -math.expm1(-alpha*v)/alpha-rho*(1-(1+alpha*v)*math.exp(-alpha*v))/(alpha*alpha)
    if q<=ell:
        v=min(h,q/(rho*ell))
        return q*(-math.expm1(-alpha*v))/alpha-rho*ell*(1-(1+alpha*v)*math.exp(-alpha*v))/(alpha*alpha)
    te=math.log(q/ell)/rho;v=min(h,te);z=max(0,min(h-te,1/rho))
    return q*(-math.expm1(-(rho+alpha)*v))/(rho+alpha)+ell*math.exp(-alpha*te)*linear(z)


def find(ka=9,stages=1,w=90,h=180):
    p=j.accepted.old.environment(j.accepted.old.HANDOFF['rows'][0])
    prof=j.accepted.CFG['profiles'][2]
    growth=dict(j.accepted.CFG['growth_classes'][0],w_s=str(w),h_s=str(h))
    c=j.accepted.calendar(p,prof,ka,growth)
    ps,pl,b,B,phi,rho=map(float,(c['Ps'],c['Pl'],p['b'],p['B'],c['phi'],F('.048')))
    window=w if stages==2 else h;shift=ps+float(320*j.accepted.TP)
    d=float(j.phase_constants(c)['d'])
    qs=[b]+[b+(B-b)*i/160 for i in range(1,161)]
    ks=[j.float_coefficient(q,rho,c,stages,4) for q in qs]
    best=None;all_rows=[]
    for alpha in (1/15,1/20,1/30,1/40,1/60):
        kappa=B*(phi*(shift+d)+(phi-phi*phi/2)*pl+phi*math.exp(-alpha*(window-ps))/alpha)
        ek=math.exp(kappa)
        zs=[[z_lower(q,alpha,rho,h)+(B/alpha-z_lower(q,alpha,rho,h))*i/48 for i in range(49)] for q in qs]
        for q0 in (.003,.006,.01,.02,.04,.06,.08):
            for mult in (.125,.25,.5,1,2,4,8):
                A=mult*(pl-ps)*ek/phi
                u=pl*b*b
                slope=0.;active=None
                for q,K,zz in zip(qs[1:],ks[1:],zs[1:]):
                    for z in zz:
                        ee=math.exp(-phi*z)
                        extra=min(max(0.,K-ps),(pl-ps)*ek*ee)
                        cost=q*q*(ps+extra)
                        derivative=A*ee*(rho*q-phi*(q-alpha*z)*(q-q0)) if q>=q0 else 0.
                        v=(cost+derivative-u)/(q-b)
                        if v>slope:slope,active=v,(q,z)
                bound=u*float(p['T'])+slope*float(p['FS'])+A*(B-q0)
                row=dict(ka=ka,stages=stages,w=w,h=h,alpha=alpha,q0=q0,A=A,mult=mult,u=u,v=slope,
                         integral=bound,active=active,kappa=kappa,not_a_certificate=True)
                all_rows.append(row)
                if best is None or bound<best['integral']:best=row
    constant=float(p['errors']+p['D']+p['K0']*p['B']*(c['Ps']+j.accepted.T['d'])/p['W'])
    best['approx_risk_without_cross']=constant+best['integral']/(2*p['W'])
    return best,all_rows


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--ka',type=int,default=9);ap.add_argument('--stage',type=int,default=1)
    args=ap.parse_args()
    best,_=find(args.ka,args.stage)
    print(json.dumps(best,indent=2))
