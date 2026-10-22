"""Directed n39 T196(7)/T119 certificate, explicitly parameterized by W/ell.

Accepted T119 is read-only. This new implementation replaces its fixed
W=524288 and ell=.001 by the common-input values and retains cell evidence.
No floating-point admission and no physical acceptance.
"""
from fractions import Fraction as F
from functools import lru_cache
import importlib.util
from pathlib import Path

from codec import ROOT
from comparison import NS,ceil,service,period
from cost import per_bit_moment_caps

spec=importlib.util.spec_from_file_location('t186_directed_intervals',ROOT/'experiments/t114-two-stage-err/intervals.py')
intervals=importlib.util.module_from_spec(spec);spec.loader.exec_module(intervals)
I=intervals.I


@lru_cache(maxsize=40000)
def exposure(q,left,right,rho,ell):
    if right<left or left<0:raise ValueError('invalid backward-cone interval')
    z=intervals.primitive(q,right,rho,ell)-intervals.primitive(q,left,rho,ell)
    return I(max(0,z.lo),max(0,z.hi))


@lru_cache(maxsize=40000)
def moment(q,t,rho,ell):
    if min(q,t,rho)<0 or ell<=0:raise ValueError('invalid cone moment')
    if not rho:return I(q*t*t/2)
    if q<=ell:
        v=min(t,q/(rho*ell))
        return I(q*v*v/2-rho*ell*v*v*v/3)
    qi,ti,ri,li=map(I,(q,t,rho,ell))
    te=(qi/li).ln()/ri
    v=I(min(ti.lo,te.lo),min(ti.hi,te.hi))
    zz=ti-te;cap=I(1)/ri
    z=I(max(0,min(zz.lo,cap.lo)),max(0,min(zz.hi,cap.hi)))
    return qi/(ri*ri)*(I(1)-(I(1)+ri*v)*(I(0)-ri*v).exp())+li*(te*z+(I(1)-ri*te)*z*z/I(2)-ri*z*z*z/I(3))


def calendar(cfg,k):
    W=cfg['words'];s=service(cfg,39);xm,xp,J=s['xminus'],s['xplus'],s['J']/NS
    if k%2!=1 or W&(W-1):raise ValueError('power-of-two W and odd inverse-address k required')
    tm,tp=xm/NS,xp/NS;g=cfg['calendar']['g_ticks'];c=cfg['calendar']['c_ticks']
    ps=W*g*tp;pm=W*g*tm;pl=k*ps
    E=s['upper']['E']/NS;app=s['upper']['app_write']/NS
    tau=pl+E+app+F(cfg['adaptive']['source_to_fresh_rule_upper_ns'],NS)+2*J
    quantum=cfg['adaptive']['timer_quantum_ticks']
    def timer(seconds,q=quantum):
        count=ceil((F(seconds)+J)/(q*tm))+1
        return dict(count=count,ticks=q*count,lower=(count-1)*q*tm-J,upper=count*q*tp+J)
    wt=timer(F(cfg['adaptive']['short_hold_s']));ht=timer(F(cfg['adaptive']['long_hold_s']))
    pair=timer(F(cfg['adaptive']['source_pair_window_s']),4)
    w=min(wt['lower'],pair['lower']);h=ht['lower']
    NR=timer(ht['upper']+tau)
    phase_edge=(k*g+7*(g-c))*tp
    d=tau-pl+phase_edge+2*J
    protected=w-2*J
    if not protected>=pl+ps+d:raise ValueError('joint zero-union timer collapse condition failed')
    if not h>=w>tau or NR['lower']<ht['upper']+tau:raise ValueError('hold/recovery condition failed')
    if max(wt['count'],ht['count'],NR['count'])>=2**34:raise ValueError('timer exceeds34bit')
    return dict(W=W,ka=k,g=g,c=c,Ps=ps,Ps_min=pm,Pl=pl,tau=tau,
                TM=tm,TP=tp,J=J,gate=cfg['calendar']['freeze_ticks'],
                w=w,h=h,w_upper=wt['upper'],h_upper=ht['upper'],
                phi=1-F(1,W),phase_edge=phase_edge,d=d,protected_window=protected,
                short_timer=wt,long_timer=ht,source_PAIR=pair,recovery=NR,
                inverse_address=pow(k,-1,W),zero_union_slack=protected-pl-ps-d,
                mandatory='j<W or j%ka==0',observed_app_read=False)


