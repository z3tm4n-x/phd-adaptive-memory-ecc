"""Finite directed verification of a fixed T119 storage function.

No controller optimization or simulation. The result is a sufficient upper
bound even when it fails epsilon; failed coefficients remain in the report.
"""
from fractions import Fraction as F
import joint as j
from intervals import I


def weighted_cone(q,t,rho,alpha,ell=F('.001')):
    """Integral_0^t exp(-alpha*r)*L_rho(q,r) dr, enclosed outward."""
    if min(q,t,rho)<0 or alpha<=0 or rho<=0: raise ValueError('arguments')
    ai,ri,li=I(alpha),I(rho),I(ell)
    def linear(v):
        e=(I(0)-ai*v).exp()
        return (I(1)-e)/ai-ri*(I(1)-(I(1)+ai*v)*e)/(ai*ai)
    if q<=ell:
        v=I(min(t,q/(rho*ell)));e=(I(0)-ai*v).exp()
        return I(q)*(I(1)-e)/ai-ri*li*(I(1)-(I(1)+ai*v)*e)/(ai*ai)
    te=(I(q)/li).ln()/ri
    ti=I(t);v=I(min(ti.lo,te.lo),min(ti.hi,te.hi));zz=ti-te;cap=I(1)/ri
    z=I(max(0,min(zz.lo,cap.lo)),max(0,min(zz.hi,cap.hi)))
    return I(q)*(I(1)-(I(0)-(ai+ri)*v).exp())/(ai+ri)+li*(I(0)-ai*te).exp()*linear(z)


def kappa_upper(p,c,stages,alpha):
    ph=j.phase_constants(c);phi=ph['phi'];window=j.proof_window(c,stages)
    H=window-c['Ps'];shift=c['Ps']+320*j.accepted.TP
    if H<c['Pl']+ph['d']:raise ValueError('insufficient zero window')
    tail=F((I(0)-I(alpha*H)).exp().hi)
    return p['B']*(phi*(shift+ph['d'])+(phi-phi*phi/2)*c['Pl']+phi*tail/alpha)


def verify(p,c,rho,stages,alpha,q0,A,phase_cells=4,q_cells=128,z_cells=64):
    """Produce u,v with cost+dV <= u+v*(q-b)+ on every covering rectangle.

    V=A*(q-q0)+*exp(-phi*z). A is fixed before verification, not obtained
    from these maxima as an optimizer. All rectangle maxima are proven.
    """
    assert p['W']==524288 and q0>max(p['b'],F('.001')) and A>=0 and c['ka']>1
    phi=c['phi'];b,B=p['b'],p['B'];ps,pl=c['Ps'],c['Pl']
    kap=kappa_upper(p,c,stages,alpha);ek=F(I(kap).exp().hi)
    xs=sorted(set([b,F('.001'),q0,B]+[b+(B-b)*i/q_cells for i in range(1,q_cells)]))
    u=pl*b*b
    # Before t=h only short pairs are possible; the same budget pays them.
    v=max(F(0),(ps*B*B-u)/(B-b));active=None;rectangles=0;min_slack=None
    bounds=[]
    for lo,hi in zip(xs[:-1],xs[1:]):
        K=j.coefficient(lo,rho,c,stages,phase_cells)
        if hi<=q0:
            # With V=0, the increasing rational quotient proves this whole cell.
            vl=max(F(0),(K*hi*hi-u)/(hi-b))
            if vl>v:v,active=vl,[lo,hi,None,None]
            bounds.append((vl,lo,hi,None,None));continue
        zmin=max(F(0),F(weighted_cone(lo,j.proof_window(c,1),rho,alpha).lo));zmax=B/alpha
        for k in range(z_cells):
            zl=zmin+(zmax-zmin)*k/z_cells;zh=zmin+(zmax-zmin)*(k+1)/z_cells
            eh=F((I(0)-I(phi*zl)).exp().hi);el=F((I(0)-I(phi*zh)).exp().lo)
            # D(q,z) is increasing in z and concave quadratic in q>=q0.
            vertex=(rho+phi*q0+phi*alpha*zh)/(2*phi)
            q=max(lo,min(hi,vertex))
            Dmax=rho*q-phi*(q-alpha*zh)*(q-q0)
            generator=A*Dmax*(eh if Dmax>=0 else el)
            cost=hi*hi*(ps+min(K-ps,(pl-ps)*ek*eh))
            upper=cost+generator
            vl=max(F(0),(upper-u)/(lo-b))
            if vl>v:v,active=vl,[lo,hi,zl,zh]
            bounds.append((vl,lo,hi,zl,zh));rectangles+=1
    # v is an exact rational upper for every complete rectangle, not samples.
    assert all(v>=bound[0] for bound in bounds)
    initial=A*(B-q0)
    return dict(alpha=alpha,q0=q0,A=A,kappa_upper=kap,u=u,v=v,initial_storage_upper=initial,
                integral=u*p['T']+v*p['FS']+initial,active_rectangle=active,
                rectangles=rectangles,phase_cells=phase_cells,q_cells=q_cells,z_cells=z_cells,
                max_slope_excess=max(row[0]-v for row in bounds),verified=True)
