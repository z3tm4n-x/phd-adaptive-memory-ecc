"""Targeted deterministic calculations; no controller or simulation imports."""
from fractions import Fraction as F
import math
import mpmath as mp


def backup(cfg, D, tau, scale=1):
    """True auxiliary fixed-reserve expectation with discrete word phases."""
    w=mp.mpf(cfg['words']); H=mp.mpf(cfg['horizon_s'])
    p=w*mp.mpf(cfg['word_frame_ns'])/10**9
    t=mp.mpf(str(tau)); k=2/mp.mpf(str(D)); s=mp.mpf(str(scale))
    lo=mp.mpf(cfg['b_low_per_s'])*s; hi=mp.mpf(cfg['b_high_per_s'])*s
    mean=(hi+lo)/2; v=(hi-lo)/2
    J=-mp.expm1(-k*t)/k
    f=mean**2*t**2/2+v**2*(t/k+mp.expm1(-k*t)/k**2)
    geom=mp.expm1(-k*p)/(w*mp.expm1(-k*p/w))
    I=(1-geom)/k
    cross=mean**2*t*p*(w-1)/(2*w)+v**2*I*J
    N=H/t
    if N != int(N): raise ValueError('This local formula requires H/tau integer')
    return (N*f+(N-1)*cross)/w


def schedule(H, p, first, second):
    """Next action selected at a completed pass, without a mid-pass reset."""
    H,p,a,b=map(lambda x:F(str(x)),(H,p,first,second))
    end=F(0); complete=started=0
    while end<H:
        tau=a if end<H/2 else b
        future=end+tau
        if future-p<H: started+=1
        if future>H: break
        end=future; complete+=1
    return complete,started


def run(cfg):
    mp.mp.dps=70
    W=cfg['words'];H=cfg['horizon_s'];p=W*cfg['word_frame_ns']/1e9
    G=mp.mpf(cfg['G']); beta=mp.mpf(cfg['beta']); num=mp.mpf(cfg['numeric_reference_reserve'])
    rows=[]
    for scale in (mp.mpf(1),mp.mpf(39)/32):
        for tau in (1,.5):
            values=[backup(cfg,D,tau,scale) for D in (30,300,3000)]
            assert values==sorted(values)
            guard=mp.mpf(cfg['b_high_per_s'])*scale*cfg['rmw_guard_window_ns']/10**9*(H/tau)
            for D,V in zip((30,300,3000),values):
                margin=(mp.mpf('.1')-guard-beta)/G-num-V
                rows.append(dict(D=D,scale=float(scale),backup_s=tau,
                    auxiliary_cost=float(V),rmw_guard=float(guard),
                    margin_before_new_model_and_numeric_validation=float(margin)))
    # Independent finite sum for small W, not the geometric helper above.
    maxerr=mp.mpf(0)
    for w in (2,7,31):
        q=dict(cfg,words=w)
        P=mp.mpf(w)*q['word_frame_ns']/10**9;k=mp.mpf(2)/300
        direct=sum((-mp.expm1(-k*P*j/w)/k for j in range(w)))/w
        geom=(1-mp.expm1(-k*P)/(w*mp.expm1(-k*P/w)))/k
        maxerr=max(maxerr,abs(direct-geom))
    assert maxerr<mp.mpf('1e-60')
    rate=float(mp.mpf(cfg['retained_target_peak_per_hour'])/3600)
    mean=float(mp.mpf(cfg['retained_target_mean_per_hour'])/3600)
    comparisons=[]
    for label,grid in [('reference_12',cfg['reference_actions_s']),('input_expanded_15',cfg['input_expanded_actions_s'])]:
        for eps in cfg['epsilon_slices']:
            valid=[]
            for a in grid:
                for b in grid:
                    n,started=schedule(H,p,a,b)
                    bound=H*rate**2*max(a,b)/(2*W)+rate*started*cfg['rmw_guard_window_ns']/1e9
                    if bound<=eps: valid.append((n,a,b,bound,started))
            best=min(valid) if valid else None
            comparisons.append(dict(grid=label,epsilon=eps,candidates=len(grid)**2,
                                    passing=len(valid),best=best))
    infos=[]
    for label,lam in [('retained_mean',mean),('retained_peak',rate)]:
        t95=math.log(20)/lam
        # The last completed read of each word precedes pass completion.
        lag=p/2-p/(2*W)+cfg['read_completion_to_write_ns']/1e9
        for tau in (1,5,30,60,300):
            for deadline in (30,60,300,3600):
                end=(deadline//tau)*tau
                exposure=max(0,end-lag)
                infos.append(dict(anchor=label,tau=tau,deadline=deadline,
                    arrival_opportunity_by_completed_read= -math.expm1(-lam*exposure),
                    auxiliary_first_nonzero_t95=tau*math.ceil((t95+lag)/tau)))
    q30=H*rate**2*30/(2*W);g30=rate*(H/30)*cfg['rmw_guard_window_ns']/1e9
    scale_threshold=(-g30+math.sqrt(g30*g30+4*q30*.001))/(2*q30)
    return dict(backup_rows=rows,finite_sum_max_error=str(maxerr),
        floor_beta_plus_G_numeric=str(beta+G*num),rule_comparisons=comparisons,
        information=infos,peak_fixed30_bound=q30+g30,
        peak_rate_scale_at_fixed30_boundary=scale_threshold,
        full39_scale='Assumed equal per-bit sensitivity, not measured',
        status='Addressed calculation only; not a new physical or numerical certificate')