def bands(c):
    w,h,tau=c['w']-2*c['J'],c['h']-2*c['J'],c['tau']+2*c['J']
    if not h>=w>tau:raise ValueError('protected old bands invalid')
    out=[];x=w
    while x<h:
        y=min(h,x+w-tau);out.append((x,y));x=y
    return out


def ramp_mass(q,rho,ell,c,amin,amax,extent):
    phi,P,d=c['phi'],c['Pl'],c['d']
    r0=(1-phi)*P+d;r1=P+d
    left=max(r0,-amin,F(0));right=min(r1,extent);total=I(0)
    if right>left:
        s0,s1=left+amax,right+amax
        mass=exposure(q,s0,s1,rho,ell)
        mom=moment(q,s1,rho,ell)-moment(q,s0,rho,ell)
        total=total+(mom-I(amax+r0)*mass)/I(P)
    left=max(r1,-amin,F(0))
    if extent>left:total=total+I(phi)*exposure(q,left+amax,extent+amax,rho,ell)
    return max(F(0),F(total.lo))


def endpoint_upper(q,rho,ell,c,distance,lo,hi,left):
    ps,pm=c['Ps'],c['Ps_min'];g0=c['gate']*c['TM'];g1=c['gate']*c['TP']
    if left:
        amin=g0-(distance-lo)*ps;amax=g1-(distance-hi)*pm
        oldshift=g1-(1-hi)*pm
    else:
        amin=g0+lo*pm;amax=g1+hi*ps
        oldshift=g1+(distance-1+hi)*ps
    mu=ramp_mass(q,rho,ell,c,amin,amax,c['protected_window']+(distance-1)*pm)
    out=(I(0)-I(mu)).exp()
    for a,b in bands(c):
        mass=max(F(0),c['phi']*F(exposure(q,a+oldshift,b+oldshift,rho,ell).lo))
        out=out*(I(0)-I(mass)).exp()*(I(1)+I(mass))
    return min(F(1),F(out.hi))


def coefficient(q,rho,ell,c,phase_cells=8):
    k=c['ka'];total=F(0)
    for n in range(1,k):
        for j in range(phase_cells):
            lo,hi=F(j,phase_cells),F(j+1,phase_cells)
            total+=(k-n)*(endpoint_upper(q,rho,ell,c,n,lo,hi,True)+endpoint_upper(q,rho,ell,c,n,lo,hi,False))
    return min(c['Pl'],c['Ps']*(1+(F(1,k*phase_cells)+F(4,c['W']))*total))


def majorant(cfg,c,p):
    settings=cfg['adaptive']['information_numeric'];M=settings['phase_cells'];Q=settings['q_cells']
    b,B,ell=p['b'],p['B'],p['ell'];rho=p['rho'];cache={}
    xs=sorted(set([b,ell,B]+[B*i/Q for i in range(1,Q) if B*i/Q>b]))
    def coef(q):
        if q not in cache:cache[q]=coefficient(q,rho,ell,c,M)
        return cache[q]
    for iteration in range(settings['refinements']):
        cells=[(lo,hi,coef(lo)) for lo,hi in zip(xs[:-1],xs[1:])]
        choices=[];active=set()
        for mult in settings['u_multipliers']:
            u=mult*c['Pl']*b*b
            v,al,ah=max((max(F(0),(K*hi*hi-u)/(hi-b)),lo,hi) for lo,hi,K in cells)
            slack=min(u+v*(q-b)-K*q*q for lo,hi,K in cells for q in (lo,hi))
            if slack<0:raise ArithmeticError('q-cell affine majorant failed')
            choices.append(dict(integral=min(c['Pl']*p['S2'],u*p['T']+v*p['FS']),
                u=u,v=v,active=[al,ah],multiplier=mult,minimum_endpoint_slack=slack))
            active.add((al,ah))
        chosen=min(choices,key=lambda x:x['integral'])
        xs=sorted(set(xs+[(lo+hi)/2 for lo,hi in active]))
    u,v=chosen['u'],chosen['v']
    chosen.update(cells=[dict(lo=lo,hi=hi,K_upper=K,left_slack=u+v*(lo-b)-K*lo*lo,
                  right_slack=u+v*(hi-b)-K*hi*hi) for lo,hi,K in cells],
                  cells_count=len(cells),coefficient_evaluations=len(cache),phase_cells=M,
                  below_background_slack=u-c['Pl']*b*b,
                  justification='K nonincreasing; affine-minus-K_lo*q^2 concave on each entire closed q-cell')
    return chosen


