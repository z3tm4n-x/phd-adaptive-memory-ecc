"""T119 addressed joint skipped-boundary bound (no online hidden state).

The float routine is a diagnostic/candidate selector only. Admission uses
directed intervals and a verified majorant on every q-cell.
Accepted T114 modules are imported read-only.
"""
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
import sys
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'experiments/t114-two-stage-err'))
import calculate as accepted
from intervals import I, primitive, exposure


def moment(q, t, rho, ell=F('.001')):
    """Directed integral of r * backward_cone(q,r), for t>=0."""
    if min(q,t,rho)<0: raise ValueError('negative argument')
    if not rho: return I(q*t*t/2)
    if q<=ell:
        v=min(t,q/(rho*ell))
        return I(q*v*v/2-rho*ell*v*v*v/3)
    qi,ti,ri,li=map(I,(q,t,rho,ell))
    te=(qi/li).ln()/ri
    v=I(min(ti.lo,te.lo),min(ti.hi,te.hi))
    zz=ti-te;cap=I(1)/ri
    z=I(max(0,min(zz.lo,cap.lo)),max(0,min(zz.hi,cap.hi)))
    return qi/(ri*ri)*(I(1)-(I(1)+ri*v)*(I(0)-ri*v).exp())+li*(te*z+(I(1)-ri*te)*z*z/I(2)-ri*z*z*z/I(3))


def phase_constants(c):
    # Mandatory starts differ from the equally spaced ideal by at most
    # 7*(g-c) ticks; one further lattice gap encloses arbitrary endpoints.
    phase_edge=(c['ka']*c['g']+7*(c['g']-164))*accepted.TP
    return dict(phi=c['phi'],P=c['Pl'],d=c['tau']-c['Pl']+phase_edge+2*accepted.JIT,
                phase_edge=phase_edge,discrepancy=F(4))


def proof_window(c, stages):
    # The actual freeze may differ from its virtual edge by J. Retain 2J
    # explicitly in addition to the accepted directed timer enclosure.
    return (c['w'] if stages==2 else c['h'])-2*accepted.JIT


def proof_bands(c):
    safe=dict(c,w=c['w']-2*accepted.JIT,h=c['h']-2*accepted.JIT,
              tau=c['tau']+2*accepted.JIT)
    return accepted.bands(safe,2)


def ramp_mass_interval(q, rho, ph, amin, amax, extent):
    """Lower mass in the joint zero band at one fixed pair endpoint.

    r is age from the LAST frozen skipped boundary; endpoint offset is a.
    Future parents relative to that endpoint are discarded, never assigned
    a lower intensity by a backward cone. Clock and phase uncertainty are
    enclosed by amin<=a<=amax.
    """
    phi,P,d=ph['phi'],ph['P'],ph['d']
    if not phi: return I(0)
    r0=(1-phi)*P+d;r1=P+d
    left=max(r0,-amin,F(0));right=min(r1,extent)
    total=I(0)
    if right>left:
        s0,s1=left+amax,right+amax
        mass=exposure(q,s0,s1,rho)
        mom=moment(q,s1,rho)-moment(q,s0,rho)
        total=total+(mom-I(amax+r0)*mass)/I(P)
    left=max(r1,-amin,F(0))
    if extent>left:
        total=total+I(phi)*exposure(q,left+amax,extent+amax,rho)
    return I(max(0,total.lo),max(0,total.hi))


def ramp_mass(q, rho, ph, amin, amax, extent):
    return F(ramp_mass_interval(q,rho,ph,amin,amax,extent).lo)


def endpoint_upper(q,rho,c,n,lo,hi,which,stages):
    ps,pm=c['Ps'],c['Ps_min'];g0=320*accepted.TM;g1=320*accepted.TP
    window=proof_window(c,stages)
    ph=phase_constants(c)
    if window < c['Pl']+ph['d']+ps:
        raise ValueError('joint zero-union collapse condition failed')
    if which=='left':
        amin=g0-(n-lo)*ps;amax=g1-(n-hi)*pm
        old_shift=g1-(1-hi)*pm
    elif which=='right':
        amin=g0+lo*pm;amax=g1+hi*ps
        old_shift=g1+(n-1+hi)*ps
    else: raise ValueError(which)
    mu=ramp_mass(q,rho,ph,amin,amax,window+(n-1)*pm)
    probability=(I(0)-I(mu)).exp()
    if stages==2:
        for a,b,allowed in proof_bands(c)[1:]:
            assert allowed==1
            m=max(F(0),c['phi']*F(exposure(q,a+old_shift,b+old_shift,rho).lo))
            probability=probability*(I(0)-I(m)).exp()*(I(1)+I(m))
    return min(F(1),F(probability.hi))


