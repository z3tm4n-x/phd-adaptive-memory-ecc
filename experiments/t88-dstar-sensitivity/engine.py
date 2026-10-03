"""T88: finite offline parameter family, accepted risk/price formulas only."""
from __future__ import annotations

from collections import Counter
import copy
from fractions import Fraction as F
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
T82 = HERE.parent / 't82-realistic-timing'
sys.path.insert(0, str(T82))
import t80_engine as old
import t80_joint as j
import t80_err as err
from timing import resources
from run_t80 import json_write, decimal_text, csv_write

CFG = json.loads((HERE / 'config.json').read_text())
DMIN = F(CFG['D_min'])
TOL = F(CFG['D_bracket_tolerance'])
LIMIT = F(CFG['cost_limit'])


def context(shield, mode):
    v = j.source_check()[0]
    si = next(i for i, e in enumerate(v['input']['environments']) if e['shield_g_cm2'] == shield)
    p = old.context(v, CFG['margin'], 'internal38', si)
    assert p['set'] == CFG['input_set'] and p['c'] == 100 and p['g'] == 131
    p['mode'] = mode
    return p


def calendar(p, g):
    q = copy.copy(p)
    q['cfg'] = copy.deepcopy(p['cfg'])
    q['cfg']['service']['g_ticks'] = g
    q.update(g=g, gm=g*p['tm'], gp=g*p['tp'], gap=(2*g-p['c'])*p['tp'],
             Ps=p['W']*g*p['tp'])
    q['resource'] = resources(q['cfg'])
    q['resource_pass'] = q['resource']['ok'] and (1+p['margin'])*q['resource']['delay'] <= F('3e-6')
    return q


def g_cap(p):
    # On this input L=FS/(B-b)<T. For ka>=1, all three branches of
    # (6a) >= Ps*S2_exact: the peak branch has positive slope b^2(T-L).
    # For (9), Q>=0 and ka>=1 imply min(Pl*S2,Ps*S2+Pl*Q)>=Ps*S2.
    tight = j.t58.rarity(p['B'], p['b'], p['FS'], p['T'])[1]
    assert p['FS']/(p['B']-p['b']) < p['T']
    assert p['S2'] >= tight
    beta = p['beta0'] if p['mode'] == 'ERR-only' else p['beta']
    square = p['S2'] if p['mode'] == 'ERR-only' else tight
    slope = p['tp']*(p['K']*p['B']+beta*p['W']*square)
    cap = j.t58.floor((p['eps']-old.errors(p['q'],p['mode'])-DMIN)/slope)
    return cap, slope


def window(p):
    return j.window(p,F(10**6),F(1),F(1),F(2),'total_load',2)


def evaluate(p, spec, direct=DMIN):
    q = dict(p, Dstar=F(direct))
    ka = spec['ka']
    if p['mode'] != 'ERR-only':
        row = j.evaluate(q, window(q), ka, F(spec['vc']), 'direct-fast', F(0),
                         theta=F(spec['theta']) if spec.get('theta') is not None else None,
                         vc_kind=spec['vc_kind'])
        if row['status'] != 'certified_conditional':
            return row
    else:
        h, Q = F(spec['h']), F(spec['Q'])
        initial = q['K']*q['B']*q['Ps']/q['W']
        pair = q['beta0']*min(ka*q['Ps']*q['S2'],q['Ps']*q['S2']+ka*q['Ps']*Q)
        risk = old.errors(q['q'],'ERR-only')+q['Dstar']+initial+pair
        row = dict(spec, risk_upper=risk, risk_slack=q['eps']-risk,
                   status='certified_conditional' if risk <= q['eps'] else 'ERR_pair_risk')
        row.update(err.err_price(q,ka,h,risk))
        hard = q['cp']/q['gm']+q['CX']
        row['quiet_upper'] = min(row['quiet_upper'],hard+(2*q['cp']+q['sigmaX'])/q['T'])
        row['returns_upper'] = min(row['returns_upper'],hard+(2*q['cp']+q['sigmaX'])*1000/(F('.9')*q['T']))
        row['objective'] = max(row['quiet_upper'],row['returns_upper'])
    row.update(Dstar=q['Dstar'], mode=p['mode'], shield=p['shield'], g=p['g'], c=p['c'],
               ka=ka, period_s_upper=q['Ps'], period_l_upper=ka*q['Ps'],
               quota_upper=old.errors(q['q'],q['mode']),
               initial_upper=q['K']*q['B']*q['Ps']/q['W'],
               pair_upper=row['risk_upper']-old.errors(q['q'],q['mode'])-q['Dstar']-q['K']*q['B']*q['Ps']/q['W'],
               peak_upper=q['resource']['peak'], delay_upper_s=q['resource']['delay'],
               resource_pass=q['resource_pass'], risk_relative_slack=row['risk_slack']/q['eps'],
               parameterization='always-S' if ka==1 else 'two-mode', physical_qualification=False)
    return row


