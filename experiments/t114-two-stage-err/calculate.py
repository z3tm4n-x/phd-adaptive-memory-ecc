"""T114 finite deterministic substitutions; output on stdout only.

All certificates use rational arithmetic and directed Decimal intervals.
Float is confined to preview candidate selection, never admission.
"""
from fractions import Fraction as F
from pathlib import Path
from functools import lru_cache
import importlib.util
import json
import math

from intervals import I, exposure

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CFG = json.loads((HERE/'config.json').read_text())
spec = importlib.util.spec_from_file_location('accepted_t110', ROOT/'experiments/t110-err-write-service/calculate.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
TM, TP, JIT = old.TM, old.TP, old.JIT
T = old.times()


def timer(x):
    ticks = 4*old.ceil((x+JIT)/(4*TM))
    return dict(ticks=ticks, lower=ticks*TM-JIT, upper=ticks*TP+JIT)


def calendar(p, profile, ka, growth):
    g = profile['g_ticks']; m = CFG['calendar']['batch']; c = CFG['calendar']['c_ticks']
    ps = p['W']*g*TP; pl = ka*ps
    # First alias: E read/turnaround/write sequence, replacing writeback by
    # requested data even at ERR=0; second alias: standalone 68-cycle write.
    # Global alias lock spans both blocks; sum the published upper bounds.
    app = T['E']+F('68.500680e-9') if profile['observed_writes'] else T['app']
    charge = 240 if profile['observed_writes'] else 208
    frame = m*g*TP; fm = m*g*TM
    tau = pl+T['d']+app+F(CFG['timing_requirements']['ERR_or_loss_to_rule_s'])+2*JIT
    lag = pl+CFG['calendar']['gate_ticks']*TP+2*JIT
    wt, ht = timer(F(growth['w_s'])), timer(F(growth['h_s']))
    # New predictable thinning excludes only the currently protected word.
    # It is justified in appendix B, including Palm insertion after old bands.
    # Keep the discarded whole-array blackout for an addressed comparison.
    discarded_blackout = min(F(1), (charge*TP+JIT)/fm) if profile['observed_writes'] else F(0)
    blackout = F(0)
    return dict(g=g, ka=ka, Ps=ps, Ps_min=p['W']*g*TM, Pl=pl, frame=frame, frame_min=fm,
                app=app, app_charge=charge, tau=tau, lag=lag, w=wt['lower'], h=ht['lower'],
                w_upper=wt['upper'], h_upper=ht['upper'], w_ticks=wt['ticks'], h_ticks=ht['ticks'],
                blackout=blackout, discarded_blackout=discarded_blackout,
                blackout_edge=2*frame*p['B'] if blackout else F(0),
                phi=max(F(0), F(profile['a_parent'])-F(1,p['W'])))


def bands(c, stages=2):
    tau, w, h = c['tau'], c['w'], c['h']
    if not h >= w > tau:
        raise ValueError('require h >= w > tau')
    if stages == 1:
        return [(tau, h, 0)]
    result = [(tau, w, 0)]
    x = w
    while x < h:
        y = min(h, x+w-tau)
        result.append((x, y, 1)); x = y
    return result


def low_upper(q, rho, c, stages=2):
    r = I(1); width = F(0)
    for a,b,allowed in bands(c,stages):
        integ = exposure(q,a+c['lag'],b+c['lag'],rho)
        mu = max(F(0), c['phi']*((1-c['blackout'])*F(integ.lo)-c['blackout_edge']))
        r = r*(I(0)-I(mu)).exp()*(I(1)+I(mu) if allowed else I(1))
        width = max(width,F(integ.hi)-F(integ.lo))
    return min(F(1),F(r.hi)), width


def majorant(p,c,rho,stages):
    b,B=p['b'],p['B']; ps,pl=c['Ps'],c['Pl']
    if c['ka'] == 1:
        return dict(integral=ps*p['S2exact'],u=None,v=None,cells=0,min_slack=F(0),interval_width=F(0),active=None)
    xs=sorted(set([b,F('.001'),B]+[B*i/1024 for i in range(1,1024) if B*i/1024>b])); cache={}; widest=F(0)
    def coefficient(lo,hi):
        nonlocal widest
        if (lo,hi) not in cache:
            r,width=low_upper(lo,rho,c,stages); widest=max(widest,width)
            cache[(lo,hi)]=ps+pl*r
        return cache[(lo,hi)]
    for iteration in range(CFG['numerical_contract']['refinements']):
        cells=[(lo,hi,coefficient(lo,hi)) for lo,hi in zip(xs[:-1],xs[1:])]
        base=(ps+pl)*b*b; candidates=[];active=set()
        for k in CFG['numerical_contract']['u_multipliers']:
            u=k*base
            # Since u>=A*b*b, (A*q*q-u)/(q-b) is increasing for q>b.
            # The right endpoint denominator is therefore SAFE, not a heuristic.
            v,al,ah=max((max(F(0),(a*hi*hi-u)/(hi-b)),lo,hi) for lo,hi,a in cells)
            active.add((al,ah))
            slack=min(u+v*(q-b)-a*q*q for lo,hi,a in cells for q in (lo,hi))
            assert slack>=0
            candidates.append(dict(integral=min(pl*p['S2exact'],u*p['T']+v*p['FS']),u=u,v=v,
                cells=len(cells),min_slack=slack,active=[al,ah],interval_width=widest,multiplier=k))
        if candidates: chosen=min(candidates,key=lambda z:(z['integral'],z['multiplier']))
        if iteration==CFG['numerical_contract']['refinements']-1:
            if not candidates: raise ValueError('no finite affine certificate')
            return chosen
        xs=sorted(set(xs+[(lo+hi)/2 for lo,hi in active]))
    raise AssertionError('finite loop')


def resource(c, frame_max=None, frame_min=None):
    fmax=c['frame'] if frame_max is None else frame_max
    fmin=c['frame_min'] if frame_min is None else frame_min
    h=F('.001');dl=F('3e-6');cx=F('1e-4');sx=F('209e-9');margin=F('1.1')
    mem=8*T['E']*(h/fmin+2)/h
    x=cx+(sx+cx*dl)/h
    fixed=T['req']+JIT+c['app']+T['reply']+F('1e-7')
    bmax=(dl/margin-fixed)/fmax
    # Joint arrivals include application reads, observed writes and X commands.
    rate_peak=(F('.8')-mem-x-c['app']/h)/(c['app']*(h+dl)/h)
    return dict(peak_control_no_application=mem+x,all_bus_peak_at_sigma1_rate0=mem+x+c['app']/h,
                rate_max_sigma1=min(1/fmax,rate_peak),burst_max_latency=bmax,frame_max=fmax,
                app_margin_slack=c['app_charge']*TM-JIT-margin*c['app'],
                placement_slack=fmin-8*164*TP-JIT-(c['app_charge']*TP+JIT),
                gate_slack=320*TM-JIT-margin*(c['app']+T['command']),
                one_request_delay=margin*(fixed+fmax))


def price(p,c,profile,risk,stages):
    pc=CFG['price_contract'];Tlife=p['T'];b=p['b'];tau=c['tau'];w=c['w_upper'];h=c['h_upper']
    # Grid occupation enclosure of each FAST interval adds <=2 frames.
    edge=2*c['frame']+CFG['calendar']['gate_ticks']*TP+2*JIT
    ww=w+tau+edge;hh=h+tau+edge
    # One parent can own multiple ERR flags; extra flags are bounded, not Poisson.
    cluster=F(profile['cluster_rate_ratio']); false=F(pc['false_flag_rate_max'])
    quiet_fast=(hh*b if stages==1 else ww*b+hh*b*b*(w+tau)+hh*cluster*b)
    # Every solar/false/cluster parent: union of all its delayed flags and
    # all later pair-confirmations lies in one interval of length h+w+2*tau.
    L=(h+w+2*tau+edge) if stages==2 else hh
    # Sharper than charging h+w to every solar parent: all pair confirmations
    # with a later solar parent fit its h+tau strip. Only later BACKGROUND
    # parents extend it; their factorial mean is <=b*(w+tau)*FS.
    solar=hh*(1+b*(w+tau))*p['FS']/Tlife if stages==2 else hh*p['FS']/Tlife
    outage=F(pc['outage_fraction_max'])+F(pc['recoveries_max'])*(h+tau+edge)/Tlife
    startup=(h+tau+edge+p['K0']*L)/Tlife
    # A hit inside an operation can be observed there and again in the next
    # epoch under the weak E obligation. One extra flag per active-word hit;
    # its predictable rate is <=nu/W. A completed E is not silently clean.
    aperture_extra_rate=p['F']/(p['W']*Tlife)
    mission_fast=min(F(1),quiet_fast+solar+L*(false+aperture_extra_rate)+outage+startup)
    tq=F(pc['quiet_fraction'])*Tlife;kq=pc['quiet_components']
    # Charge complete history at each quiet boundary, not a clean start there.
    boundary=kq*L+p['K0']*L
    quiet_total=min(F(1),quiet_fast+L*(false+b/p['W'])+(boundary+outage*Tlife)/tq)
    cfR=T['R']/(c['g']*TM);cfE=T['E']/(c['g']*TM)
    bad=min(F(1),risk);base=cfR/c['ka'];X=F(pc['X_rate'])+kq*(F(pc['X_burst_s'])+F(pc['X_rate'])*F('3e-6'))/tq
    bus_edges=4*CFG['calendar']['batch']*T['E']*kq/tq
    def cost(frac,rate):
        # Pre-observation of application writes is charged separately by rate.
        cap=cfR+(T['E']-T['R'])*min(1/(c['g']*TM),rate+bad/(c['g']*TM))
        return min(cap,base+cfR*frac+(T['E']-T['R'])*rate+cfE*bad)+X+bus_edges
    mission=cost(mission_fast,p['F']/Tlife+aperture_extra_rate+p['K0']/Tlife)
    quiet=cost(quiet_total,b*(1+F(1,p['W']))+(p['K0']+kq*p['B']*tau*(1+F(1,p['W'])))/tq)
    return dict(mission_upper_intercept=mission,quiet_upper_intercept=quiet,
        mission_fast_fraction=mission_fast,quiet_fast_fraction=quiet_total,base_read=base,
        background_fast=quiet_fast,solar_fast=solar,loss_fast=outage,global_bad_probability=bad,
        aperture_extra_flag_rate_upper=aperture_extra_rate,aperture_extra_fast_fraction=L*aperture_extra_rate,
        global_bad_price=cfE*bad,bus_edges=bus_edges,write_observation_price_per_request=T['R'] if profile['observed_writes'] else F(0),
        total_bus_application_write_per_request=c['app'],total_bus_application_read_per_request=T['app'],
        price_scope='upper uniform in declared class; add admitted offered-work rates; not a history estimate')


def compute(p,profile,growth,ka,stages=2):
    c=calendar(p,profile,ka,growth);rho=F(growth['rho_per_s'])
    ma=majorant(p,c,rho,stages);beta0=F(1,2*p['W'])
    cp=dict(p,beta=beta0)
    cross=old.cross(cp,c['Ps_min'],c['Pl'],ka,p['S2exact'],T['d'])
    initial=p['K0']*p['B']*(c['Ps']+T['d'])/p['W']
    rb=p['errors']+p['D']+initial+beta0*ma['integral']+cross['X']
    re=resource(c);pr=price(p,c,profile,rb,stages)
    ok=rb<=p['eps'] and re['placement_slack']>=0 and re['app_margin_slack']>=0 and re['gate_slack']>=0 and re['rate_max_sigma1']>=0 and re['burst_max_latency']>=1
    lb=old.lower_class(p)
    return dict(shield=p['shield'],growth=growth['name'],rho=rho,profile=profile['name'],stages=stages,calendar=c,
        majorant=ma,pair_risk=beta0*ma['integral'],cross=cross,initial=initial,risk_upper=rb,risk_slack=p['eps']-rb,
        risk_pass=rb<=p['eps'],resources=re,certified=ok,price=pr,
        class_price_lower=lb['read_price_lower'],gain_lower=lb['read_price_lower']/pr['mission_upper_intercept'] if ok else None,
        required_price_for_10x=lb['read_price_lower']/10,
        tenfold_pass=ok and 10*pr['mission_upper_intercept']<=lb['read_price_lower'],
        quiet_one_percent_pass=ok and pr['quiet_upper_intercept']<=F('.01'))


def preview(p,profile,growth,ka,stages=2):
    """Uncertified scalar candidate selector, printed nowhere as a result."""
    c=calendar(p,profile,ka,growth);rho=float(F(growth['rho_per_s']));l=.001
    def A(q,t):
        if q<=l:
            v=min(t,q/(rho*l));return q*v-rho*l*v*v/2
        te=math.log(q/l)/rho;v1=min(t,te);v2=max(0,min(t-te,1/rho))
        return q/rho*(-math.expm1(-rho*v1))+l*(v2-rho*v2*v2/2)
    def r(q):
        out=1.
        for a,b,k in bands(c,stages):
            v=A(q,float(b+c['lag']))-A(q,float(a+c['lag']))
            mu=max(0,float(c['phi'])*((1-float(c['blackout']))*v-float(c['blackout_edge'])))
            out*=math.exp(-mu)*(1+mu if k else 1)
        return out
    ps,pl,b,B=map(float,(c['Ps'],c['Pl'],p['b'],p['B']))
    integ=pl*float(p['S2exact'])
    for k in (1,2,4,16):
        u=k*b*b*(ps+pl)
        v=max(0,max((q*q*(ps+pl*r(q))-u)/(q-b) for q in [b+(B-b)*i/512 for i in range(1,513)]))
        integ=min(integ,u*float(p['T'])+v*float(p['FS']))
    if ka==1:integ=ps*float(p['S2exact'])
    cp=dict(p,beta=F(1,2*p['W']))
    return float(p['errors']+p['D']+p['K0']*p['B']*c['Ps']/p['W']+old.cross(cp,c['Ps_min'],c['Pl'],ka,p['S2exact'],T['d'])['X'])+integ/(2*p['W'])


def preview_table():
    p=old.environment(old.HANDOFF['rows'][0])
    rows=[]
    for profile in CFG['profiles']:
        for gr in CFG['growth_classes']:
            for stages in (2,1):
                passing=[k for k in range(1,64,2) if preview(p,profile,gr,k,stages)<=float(p['eps'])]
                ka=max(passing,default=1);rows.append([profile['name'],gr['name'],stages,ka,preview(p,profile,gr,ka,stages)])
    return rows


if __name__=='__main__':
    print(json.dumps(preview_table(),indent=2))