def coefficient(q,rho,c,stages,phase_cells=8):
    ka=c['ka'];ps=c['Ps']
    if ka==1: return ps
    total=F(0)
    for n in range(1,ka):
        for j in range(phase_cells):
            lo,hi=F(j,phase_cells),F(j+1,phase_cells)
            rr=sum(endpoint_upper(q,rho,c,n,lo,hi,k,stages) for k in ('left','right'))
            total+=(ka-n)*rr
    return min(c['Pl'],ps*(1+(F(1,ka*phase_cells)+F(4,524288))*total))


def coefficient_lower(q,rho,c,stages,phase_cells=8):
    """Lower enclosure of the ANALYTIC relaxed K, NOT of physical risk.

    Used only to prove a barrier for affine majorization of this K. An upper
    numerical enclosure of K cannot serve that purpose.
    """
    ka=c['ka'];ps,pm=c['Ps'],c['Ps_min']
    if ka==1:return ps
    g0,g1=320*accepted.TM,320*accepted.TP;ph=phase_constants(c)
    window=proof_window(c,stages);total=F(0)
    for n in range(1,ka):
        for z in range(phase_cells):
            lo,hi=F(z,phase_cells),F(z+1,phase_cells)
            for side in ('left','right'):
                if side=='left':
                    amin,amax=g0-(n-lo)*ps,g1-(n-hi)*pm
                    old_shift=g1-(1-hi)*pm
                else:
                    amin,amax=g0+lo*pm,g1+hi*ps
                    old_shift=g1+(n-1+hi)*ps
                mu=ramp_mass_interval(q,rho,ph,amin,amax,window+(n-1)*pm)
                prob=(I(0)-mu).exp()
                if stages==2:
                    for a,b,allowed in proof_bands(c)[1:]:
                        mu=I(c['phi'])*exposure(q,a+old_shift,b+old_shift,rho)
                        prob=prob*(I(0)-mu).exp()*(I(1)+mu)
                total+=(ka-n)*max(F(0),F(prob.lo))
    return min(c['Pl'],ps*(1+(F(1,ka*phase_cells)+F(4,524288))*total))


def majorant(p,c,rho,stages,phase_cells=8,q_cells=96,refinements=4):
    """Finite q-cell majorant; no claim that the selected u is optimal."""
    if c['ka']==1:
        return dict(integral=c['Ps']*p['S2exact'],u=None,v=None,cells=0,
                    phase_cells=phase_cells,slack=F(0),active=None)
    b,B=p['b'],p['B'];xs=sorted(set([b,F('.001'),B]+[B*i/q_cells for i in range(1,q_cells) if B*i/q_cells>b]))
    cache={}
    def coef(q):
        if q not in cache: cache[q]=coefficient(q,rho,c,stages,phase_cells)
        return cache[q]
    for iteration in range(refinements):
        cells=[(lo,hi,coef(lo)) for lo,hi in zip(xs[:-1],xs[1:])]
        choices=[];active=set()
        for mult in (1,2,4,16):
            u=mult*c['Pl']*b*b
            v,al,ah=max((max(F(0),(A*hi*hi-u)/(hi-b)),lo,hi) for lo,hi,A in cells)
            slack=min(u+v*(q-b)-A*q*q for lo,hi,A in cells for q in (lo,hi))
            assert slack>=0
            active.add((al,ah))
            choices.append(dict(integral=min(c['Pl']*p['S2exact'],u*p['T']+v*p['FS']),u=u,v=v,
                                cells=len(cells),phase_cells=phase_cells,slack=slack,active=[al,ah],u_multiplier=mult))
        selected=min(choices,key=lambda x:x['integral'])
        xs=sorted(set(xs+[(lo+hi)/2 for lo,hi in active]))
    return selected


