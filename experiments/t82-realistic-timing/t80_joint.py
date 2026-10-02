"""Addressed T80 ff85fc8: (6a), B.6/B.7, V.3. Old engine is immutable."""
from __future__ import annotations

import copy
import hashlib
import json
from decimal import Decimal as D
from fractions import Fraction as F
from functools import lru_cache
from math import isqrt

import t80_engine as old
from t80_engine import HERE, FAMILY, PROFILE, errors, phi, t58, short_gate
from t80_err import I, integral_A
from timing import min_ticks, resources

CONFIG = json.loads((HERE/'t80_joint_config.json').read_text())


def source_check():
    variants = old.source_check()
    for name, expected in CONFIG['source_blobs'].items():
        raw = (HERE/'inputs/ff85fc8'/name).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == expected, name
    source = json.loads((HERE/'inputs/ff85fc8/t80-realistic-channel-inputs.json').read_text())
    assert source['accepted_input_sets'] == old.SOURCE['accepted_input_sets']
    assert source['new_family'] == old.SOURCE['new_family']
    assert source['pilot'] == old.SOURCE['pilot']
    return variants


def pair_bound(p, ka, vc):
    b, B, T, S2, FS, Ps = (p[k] for k in ('b','B','T','S2','FS','Ps'))
    Pl = ka*Ps
    Vc = min(vc*vc*T, b*b*T+(vc+b)*FS)
    prior = Ps*S2+Pl*Vc
    mandatory = Pl*S2
    u = (Ps+Pl)*b*b
    if b < vc < B:
        va, vb = (Ps+Pl)*(vc+b), (Ps*B*B-u)/(B-b)
        v = max(va, vb, F(0))
        affine = u*T+v*FS
        opts = [('joint', affine), ('old', prior), ('mandatory', mandatory)]
        branch = 'low' if va >= vb else 'peak'
    else:
        v = va = vb = affine = None
        opts = [('old', prior), ('mandatory', mandatory)]
        branch = 'not_applicable'
    active, Q = min(opts, key=lambda kv: kv[1])
    risk = errors(p['q'], p['mode'])+p['Dstar']+p['K']*B*Ps/p['W']+p['beta']*Q
    return dict(Q=Q, old_pair=prior, mandatory_pair=mandatory, u=u, v=v,
                v_low=va, v_peak=vb, affine_pair=affine,
                pair_active=active, v_branch=branch, risk_upper=risk,
                risk_slack=p['eps']-risk, D_allow=p['Dstar']+p['eps']-risk)


def flat_v(p, ka):
    return p['B']*(p['B']/F(1+ka)-p['b'])/(p['B']-p['b'])


def price_edges(p, TQ=None, KQ=1):
    TQ = p['T'] if TQ is None else TQ
    if TQ <= 0 or KQ < 1:
        raise ValueError('positive quiet horizon and number of intervals required')
    return 2*p['cp']*KQ/TQ, p['sigmaX']*KQ/TQ


@lru_cache(maxsize=100000)
def positive_A(x, bU, t, rho=F('.048'), l=F('.001')):
    if min(x,bU,t,rho) < 0:
        raise ValueError('negative input')
    if x <= bU or not t:
        return I(0)
    if not rho:
        return I((x-bU)*t)
    if x <= l:
        v = min(t,(x-bU)/(rho*l))
        return I((x-bU)*v-rho*l*v*v/2)
    def H(v):
        return I(v/l) if v <= l else I(1)+(I(v)/I(l)).ln()
    stop = (H(x)-H(bU))/I(rho)
    tm, tp = min(t,F(stop.lo)), min(t,F(stop.hi))
    # A is increasing; subtract the whole possible invisible integral.
    lo = integral_A(x,tm,rho,l)-I(bU*tp)
    hi = integral_A(x,tp,rho,l)-I(bU*tm)
    return I(max(D(0),lo.lo), max(D(0),hi.hi))


@lru_cache(maxsize=100000)
def fast_exposure(vc, bU, wm, hF):
    if hF < wm:
        raise ValueError('forecast end before window end')
    value = positive_A(vc,bU,hF)-positive_A(vc,bU,hF-wm)
    return F(max(D(0),value.lo)), F(max(D(0),value.hi))


