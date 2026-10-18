"""Conditional continuous-NHPP certificate. Exact rational upper enclosures.

For any service rule retaining stride-k support, each error birth survives
at most L=k*W*196 ns+132 ns. Any first weight>1 requires two different-bit
marks on one word separated by <=L. Campbell + union + Cauchy-Schwarz give
Q<=min(1,(37/38)/W*L*integral(lambda**2)). This deliberately also counts
cancelled/repaired pairs. It is not a probability estimator for one trace.
"""
from fractions import Fraction as F
from functools import lru_cache
from scenarios import segments


@lru_cache(maxsize=None)
def upper_log_ratio(x,y,terms=60):
    """Exact rational enclosure for log(y/x), x,y>0, y>=x.

    Range reduction to [1,2] and atanh series; tail <=2*z^(2n+1)/
    ((2n+1)*(1-z*z)). No floating directed rounding is required.
    """
    r=F(y)/F(x)
    assert r>=1
    p=0
    while r>=2:
        r/=2;p+=1
    def one(r):
        z=(r-1)/(r+1)
        s=2*sum((z**(2*i+1)/F(2*i+1) for i in range(terms)),F(0))
        tail=2*z**(2*terms+1)/((2*terms+1)*(1-z*z))
        return s,s+tail
    a,b=one(r);c,d=one(F(2))
    return a+p*c,b+p*d


def exp_upper(x,terms=60):
    assert 0<=x<1
    value=term=F(1)
    for i in range(1,terms):
        term*=x/i;value+=term
    following=term*x/terms
    return value+following/(1-x/F(terms+1))


def fixed_phase_factor(k,W,rho):
    # For every t, next W selected starts cover each word once. Since
    # s(j)=196*j-32*(j%8), mean(next_start-t)<=P/2+98*k+224 ns.
    # Add repair 132 ns and bound lambda(t+u)<=lambda(t)*exp(rho*L).
    L=F(k*W*196+132,10**9)
    mean=F(k*W*98+98*k+356,10**9)
    return mean*exp_upper(rho*L)


def moment_enclosure(ep,env,power):
    low=high=F(0)
    for a,b,x,y in segments(ep,env):
        # Endpoints come from the two input strings, not reconstructed floats.
        X=F(env['background_per_s']) if x==float(env['background_per_s']) else F(env['peak_per_s'])
        Y=F(env['background_per_s']) if y==float(env['background_per_s']) else F(env['peak_per_s'])
        dt=F(b-a)
        if X==Y:
            low+=dt*X**power;high+=dt*X**power
        else:
            u,v=sorted([X,Y]);lnlo,lnhi=upper_log_ratio(u,v)
            val=dt*(v**power-u**power)/power
            low+=val/lnhi;high+=val/lnlo
    return low,high


def ceil_decimal(value,places=18):
    scale=10**places
    n=-(-value.numerator*scale//value.denominator)
    return f'{n//scale}.{n%scale:0{places}d}'


def calculate(cfg):
    env=cfg['environment'];W=cfg['memory']['words'];c=F(37,38)
    b,B,Fs,T,epsilon=(F(env[k]) for k in ['background_per_s','peak_per_s','solar_fluence_budget','mission_s','epsilon'])
    slope_lo,slope_hi=upper_log_ratio(b,B)
    rows=[]
    for ep in cfg['episodes']:
        _,S1=moment_enclosure(ep,env,1);_,S2=moment_enclosure(ep,env,2)
        fl=S1-b*ep['horizon_s']
        rho=max(slope_hi/F(ep['rise_s']),slope_hi/F(ep['fall_s'])) if ep['shape']!='quiet' else F(0)
        assert fl<=Fs and rho<=F(env['rho_per_s'])
        for k in cfg['strides']:
            L=F(k*W*196+132,10**9)
            Q=min(F(1),c*L*S2/W)
            fixed=min(Q,c*fixed_phase_factor(k,W,rho)*S2/W)
            rows.append(dict(episode=ep['id'],support_stride=k,maximum_residence_s=str(L),
                             S1_upper=ceil_decimal(S1),S2_upper=ceil_decimal(S2),
                             solar_excess_upper=ceil_decimal(fl),log_slope_upper=ceil_decimal(rho),
                             Q_upper=ceil_decimal(Q),within_epsilon=Q<=epsilon,
                             fixed_phase_Q_upper=ceil_decimal(fixed),fixed_within_epsilon=fixed<=epsilon))
    # Over the scalar 10-year envelope: lambda=b+f, 0<=f<=B-b,
    # integral f<=Fs => S2<=b*b*T+(B+b)*Fs.
    S2=b*b*T+(B+b)*Fs
    mission=[]
    for k in cfg['strides']:
        L=F(k*W*196+132,10**9);Q=min(F(1),c*L*S2/W)
        fixed=min(Q,c*fixed_phase_factor(k,W,F(env['rho_per_s']))*S2/W)
        mission.append(dict(k=k,maximum_residence_s=str(L),S2_upper_exact=str(S2),
                            Q_upper_exact=str(Q),Q_upper=ceil_decimal(Q),within_epsilon=Q<=epsilon,
                            fixed_phase_Q_upper=ceil_decimal(fixed),fixed_within_epsilon=fixed<=epsilon,
                            asymptotic_baseline_bus_fraction=str(F(92,196*k))))
    feasible=[x for x in mission if x['fixed_within_epsilon']]
    return dict(scope='continuous NHPP, independent uniform word/bit singleton marks, clean start, ideal birth-preserving E; not full R0-A/Theta',
                formula='Q <= min(1, (37/38)/W * (k*W*196+132)/1e9 * S2)',
                certificate_arithmetic='exact rational log enclosures, output rounded upward to 18 places',
                episode_bounds=rows,scalar_mission_bounds=mission,
                maximum_certified_stride_in_finite_family=max((x['k'] for x in feasible),default=None),
                finite_family_mean_total_cost_optimum=None,
                unknown=['full environment transfer','constant class optimum','expected correction/application/observation cost','sufficiency does not exclude uncertified k'])