def compute(p,profile,growth,ka,stages,**numeric):
    assert p['W']==524288, 'phase-discrepancy coefficient is pinned to R0-A'
    c=accepted.calendar(p,profile,ka,growth);rho=F(growth['rho_per_s'])
    ma=majorant(p,c,rho,stages,**numeric)
    cross=accepted.old.cross(dict(p,beta=F(1,2*p['W'])),c['Ps_min'],c['Pl'],ka,p['S2exact'],accepted.T['d'])
    initial=p['K0']*p['B']*(c['Ps']+accepted.T['d'])/p['W']
    upper=p['errors']+p['D']+initial+ma['integral']/(2*p['W'])+cross['X']
    price=accepted.price(p,c,profile,upper,stages)
    return dict(calendar=c,stages=stages,growth=growth,profile=profile,majorant=ma,cross=cross,
                initial=initial,risk_upper=upper,risk_slack=p['eps']-upper,
                certified=upper<=p['eps'],price=price,resources=accepted.resource(c))


def float_primitives(q,t,rho):
    ell=.001
    if q<=ell:
        v=min(max(0.,t),q/(rho*ell))
        return q*v-rho*ell*v*v/2, q*v*v/2-rho*ell*v*v*v/3
    te=math.log(q/ell)/rho;v=min(max(0.,t),te);z=max(0.,min(t-te,1/rho))
    A=q/rho*(-math.expm1(-rho*v))+ell*(z-rho*z*z/2)
    J=q/(rho*rho)*(1-(1+rho*v)*math.exp(-rho*v))+ell*(te*z+(1-rho*te)*z*z/2-rho*z*z*z/3)
    return A,J


def float_coefficient(q,rho,c,stages,phase_cells=8):
    ka=c['ka'];ps=float(c['Ps']);pl=float(c['Pl']);phi=float(c['phi'])
    if ka==1:return ps
    w=float(proof_window(c,stages));d=float(phase_constants(c)['d']);g=float(320*accepted.TP)
    if w<pl+d+ps: return math.inf
    oldbands=[tuple(float(z) for z in (a,b)) for a,b,k in proof_bands(c)[1:]] if stages==2 else []
    r0=(1-phi)*pl+d;r1=pl+d;total=0.
    def integral(l,r):
        return max(0.,float_primitives(q,r,rho)[0]-float_primitives(q,l,rho)[0])
    for n in range(1,ka):
        for j in range(phase_cells):
            lo,hi=j/phase_cells,(j+1)/phase_cells
            for left in (True,False):
                amin=g+((lo-n) if left else lo)*ps
                a=g+((hi-n) if left else hi)*ps
                oldshift=g+((hi-1) if left else n-1+hi)*ps
                end=w+(n-1)*ps; l=max(r0,-amin,0.);r=min(r1,end);mu=0.
                if r>l:
                    x0,x1=l+a,r+a;A=integral(x0,x1)
                    J=float_primitives(q,x1,rho)[1]-float_primitives(q,x0,rho)[1]
                    mu+=(J-(a+r0)*A)/pl
                l=max(r1,-amin,0.)
                if end>l:mu+=phi*integral(l+a,end+a)
                rr=math.exp(-max(0.,mu))
                for aa,bb in oldbands:
                    m=phi*integral(aa+oldshift,bb+oldshift);rr*=math.exp(-m)*(1+m)
                total+=(ka-n)*min(1.,rr)
    return min(pl,ps*(1+(1/(ka*phase_cells)+4/524288)*total))


def preview(p,profile,growth,ka,stages,phase_cells=4,q_cells=96):
    c=accepted.calendar(p,profile,ka,growth);rho=float(F(growth['rho_per_s']))
    b,B=float(p['b']),float(p['B']);pl=float(c['Pl'])
    qs=[b+(B-b)*i/q_cells for i in range(1,q_cells+1)]
    co=[float_coefficient(q,rho,c,stages,phase_cells) for q in qs]
    integral=pl*float(p['S2exact'])
    for mult in (1,2,4,16):
        u=mult*pl*b*b;v=max(0.,max((A*q*q-u)/(q-b) for q,A in zip(qs,co)))
        integral=min(integral,u*float(p['T'])+v*float(p['FS']))
    if ka==1: integral=float(c['Ps']*p['S2exact'])
    cross=accepted.old.cross(dict(p,beta=F(1,2*p['W'])),c['Ps_min'],c['Pl'],ka,p['S2exact'],accepted.T['d'])
    risk=float(p['errors']+p['D']+p['K0']*p['B']*(c['Ps']+accepted.T['d'])/p['W']+cross['X'])+integral/(2*p['W'])
    return risk