def window(p, aM, w, d, qratio, kind, divisor):
    ticks = divisor*t58.ceil(w/(divisor*F(p['cfg']['service']['tick_nominal_s'])))
    wm, wp = ticks*p['tm'], ticks*p['tp']
    dm, dp = wm/divisor, wp/divisor
    dt = min_ticks(d,p['margin'],p['tm'])
    J = t58.ceil(p['T']/dm)
    H = old.smallest_H(J,F(p['q']['alpha_M']))
    qR = qratio*p['b']; bU = F(0) if kind=='total_load' else p['b']
    mr = old.retrospective(qR,bU,wm-dm)
    deadline = dt*p['tp']
    required = wp+deadline+dp+p['Gp']+p['gap']+p['f']+p['Ps']
    ht = min_ticks(required,p['margin'],p['tm'])
    mu = wp*(aM*p['b']*F(PROFILE['upper_to_lower_ratio'])+F(PROFILE['eta_per_s']))
    return dict(aM=aM,w=w,d=d,qratio=qratio,kind=kind,divisor=divisor,
                qR=qR,bU=bU,wm=wm,wp=wp,Delta_m=dm,Delta_p=dp,dp=deadline,
                dticks=dt,dmin=dt*p['tm'],J=J,H=H,mu=mu,mR=mr,h0=wm-dm,
                hF_ticks=ht,hF_max=ht*p['tp'],hF_min=ht*p['tm'],
                hF_required=required,hF_slack=ht*p['tm']-(1+p['margin'])*required,
                cadence_min_s=dm,ring_counters=divisor+1,
                total_messages_upper=J,physical_cadence_qualified=False)


@lru_cache(maxsize=100000)
def safe_threshold(mass, aM, H):
    values = []
    for z in map(F,FAMILY['z']):
        pl, pu = phi(z)
        k = t58.floor((aM*pl*mass-H)/z)
        values.append((k,z,aM*pl*mass-z*k-H,aM*pu*mass-z*(k+1)-H))
    k,z,slack,next_slack = max(values,key=lambda x:x[0])
    return dict(k=k,z=z,LOW_slack=slack,next_k_slack_upper=next_slack)


@lru_cache(maxsize=100000)
def poisson_chernoff(mu,k):
    """Upper on P(Pois(mu)>k); k+1 matters. Not the exact probability."""
    if k < 0: return F(1)
    if mu == 0: return F(0)
    r = F(k+1)
    if r <= mu: return F(1)
    exponent = I(r)*(I(r)/I(mu)).ln()-I(r)+I(mu)
    # Strictly positive upper, not numerical zero; (3/8)^160 < 1e-60.
    if exponent.lo >= 160:return F(1,10**60)
    return min(F(1),F((I(0)-exponent).exp().hi))


def analytic_safe_value(m,k):
    """B6, only under an independently declared all-z Laplace contract."""
    if m < 0 or k < 0: raise ValueError('nonnegative m,k')
    if k == 0: return I(m)
    if k >= m: return I(0)
    return I(m)-I(k)+I(k)*(I(k)/I(m)).ln()


def poisson_tail_exact(mu,k,tol=F(1,10**35)):
    """Finite interval sum + geometric remainder, no scipy/float decision."""
    if k < 0: return I(1)
    if mu == 0: return I(0)
    mi=I(mu)
    # If the lower tail is shorter, sum through k and subtract from one.
    if k < mu:
        term=(I(0)-mi).exp(); total=term
        for j in range(1,k+1):
            term=term*mi/I(j); total=total+term
        val=I(1)-total
        return val.clip(0,1)
    # Start at k+1 in log space to avoid exp(-mu) underflow for long windows.
    r=k+1
    fact=I(0)
    for j in range(2,r+1):fact=fact+I(j).ln()
    term=(I(0)-mi+I(r)*mi.ln()-fact).exp(); total=term; j=r
    while True:
        ratio=mi/I(j+1)
        remainder=term*ratio/(I(1)-ratio)
        if F(remainder.hi)<=tol:
            return I(max(D(0),total.lo),min(D(1),(total+remainder).hi))
        j+=1;term=term*mi/I(j);total=total+term
        if j>1000000:raise ArithmeticError('finite exact-tail bracket exhausted')


def k_price_exact(mu,target):
    if target <= 0:return None
    if target >= 1:return 0
    low=-1;high=max(1,t58.ceil(mu))
    while poisson_chernoff(mu,high)>target:high=2*high+1
    while high-low>1:
        mid=(high+low)//2;tail=poisson_tail_exact(mu,mid)
        if F(tail.hi)<=target:high=mid
        elif F(tail.lo)>target:low=mid
        else:raise ArithmeticError('price quantile unresolved at directed precision')
    return high