def compute(cfg,k):
    W=cfg['words'];m=per_bit_moment_caps(cfg);env=cfg['environment'];nu=39*W
    factor=F(nu,env['reference_words']*env['reference_bits'])
    p=dict(W=W,b=F(env['reference_background_per_s'])*factor,
       B=F(env['reference_peak_per_s'])*factor,FS=F(env['reference_solar_mass'])*factor,
       ell=F(env['reference_growth_threshold_per_s'])*factor,
       rho=F(env['reference_growth_per_s']),T=F(cfg['mission_s']),F=nu*m['M1'],S2=nu*nu*m['M2'],
       rate_scale=factor,lower_channel_a=F(1),multiword_fraction=F(0))
    c=calendar(cfg,k);ma=majorant(cfg,c,p);beta=F(1,2*W);d=service(cfg,39)['upper']['E']/NS
    # T110 cross bound with the COUPLING coefficient, not physical37/38 etc.
    X1=beta*(k*d+c['Pl']/W)*p['S2'];eta=2*beta/W
    v=2*beta*d*(p['T']/c['Ps_min']+1)
    X2=min(p['B']*c['Pl'],p['F'])*min(p['B']*v,p['b']*v+eta*p['FS'],eta*p['F'])
    cross=min(X1,X2);delta=F(cfg['lifetime_other_budget'])
    upper=min(F(1),delta+ma['integral']*beta+cross)
    return dict(k=k,calendar=c,environment=p,majorant=ma,
        risk=dict(upper=upper,slack=F(cfg['epsilon'])-upper,relative_slack=1-upper/F(cfg['epsilon']),
                  terms=dict(lifetime_exceptions=delta,direct=F(0),initial=F(0),
                             joint_coupling=ma['integral']*beta,E_cross=cross),
                  E_cross_X1=X1,E_cross_X2=X2,coupling_beta=beta,
                  physical_unconditional_probability=None,exact_probability=None,
                  basis='new W/ell/phase T196(7)/T119(2)-(5), singleton conditional reference'),
        selected_target=F(cfg['epsilon'])/2,sufficient_for_target=upper<=F(cfg['epsilon'])/2,
        status='author numerical certificate, structural and physical applicability subject to stated conditions')


def candidates(cfg,progress=None):
    out=[]
    for k in cfg['adaptive']['candidate_ka']:
        row=compute(cfg,k);out.append(row)
        if progress:progress(k,row['risk']['upper'])
    eligible=[r for r in out if r['sufficient_for_target']]
    return dict(candidates=out,selected=max(eligible,key=lambda r:r['k']) if eligible else None)


if __name__=='__main__':
    import json,time
    path=Path(__file__).resolve().parent
    cfg=json.loads((path/'common-input.json').read_text(encoding='utf-8'))
    start=__import__('time').perf_counter()
    result=candidates(cfg,lambda k,u:print(json.dumps(dict(k=k,U=str(u),value=float(u))),flush=True))
    output=path/'outputs/informational.json'
    output.write_text(json.dumps(result,indent=2,sort_keys=True,default=str)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(selected=result['selected']['k'] if result['selected'] else None,
                         elapsed_s=time.perf_counter()-start)),flush=True)