def cost_at(witness, direct):
    """Exact affine D-dependence of both prices until the hard-mask cap.

    In the certified range D+R0<=epsilon<1. For whole-quiet p_q is also
    <=epsilon because the long mandatory quiet pair bound need not be <=
    the mission budget; if it exceeds one the hard mask remains the min.
    min(hard,raw affine) covers either saturation without a zeroing trick.
    """
    d = F(direct)-DMIN
    slope = witness['cost_slope']
    quiet = min(witness['hard_whole'],witness['raw_whole_at_min']+slope*d)
    returns = min(witness['hard_return'],witness['raw_return_at_min']+slope*d)
    return quiet, returns, max(quiet,returns)


def pack(p, row):
    ka=row['ka'];cf=p['cp']/p['gm'];T=p['T'];TQ=F('.9')*T
    if p['mode']=='ERR-only':
        # Reconstruct uncapped (10); all D dependence is explicit.
        E=row['DE'];Pl=ka*p['Ps']
        pq0=old.errors(p['q'],'ERR-only',False)+DMIN+p['K']*p['b']*p['Ps']/p['W']+p['beta0']*Pl*p['b']**2*T
        whole=cf/ka+cf*(E*(1+p['K'])/T+E*(p['b']+p['rF']+p['rloss'])+pq0)+(2*p['cp']+p['sigmaX'])/T+p['CX']
        boundary=E*(1000+p['K']+1000*p['B']*(Pl+p['dE']))/TQ
        ret=cf/ka+cf*(boundary+E*(p['b']+p['rF']+p['rloss'])+row['risk_upper'])+(2*p['cp']+p['sigmaX'])*1000/TQ+p['CX']
        spec={k:row[k] for k in ('ka','h','Q','u','v','cells','r0','tau') if k in row}
    else:
        whole=row['quiet_formula_upper'];ret=row['returns_formula_upper']
        # If the original expression already saturated, only the mask can
        # bind: its value is lower than Cs+Cf. Preserve that cap exactly.
        spec={k:row[k] for k in ('ka','vc','vc_kind','theta','k','z')}
    w=dict(mode=p['mode'],shield=p['shield'],g=p['g'],spec=spec,
           risk_intercept=row['risk_upper']-DMIN,D_cert=p['eps']-row['risk_upper']+DMIN,
           cost_slope=cf,raw_whole_at_min=whole,raw_return_at_min=ret,
           hard_whole=cf+(2*p['cp']+p['sigmaX'])/T+p['CX'],
           hard_return=cf+(2*p['cp']+p['sigmaX'])*1000/TQ+p['CX'])
    assert cost_at(w,DMIN)[2]==max(min(row['quiet_upper'],w['hard_whole']),min(row['returns_upper'],w['hard_return']))
    # In this family the hard mask is >1%, so the two uncapped affine
    # inequalities are necessary and sufficient for this *upper* <=1%.
    assert min(w['hard_whole'],w['hard_return'])>LIMIT
    w['D_cost']=min(w['D_cert'],DMIN+(LIMIT-max(whole,ret))/cf)
    return w


def dominates(a,b):
    # Same g -> exactly equal slopes and mask caps. Both prices dominated.
    return (a['D_cert']>=b['D_cert'] and a['raw_whole_at_min']<=b['raw_whole_at_min']
            and a['raw_return_at_min']<=b['raw_return_at_min'])


def frontier_add(frontier,w):
    if any(dominates(a,w) for a in frontier):return False
    frontier[:]=[a for a in frontier if not dominates(w,a)]
    frontier.append(w)
    return True