def cadence_context(p, divisor, available=True):
    q=copy.copy(p)
    q['CX']=p['CX']*F(divisor,2)
    cfg=copy.deepcopy(p['cfg'])
    cfg['resources']['extra_monitor_control_rate']=str(q['CX'])
    cfg['resources']['extra_monitor_control_sigma_s']=str(q['sigmaX'])
    rv=resources(cfg)
    q['resource']=rv
    q['cadence_pass']=available and rv['ok'] and (1+p['margin'])*rv['delay']<=F('.000003')
    return q


def strips(p,m,DQ,low_type):
    return old.strips(p,m,DQ if low_type=='reset-slow' else F(0))


def price(p,m,ka,risk,DE,DM,pM):
    T,b,Ps=p['T'],p['b'],p['Ps'];Pl=ka*Ps
    cf=p['cp']/p['gm'];cs=cf/ka
    E=DE if p['mode']=='combined' else F(0)
    pq=min(F(1),errors(p['q'],p['mode'],False)+p['Dstar']+
           p['K']*b*Ps/p['W']+p['beta']*Pl*b*b*T)
    false=pM+F(PROFILE['bad_window_probability'])
    start=(DM+E*p['K'])/T
    true_ERR=E*b;false_ERR=E*p['rF'];loss_ERR=E*p['rloss']
    flags=true_ERR+false_ERR+loss_ERR
    freq=F(m['J'],1)/T
    mon=freq*DM*false
    ecal,ectrl=price_edges(p)
    EX=ecal+p['CX']+ectrl
    whole_formula=cs+cf*min(F(1),start+flags+mon+pq)+EX
    hard=cf+EX
    TQ=F(9,10)*T;KQ=1000
    boundary=(DM*KQ+E*(p['K']+KQ*p['B']*(Pl+p['dE'])))/TQ
    freqQ=1/m['Delta_m']+2*KQ*m['wp']/(m['Delta_m']*TQ)+2*F(KQ)/TQ
    monQ=DM*freqQ*false
    eqcal,eqctrl=price_edges(p,TQ,KQ)
    EXQ=eqcal+p['CX']+eqctrl
    ret_formula=cs+cf*min(F(1),boundary+flags+monQ+min(F(1),risk))+EXQ
    quiet=min(hard,whole_formula);ret=min(cf+EXQ,ret_formula)
    pstar=((F('.01')-cs-EX)/cf-start-flags-pq)/(freq*DM)-F(PROFILE['bad_window_probability'])
    pstarQ=((F('.01')-cs-EXQ)/cf-boundary-flags-min(F(1),risk))/(freqQ*DM)-F(PROFILE['bad_window_probability'])
    return dict(quiet_upper=quiet,returns_upper=ret,objective=max(quiet,ret),
        quiet_formula_upper=whole_formula,returns_formula_upper=ret_formula,
        base_tax=cs,quiet_start_component=cf*start,quiet_ERR_component=cf*true_ERR,
        false_ERR_component=cf*false_ERR,loss_ERR_component=cf*loss_ERR,
        quiet_monitor_component=cf*mon,quiet_global_component=cf*pq,
        return_boundary=cf*boundary,return_monitor_component=cf*monQ,
        return_global_component=cf*min(F(1),risk),
        calendar_edge=ecal,control_edge=ectrl,return_calendar_edge=eqcal,
        return_control_edge=eqctrl,channel_rate=p['CX'],sigmaX=p['sigmaX'],
        DM=DM,DE=E,p_q=pq,pstar_whole=pstar,pstar_return=pstarQ,
        pstar=min(pstar,pstarQ),full_goal_pass=max(quiet,ret)<=F('.01'))


def max_ka(p,vc):
    if pair_bound(p,1,vc)['risk_upper']>p['eps']:return 0
    lo,hi=0,2048
    while hi-lo>1:
        mid=(lo+hi)//2
        if pair_bound(p,2*mid+1,vc)['risk_upper']<=p['eps']:lo=mid
        else:hi=mid
    return 2*lo+1


def near_odd(x, cap):
    i=t58.floor(x)
    return [k for k in (i-2,i-1,i,i+1,i+2) if k%2 and 1<=k<=cap]


