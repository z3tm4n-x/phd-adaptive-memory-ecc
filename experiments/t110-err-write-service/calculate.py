"""Exact T110 substitutions. All decisions use fractions, no simulations.

The input engineering package and accepted scientific files are read-only.
Symbols and proofs: theory/t110-err-write-service[-appendix].md.
"""
from fractions import Fraction as F
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CFG = json.loads((HERE / 'inputs.json').read_text())
HANDOFF = json.loads((ROOT / CFG['input']).read_text())
TM, TP, JIT = F('0.99999e-9'), F('1.00001e-9'), F('0.5e-9')
MARGIN = F(11, 10)


def floor(x):
    return x.numerator // x.denominator


def ceil(x):
    return -floor(-x)


def ticks_up(x, margin=F(1), q=4):
    return q * ceil((margin*x+JIT)/(q*TM))


def text_number(x, up=True, digits=12):
    x = F(x); scale = 10**digits
    i = ceil(x*scale) if up else floor(x*scale)
    sign = '-' if i < 0 else ''; i = abs(i)
    return f'{sign}{i//scale}.{i%scale:0{digits}d}'


def serial(value):
    if isinstance(value, F): return str(value)
    if isinstance(value, dict): return {k: serial(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [serial(v) for v in value]
    return value


def environment(row):
    e = row['environment']
    p = {k: F(e[k]) for k in ('T', 'eps', 'b', 'B', 'FS', 'S2', 'beta')}
    p.update(W=e['W'], n=e['n'], K0=row['quotas']['K0'], D=F(row['Dstar']), shield=row['shield'])
    p['errors'] = sum(F(row['quotas'][k]) for k in ('rho0', 'delta_exec', 'delta_svc', 'delta_E', 'delta_M', 'alpha_M'))
    p['fixed_errors'] = sum(F(row['quotas'][k]) for k in ('rho0', 'delta_exec', 'delta_svc'))
    p['F'] = min(p['B']*p['T'], p['b']*p['T']+p['FS'])
    p['S2exact'] = min(p['B']**2*p['T'], p['B']*p['F'], p['b']**2*p['T']+(p['B']+p['b'])*p['FS'])
    return p


def times():
    t = HANDOFF['proposed_service_timing']
    ns = lambda x: F(x)/10**9
    R, E = [ns(t['upper_ns'][k]) for k in ('read_no_ERR', 'read_ERR_repair')]
    req, reply, command = [ns(t['outside_lock_upper_ns'][k]) for k in ('request_CDC_validation', 'response_CDC', 'command_receive_validate_shadow')]
    return dict(R=R, E=E, d=E, r_lower=92*TM-JIT, e_lower=148*TM-JIT,
                app=ns(t['upper_ns']['application_read32_atomic_two_aliases']),
                inline32=ns(t['upper_ns']['application_read32_with_inline_repairs']),
                req=req, reply=reply, command=command)


def cross(p, Ps_lower, Pl_upper, multiplicity, square, d):
    """All potential short windows; preceding intervals of length ka*Ps.

    X1 follows 2xy<=x²+y²; X2 makes the zero-aperture limit explicit.
    For constant E multiplicity=1, Ps_lower is its period lower bound.
    """
    if d == 0: return dict(X=F(0), X1=F(0), X2=F(0))
    beta, W = p['beta'], p['W']; eta = 2*beta/W
    x1 = beta*(multiplicity*d+Pl_upper/W)*square
    v = 2*beta*d*(p['T']/Ps_lower+1)
    x2 = min(p['B']*Pl_upper, p['F'])*min(p['B']*v, p['b']*v+eta*p['FS'], eta*p['F'])
    return dict(X=min(x1, x2), X1=x1, X2=x2)


def risk(p, g, ka, vc):
    W = p['W']; ps, pl = W*g*TP, W*g*ka*TP
    u = (ps+pl)*p['b']**2
    v = max((ps+pl)*(vc+p['b']), (ps*p['B']**2-u)/(p['B']-p['b']), F(0))
    Vc = min(vc*vc*p['T'], p['b']**2*p['T']+(vc+p['b'])*p['FS'])
    q = min(ps*p['S2']+pl*Vc, pl*p['S2'], u*p['T']+v*p['FS'])
    x = cross(p, W*g*TM, pl, ka, p['S2'], times()['d'])
    init = p['K0']*p['B']*ps/W
    upper = p['errors']+p['D']+init+p['beta']*q+x['X']
    return dict(Ps=ps, Ps_lower=W*g*TM, Pl=pl, pair_integral=q, initial=init,
                ordinary_pairs=p['beta']*q, **x, upper=upper, slack=p['eps']-upper, pass_risk=upper<=p['eps'])


def monitor(p, g):
    c = CFG['calendar']; m = CFG['monitor']; t = times()
    wp = m['window_ticks']*TP+JIT; wm = m['window_ticks']*TM-JIT
    dm, dp = m['stride_ticks']*TM, m['stride_ticks']*TP
    dt = ticks_up(F(m['post_window_required_s']), MARGIN)
    delivery = dt*TP+JIT
    gap = (c['batch']*g-(c['batch']-1)*c['c_ticks'])*TP+JIT
    gate = c['gate_ticks']*TP+JIT; ps = p['W']*g*TP
    required = wp+delivery+dp+gate+gap+t['d']+ps+2*JIT+8*TP
    lease_ticks = ticks_up(required, MARGIN)
    lease = lease_ticks*TP+JIT
    # vc=l: exact linear branch of the fast backward cone over the whole window.
    vc, rho = F(m['vc_per_s']), F('0.048')
    lag = lease+2*JIT
    mass = vc*wm*(1-rho*(lag-wm/2))
    assert vc == F('.001') and 0 < wm < lag < 1/rho
    phi, H = F(m['phi_lower']), m['H']
    k = floor(10**6*phi*mass-H)
    count = ceil((p['T']+2*JIT)/dm)+2
    alpha = count*F(3,8)**H  # e^-1 < 3/8, proven by finite Taylor terms.
    mu = wp*(10**6*p['b']+F('.001'))
    exponent = floor(k+1-F(7,4)*mu)  # e-1 < 7/4; Chernoff at z=1.
    tail = min(F(1), F(3,8)**max(0, exponent))
    hold_ticks = ticks_up(F(1)); hold = hold_ticks*TP+JIT
    frame = c['batch']*g*TP
    edge = 2*gate+gap+t['d']+2*frame+2*JIT+8*TP
    de_req = hold+F(m['ERR_delay_required_s'])+edge
    dm_req = 2*wp+2*dp+delivery+hold+2*ps+edge
    return dict(k=k, H=H, J=count, z=1, phi_lower=phi, mass_lower=mass,
                test_slack=10**6*phi*mass-k-H, next_test_slack=10**6*phi*mass-(k+1)-H,
                global_tail_upper=alpha, quiet_mean_upper=mu, quiet_tail_upper=tail,
                price_exponent_lower=exponent, window_min=wm, window_max=wp,
                stride_min=dm, stride_max=dp, delivery_ticks=dt, delivery_upper=delivery,
                lease_ticks=lease_ticks, lease_upper=lease, lease_required=required,
                lease_slack=lease_ticks*TM-JIT-MARGIN*required,
                post_window_physical_path_required=F(m['post_window_required_s']),
                pre_mailbox_path_required=F(m['post_window_required_s'])-t['command'],
                DE_required=de_req, DM_required=dm_req,
                DE=F(m['DE_s']), DM=F(m['DM_s']), hold_ticks=hold_ticks,
                first_reaction_upper=gate+gap+t['d'],
                all_words_reaction_upper=gate+gap+t['d']+ps)


def resources(g, frame_min=None, frame_max=None):
    c = CFG['calendar']; t = times(); m = c['batch']; h=F('.001')
    fmin = m*g*TM if frame_min is None else frame_min
    fmax = m*g*TP if frame_max is None else frame_max
    a = CFG['resource_allocations']; cx, sigma, bp = map(F, [a['X_rate'], a['X_burst_s'], a['response_backpressure_required_s']])
    # At most h/F+2 frames intersect any window; all visits may have ERR.
    peak_mem = m*t['E']*(h/fmin+2)/h
    peak_x = (sigma+cx*(h+F('3e-6')))/h
    slot_free = fmin-m*c['c_ticks']*TP-JIT
    app_charge = c['application_charge_ticks']*TP+JIT
    margin_available = c['application_charge_ticks']*TM-JIT-MARGIN*t['app']
    fixed_delay = t['req']+t['app']+t['reply']+bp+JIT
    bcap = (F('3e-6')/MARGIN-fixed_delay)/fmax
    one_delay = MARGIN*(fixed_delay+fmax)
    return dict(frame_min=fmin, frame_max=fmax, slot_free_lower=slot_free,
                application_charge_upper=app_charge, placement_slack=slot_free-app_charge,
                app_margin_slack=margin_available,
                control_margin_slack=c['c_ticks']*TM-JIT-MARGIN*t['E'],
                read_margin_slack=c['read_charge_ticks']*TM-JIT-MARGIN*t['R'],
                gate_slack=c['gate_ticks']*TM-JIT-MARGIN*(t['app']+t['command']),
                peak_memory_upper=peak_mem, peak_X_upper=peak_x, peak_upper=peak_mem+peak_x,
                reserved_fraction=m*c['c_ticks']*TP/fmin,
                joint_rate_cap_per_s=1/fmax, joint_burst_cap=bcap,
                backpressure_allocation=bp, one_packet_delay_with_margin=one_delay,
                inline32_placement=False if MARGIN*t['inline32']+JIT>slot_free else True,
                pass_resources=(slot_free>=app_charge and peak_mem+peak_x<=F('.8') and bcap>=1 and margin_available>=0))


def price(p, rb, mon, g, ka, returns=True, reserve_charge=False):
    t=times(); c=CFG['calendar']; a=CFG['resource_allocations']
    tq=F(CFG['price']['TQ_fraction'])*p['T'] if returns else p['T']
    kq=CFG['price']['KQ'] if returns else 1
    # With reserve_charge=True the unused 10% reserve is also charged for diagnostics.
    r=c['read_charge_ticks']*TP+JIT if reserve_charge else t['R']
    e=c['c_ticks']*TP+JIT if reserve_charge else t['E']
    cfR=r/(g*TM); cfE=e/(g*TM); de,dm=mon['DE'],mon['DM']
    dE=F(CFG['monitor']['ERR_delay_required_s'])
    tokens=p['K0']+kq*p['B']*(rb['Pl']+t['d']) if returns else F(p['K0'])
    delayed_tokens=p['K0']+kq*p['B']*(rb['Pl']+t['d']+dE) if returns else F(p['K0'])
    fq=1/mon['stride_min']+2*kq*mon['window_max']/(mon['stride_min']*tq)+2*F(kq)/tq if returns else F(mon['J'])/tq
    frac=(dm*kq+de*delayed_tokens)/tq+de*(p['b']+F('2e-6'))+dm*fq*(mon['quiet_tail_upper']+F('1e-9'))
    if returns:
        bad=min(F(1),rb['upper'])
    else:
        quiet=dict(p,B=p['b'],FS=F(0),F=p['b']*p['T'])
        crossq=cross(quiet, rb['Ps_lower'], rb['Pl'], ka, p['b']**2*p['T'], t['d'])['X']
        bad=min(F(1),p['errors']+p['D']+p['K0']*p['b']*rb['Ps']/p['W']+p['beta']*rb['Pl']*p['b']**2*p['T']+crossq)
    write_rate=tokens/tq+p['b']+F('1e-6')
    edge=4*c['batch']*e*kq/tq
    xprice=F(a['X_rate'])+kq*(F(a['X_burst_s'])+F(a['X_rate'])*F('3e-6'))/tq
    base=cfR/ka
    raw=base+cfR*min(F(1),frac)+(e-r)*write_rate+cfE*bad+edge+xprice
    cap=cfR+(e-r)*min(1/(g*TM),write_rate+bad/(g*TM))+edge+xprice
    value=min(raw,cap)
    return dict(upper=value, percent_upper=text_number(100*value), raw=raw, all_short_cap=cap,
                base_read=base, optional_read=cfR*min(F(1),frac),
                good_writes=(e-r)*write_rate, global_bad=cfE*bad,
                bad_probability=bad, edges=edge, X=xprice,
                quiet_fraction_extra=frac, token_rate_upper=write_rate,
                outage_slope=cfE, outage_fraction_sufficient=max(F(0),(F('.01')-value)/cfE),
                charge_includes_unused_reserve=reserve_charge)


def constant(p):
    t=times(); c=CFG['calendar']; N=p['W']//c['batch']
    def bound(M):
        period=M*TP
        x=cross(p,M*TM,period,1,p['S2exact'],t['d'])
        return p['fixed_errors']+p['D']+p['K0']*p['B']*period/p['W']+p['beta']*period*p['S2exact']+x['X']
    # Every term is nondecreasing here: P<F/B and the X2 products are affine.
    hi=ceil((p['eps']-p['D']-p['fixed_errors'])/(4*TP*(p['beta']*p['S2exact']+p['K0']*p['B']/p['W'])))+1
    lo=0
    while hi-lo>1:
        mid=(hi+lo)//2
        if bound(4*mid)<=p['eps']: lo=mid
        else: hi=mid
    M=4*lo; P=M*TP
    amin=4*(M//(4*N)); amax=amin+(4 if M%(4*N) else 0)
    res=resources(F(M,p['W']),amin*TM,amax*TP)
    tq=F(CFG['price']['TQ_fraction'])*p['T']; kq=CFG['price']['KQ']
    # Read floor / rare-write upper; no monitor tax is charged to the competitor.
    rate=p['K0']/tq+kq*p['B']*(P+t['d'])/tq+p['b']
    bad=min(F(1),bound(M))
    reads=p['W']*t['R']/(M*TM)
    # A complete phase period has N frames; floor placement differs by <4 ticks.
    upper=reads+(t['E']-t['R'])*(rate+p['W']*bad/(M*TM))+4*c['batch']*t['E']*kq/tq
    lower=p['W']*t['r_lower']/P-2*p['W']*t['R']*kq/tq
    return dict(M_ticks=M, period_upper=P, period_lower=M*TM,
                risk_upper=bound(M), next_risk_upper=bound(M+4),
                certificate_max_on_core_grid=True, optimal_period_claimed=False,
                risk_only_candidate=True, resources=res, feasible=res['pass_resources'],
                cost_lower=lower, cost_upper=upper,
                cost_percent_lower=text_number(100*lower,False),cost_percent_upper=text_number(100*upper))


def lower_class(p):
    t=times(); T,B,W=p['T'],p['B'],p['W'];L=p['FS']/(B-p['b'])
    p1=F(CFG['constant_lower']['split_s']);mesh=F(CFG['constant_lower']['proof_mesh_s']);de=F('1e-6')
    def z(P):
        return p['beta']*B*B*(L-2*p1)*P*(1-t['E']/P)**2*(1-B*p1/W)
    def lb(P):
        zz=z(P);return zz/(1+zz)-de
    lo,hi=floor(t['E']/mesh)+1,floor(p1/mesh)
    while hi-lo>1:
        mid=(lo+hi)//2
        if lb(mid*mesh)>p['eps']: hi=mid
        else: lo=mid
    p0=hi*mesh;J=floor(L/p1)+2;ell=(L-J*t['E'])/(4*J);x=B*ell/W
    zl=2*W*J*F(p['n']-1,2*p['n'])*x*x*(1-x)
    far=zl/(1+zl)-de
    tq=F(CFG['price']['TQ_fraction'])*T;kq=CFG['price']['KQ']
    cost=W*t['r_lower']/p0-2*W*t['R']*kq/tq
    # All-ERR is an admissible finite trace. Peak<=.8 implies its long average<=.8+2h/T.
    # Omit the first full period (unknown initial errors); two more phase edges are removed.
    all_err_lower=W*t['e_lower']/p0-3*W*t['E']/T
    return dict(P0=p0, risk_lower_at_P0=lb(p0), predecessor_lower=lb(p0-mesh),
                large_period_risk_lower=far, read_price_lower=cost,
                read_percent_lower=text_number(100*cost,False),
                all_ERR_mean_lower=all_err_lower,
                fixed_class_resource_excluded=(all_err_lower>F('.8')+2*F('.001')/T),
                plateau_length=L, removed_window=t['E'])


def calculate():
    c=CFG['calendar'];g,ka=c['g_ticks'],c['ka']; rows=[]
    for source in HANDOFF['rows']:
        p=environment(source);rb=risk(p,g,ka,F(CFG['monitor']['vc_per_s']))
        mon=monitor(p,g);res=resources(g);cost=price(p,rb,mon,g,ka)
        con=constant(p);lb=lower_class(p)
        common_frame=max(res['frame_max'],con['resources']['frame_max'])
        t=times();bp=F(CFG['resource_allocations']['response_backpressure_required_s'])
        burst=(F('3e-6')/MARGIN-t['req']-t['app']-t['reply']-bp-JIT)/common_frame
        gain=lb['read_price_lower']/cost['upper']
        # Risk floor of this affine certificate, before any price or resource test.
        slope=TP*(p['K0']*p['B']+p['beta']*p['W']*p['S2exact'])
        gcap=(p['eps']-p['D']-p['errors'])/slope
        sq=cross(p,rb['Ps_lower'],rb['Ps'],1,p['S2'],t['d'])['X']
        always_s=p['fixed_errors']+p['D']+p['K0']*p['B']*rb['Ps']/p['W']+p['beta']*rb['Ps']*p['S2']+sq
        vq=t['d']*(p['T']/rb['Ps_lower']+1)
        aperture_upper=min(p['B']*vq,p['b']*vq+p['FS']/p['W'],p['F']/p['W'])
        rows.append(dict(shield=p['shield'],Dstar=p['D'],environment=p,risk=rb,
            monitor=mon,resources=res,quiet_return_price=cost,
            whole_quiet_price=price(p,rb,mon,g,ka,False),
            price_charging_reserve=price(p,rb,mon,g,ka,True,True),
            constant_E=con,constant_class=lb,
            common_traffic_region=dict(joint_burst_max=burst,joint_rate_max=1/common_frame,
                minimum_burst=1,backpressure_max=bp,actual_application_stream=None),
            certified_gain_lower=gain if rb['pass_risk'] and res['pass_resources'] and con['feasible'] and cost['upper']<=F('.01') else None,
            certificate_g_cap_without_cross=gcap,
            always_S_from_start_risk_upper=always_s,
            no_hit_full_aperture_bound=aperture_upper,
            no_hit_aperture_sufficient_s=F('1e-6')/(p['B']*(p['T']/rb['Ps_lower']+1)),
            joint_success=rb['pass_risk'] and res['pass_resources'] and cost['upper']<=F('.01')))
    return dict(task=110,engineering_sha=CFG['engineering_sha'],status='conditional mathematical result; no physical qualification',
                times=times(),calendar=c,rows=rows)