def monitor_family(p, log):
    """Complete finite vc/ka family at one g; reject before expensive LOW."""
    m=window(p);de,dm=j.strips(p,m,F(0),'direct-fast')
    for theta in map(F,old.FAMILY['vc_fraction_of_gap_qR_to_ve']):
        vc=m['qR']+theta*(F('.001')-m['qR'])
        cap=j.max_ka(p,vc)
        log['risk_rejected_old_vc']+=(4095-cap+1)//2 if cap else 2048
        mass,upper=j.fast_exposure(vc,F(0),m['wm'],m['hF_max'])
        th=j.safe_threshold(mass,m['aM'],m['H'])
        if th['k']<0:
            log['LOW_rejected_old_vc']+=(cap+1)//2
            continue
        pm=j.poisson_chernoff(m['mu'],th['k'])
        for ka in range(1,cap+1,2):
            rb=j.pair_bound(p,ka,vc)
            pr=j.price(p,m,ka,rb['risk_upper'],de,dm,pm)
            yield dict(ka=ka,vc=vc,vc_kind='old',theta=theta,**th,**rb,**pr)
    for ka in range(1,4096,2):
        vf=j.flat_v(p,ka)
        if vf<=p['b']:
            log['vc_flat_outside']+=2*((4095-ka)//2+1)
            break
        for kind,vc in [('mid_flat',(p['b']+vf)/2),('flat',vf)]:
            rb=j.pair_bound(p,ka,vc)
            if rb['risk_upper']>p['eps']:
                log['risk_rejected_flat']+=1
                continue
            row=j.evaluate(p,m,ka,vc,'direct-fast',F(0),vc_kind=kind)
            if row['status']!='certified_conditional':log[row['status']]+=1
            else:yield row


def compile_g(p):
    counts=Counter();front=[];fallback=[]
    if not p['resource_pass']:
        return [],[],dict(resource_rejected=1)
    if p['mode']=='ERR-only':
        rows,_=err.err_scan(p)
        iterator=(r for r in rows if r['status']=='certified_conditional')
        for r in rows:
            if r['status']!='certified_conditional':counts[r['status']]+=1
    else:iterator=monitor_family(p,counts)
    for row in iterator:
        counts['accepted_candidates']+=1
        w=pack(p,row)
        which=fallback if row['ka']==1 else front
        if not frontier_add(which,w):counts['dominated_at_same_g']+=1
    counts.update(frontier=len(front),always_S_frontier=len(fallback))
    return front,fallback,dict(counts)


def best_at(frontier,direct,reserve=F(0)):
    good=(w for w in frontier if direct+reserve<=w['D_cert'])
    return min(good,key=lambda w:(cost_at(w,direct)[2],w['g'],w['spec']['ka'],str(w['spec'])),default=None)


def bracket(value):
    if value is None or value<DMIN:return None
    lo=j.t58.floor(value/TOL)*TOL
    hi=j.t58.ceil(value/TOL)*TOL
    return dict(lower=lo,upper=hi,width=hi-lo,exact_family_bound=value)


def fixed(p,direct):
    # All integer periods, exact T52 rarity rather than a coarse M grid.
    t=j.t58;T=p['T'];W=p['W'];s2=t.rarity(p['B'],p['b'],p['FS'],T)[1]
    e=sum(F(p['q'][k]) for k in ('rho0','delta_exec','delta_svc'))
    slope=p['beta']*s2+p['K']*p['B']/W
    M=max(0,min(t.floor(T/p['tp']),t.floor((p['eps']-e-direct)/(p['tp']*slope))))
    out=dict(Dstar=direct,shield=p['shield'],quota_upper=e,square_upper=s2,
             M=M,certificate_range_is_complete=True,monitor_cost=F(0),
             physical_occupied_lower_s=None,occupied_contract='whole 100-tick block occupied; conditional')
    if M<1:return out|dict(status='no_risk_candidate',resource_pass=False)
    # Saturating initial branch cannot admit a larger period here: even
    # pairs alone at its switch exceed epsilon. Thus the linear interval
    # is the full T52 certificate, not only a selected sufficient branch.
    exposure=t.rarity(p['B'],p['b'],p['FS'],T)[0]
    assert p['beta']*s2*exposure/p['B']>p['eps']
    r=t.Resource(W=W//2,c=2*p['cp'],H=T,h=F('.001'),tax=F(1),peak=F('.8'),
                 delay=F('3e-6')/(1+p['margin']),sigma=F(p['cfg']['resources']['application_sigma_s']),
                 u=F(p['cfg']['resources']['application_rate']),g=F(p['cfg']['resources']['application_max_request_s']),
                 tick=F('1e-9'),clock_error=F('.00001'))
    rv=t.resources(r,M)
    risk=e+direct+M*p['tp']*slope
    next_risk=e+direct+(M+1)*p['tp']*slope
    assert risk<=p['eps'] and next_risk>p['eps']
    minimum=t.first_resource_tick(r,1,M)
    return out|dict(status='certified_conditional' if t.resource_ok(rv) else 'resource_rejected',
        period_upper_s=M*p['tp'],risk_upper=risk,next_risk_upper=next_risk,
        risk_slack=p['eps']-risk,M_resource_min=minimum,resource_pass=t.resource_ok(rv),
        cost_lower=F(W*p['c'],M)-2*p['cp']/T,cost_upper=F(W*p['c'],M)+2*p['cp']/T,
        resource_tax_upper=rv['tax_upper'],peak_upper=rv['peak_upper'],delay_upper_s=rv['delay_upper'])


def necessary_constant(p):
    # Existing accepted witness, independent of the chosen upper D*;
    # the same zero-direct singleton witness remains in every larger class.
    t=j.t58;T=p['T'];W=p['W'];L=F(115776)
    tau=W*p['cm']/(LIMIT+2*W*p['cp']/T)
    J=t.floor(L/tau)+2;ell=(L-J*p['cp'])/(4*J);x=p['B']*ell/W
    expo=2*W*J*F(p['n']-1,2*p['n'])*x*x*t.exp_neg(x)[0]
    return dict(shield=p['shield'],tau_min_arbitrary_phase=tau,J=J,
                risk_lower=t.poisson_event(expo)[0]-F(p['q']['delta_exec']),
                scope='deterministic constant full-U with whole-block occupancy and tax<=1%; not other services or mixtures',
                direct_witness=0,physical_occupied_lower_s=None)