def ka_candidates(p,m,vc,cap,E):
    """All possible turning points of piecewise affine-price + 1/ka.

    Lines are pair-budget branches. Their intersections cover both max and
    min changes. For every affine price piece include the two odd neighbours
    of sqrt(1/slope), endpoints and hard-mask branch. Exhaustive tests check it.
    """
    if cap<1:return []
    b,B,Ps,FS,T,S2=(p[k] for k in ('b','B','Ps','FS','T','S2'))
    Vc=min(vc*vc*T,b*b*T+(vc+b)*FS)
    lines=[(Ps*S2,Ps*Vc),(F(0),Ps*S2)]
    if b<vc<B:
        low=Ps*(b*b*T+(vc+b)*FS)
        peak0=Ps*b*b*T+(Ps*B*B-Ps*b*b)/(B-b)*FS
        peak1=Ps*b*b*T-Ps*b*b/(B-b)*FS
        lines.extend([(low,low),(peak0,peak1)])
    roots={1,cap}
    for a0,a1 in lines:
        for b0,b1 in lines:
            if a1!=b1:roots.update(near_odd((b0-a0)/(a1-b1),cap))
    slopes=[p['beta']*Ps*b*b*T]
    return_boundary=E*1000*B*Ps/(F(9,10)*T)
    slopes += [return_boundary+p['beta']*slope for _,slope in lines]
    for slope in slopes:
        if slope>0:
            r=isqrt(slope.denominator//slope.numerator)
            roots.update(near_odd(F(r),cap))
    return sorted(roots)


def evaluate(p,m,ka,vc,low_type,DQ,theta=None,rho_e=None,vc_kind='old'):
    risk=pair_bound(p,ka,vc)
    if risk['risk_upper']>p['eps']:return dict(status='long_risk',**risk)
    if low_type=='reset-slow':
        if vc>=F(FAMILY['v_e_per_s']):return dict(status='reset_vc_outside')
        le=old.lease(p,m,rho_e,theta)
        if le['lease_slack_s']<0:return dict(status='LOW_delay',**le,**risk)
        mass=upper=m['mR'];timing=le
    else:
        mass,upper=fast_exposure(vc,m['bU'],m['wm'],m['hF_max'])
        timing=dict(lease_ticks=m['hF_ticks'],lease_min_s=m['hF_min'],
                    lease_slack_s=m['hF_slack'],coverage_upper_s=m['hF_required'])
    th=safe_threshold(mass,m['aM'],m['H'])
    common=dict(ka=ka,vc=vc,vc_kind=vc_kind,theta=theta,mass_lower=mass,
                mass_upper=upper,mu_upper=m['mu'],H=m['H'],J=m['J'],
                low_type=low_type,**th)|timing|risk
    if th['k']<0:return dict(status='LOW_uninformative',**common)
    DE,DM=strips(p,m,DQ,low_type)
    pm=poisson_chernoff(m['mu'],th['k'])
    pr=price(p,m,ka,risk['risk_upper'],DE,DM,pm)
    return dict(status='certified_conditional',pM_upper=pm,**common,**pr)


def best_reset(p,m,rho_e,DQ):
    best=None;failed=None;count=0;quiet_best=None
    th=safe_threshold(m['mR'],m['aM'],m['H'])
    if th['k']<0:
        return dict(status='LOW_uninformative',mass_lower=m['mR'],mass_upper=m['mR'],
                    mu_upper=m['mu'],**th,evaluated_candidates=0,minimum_whole_quiet=None)
    DE,DM=strips(p,m,DQ,'reset-slow')
    pm=poisson_chernoff(m['mu'],th['k'])
    # If both monitor strips alone fill the mask, every accepted ka/theta
    # has exactly the same capped price. This is an exact pruning, not a
    # change to the channel, objective, or risk budget.
    mask_filled=(F(m['J'])*DM/p['T']*pm>=1 and DM/m['Delta_m']*pm>=1)
    for theta in map(F,FAMILY['vc_fraction_of_gap_qR_to_ve']):
        vc=m['qR']+theta*(F('.001')-m['qR'])
        le=old.lease(p,m,rho_e,theta)
        if le['lease_slack_s']<0:
            failed=dict(status='LOW_delay',**le)
            continue
        cap=max_ka(p,vc)
        if not cap:failed=dict(status='long_risk');continue
        ks=[cap] if mask_filled else ka_candidates(p,m,vc,cap,DE if p['mode']=='combined' else F(0))
        for ka in ks:
            row=evaluate(p,m,ka,vc,'reset-slow',DQ,theta,rho_e)
            count+=1
            if row['status']!='certified_conditional':failed=row;continue
            if quiet_best is None or row['quiet_upper']<quiet_best:quiet_best=row['quiet_upper']
            row['ka_max_same_vc']=cap
            row['next_odd_risk']=pair_bound(p,cap+2,vc)['risk_upper'] if cap<4095 else None
            if best is None or row['objective']<best['objective']:best=row
        if mask_filled and best is not None:break
    return (best or failed or dict(status='long_risk'))|{'evaluated_candidates':count,'minimum_whole_quiet':quiet_best}


def best_direct(p,m,only_flat=False,include_flat=True):
    best=None;failed=None;count=0;quiet_best=None
    # Old six vc candidates remain; their threshold is independent of ka.
    if not only_flat:
        for theta in map(F,FAMILY['vc_fraction_of_gap_qR_to_ve']):
            vc=m['qR']+theta*(F('.001')-m['qR'])
            cap=max_ka(p,vc)
            if not cap:continue
            DE,_=strips(p,m,F(0),'direct-fast')
            for ka in ka_candidates(p,m,vc,cap,DE if p['mode']=='combined' else F(0)):
                row=evaluate(p,m,ka,vc,'direct-fast',F(0),theta)
                count+=1
                if row['status']!='certified_conditional':failed=row;continue
                if quiet_best is None or row['quiet_upper']<quiet_best:quiet_best=row['quiet_upper']
                row['ka_max_same_vc']=cap
                row['next_odd_risk']=pair_bound(p,cap+2,vc)['risk_upper'] if cap<4095 else None
                if best is None or row['objective']<best['objective']:best=row
    # Preregistered B11 candidates, no extra vc grid. Full odd enumeration.
    for ka in (range(1,4096,2) if include_flat else []):
        vf=flat_v(p,ka)
        if vf<=p['b']:break
        # At or below vflat, joint affine branch is independent of vc.
        for kind,vc in [('mid_flat',(p['b']+vf)/2),('flat',vf)]:
            rb=pair_bound(p,ka,vc)
            if rb['risk_upper']>p['eps']:continue
            if best is not None and p['cp']/p['gm']/ka>=best['objective']:continue
            row=evaluate(p,m,ka,vc,'direct-fast',F(0),vc_kind=kind)
            count+=1
            if row['status']!='certified_conditional':failed=row;continue
            if quiet_best is None or row['quiet_upper']<quiet_best:quiet_best=row['quiet_upper']
            row['v_flat']=vf
            if best is None or row['objective']<best['objective']:best=row
    return (best or failed or dict(status='long_risk'))|{'evaluated_candidates':count,'minimum_whole_quiet':quiet_best}


def requirement_B7(m,mass,target,z,y):
    if not 0<target<1:return dict(status='nonpositive_or_unneeded_pstar')
    z,y=F(z),F(y)
    phi_lo=I(phi(z)[0]);ey=I(y).exp()-I(1)
    C=phi_lo*I(mass)/I(z)-I(m['wp']*F(PROFILE['upper_to_lower_ratio']))*I(m['b_nom'])*ey/I(y)
    if C.hi<=0:return dict(status='nonpositive_contrast',contrast_lower=F(C.lo),contrast_upper=F(C.hi))
    if C.lo<=0:return dict(status='unresolved_contrast',contrast_lower=F(C.lo),contrast_upper=F(C.hi))
    H=I(m['H']);log=(I(1)/I(target)).ln()
    num=H/I(z)+I(F(PROFILE['eta_per_s'])*m['wp'])*ey/I(y)+log/I(y)+I(1)
    a=(num/C).hi
    return dict(status='sufficient',a_suff_upper=F(a),contrast_lower=F(C.lo),z=z,y=y)


def conflict_B3(p,m):
    applies=(m['divisor']==2 and m['qR']<=2*p['b'] and m['mu']>=m['aM']*p['b']*m['wm'])
    lower=F(1)-t58.exp_neg(F(m['H']))[1] if applies else None
    return dict(B3_applies=applies,pM_B3_lower=lower,
                a_mass=m['aM']*m['mR'],mu_upper=m['mu'],mR=m['mR'],
                H=m['H'],J=m['J'],alpha_M=F(p['q']['alpha_M']))
