"""One directed substitution of accepted hybrid (9)-(14), no schedule search."""
from fractions import Fraction as F
from common import NS,ceil,intervals

def f(x,L,d):
    return max(F(0),L-d*x)**2/(x+1)

def root_bracket(y,L,d,steps=116):
    """Exact rational bisection; f decreases. Enclose the nonnegative root."""
    if y>=L*L:
        return F(0),F(0)
    if y<=0 or d<0:
        raise ValueError('positive target and nonnegative aperture required')
    if not d:
        x=L*L/y-1
        return x,x
    lo,hi=F(0),L/d
    for _ in range(steps):
        mid=(lo+hi)/2
        if f(mid,L,d)>y:
            lo=mid
        else:
            hi=mid
    return lo,hi

def calculate(inp,cfg,manifest):
    I=intervals()
    W=inp['fixed']['words'];T=F(inp['fixed']['mission_s']);eps=F(inp['fixed']['epsilon'])
    env=inp['proposed_environment'];r=env['residual']
    b,B,R,g,Fr=map(F,(env['background'],env['total_peak'],r['cap_R'],r['growth_g'],r['mass_F_r']))
    delta=F(manifest['delta_exec'])
    if delta!=F(inp['fixed']['lifetime_other_budget']):
        raise ValueError('Use the retained shared execution bound, not a new quota')
    s=cfg['service'];xm,xp,J=map(F,(s['clock_lower'],s['clock_upper'],s['operation_endpoint_span_ns']))
    E_nom=3*s['read_beat_ns']+s['decode39_ns']+3*s['write_beat_ns']+s['turnaround_ns']
    R_nom=3*s['read_beat_ns']+s['decode39_ns']
    E_plus=E_nom*xp+J
    # Nominal anchor +-J and release no later than start+E_plus.
    # Fixed envelope includes all permitted repair choices and both endpoints.
    d=(E_plus+2*J)/NS
    R_bus=(3*s['read_beat_ns']*xm-J)/NS
    R_core=(R_nom*xm-J)/NS
    h=R/g;L=Fr/R-h/2;D=h+L
    kappa=I(F(38,78)*((b+R)/W)**2)*I(-B*L/W).exp()
    H=I(0)-I(1-eps-delta).ln()
    target=H/(kappa*I(W))
    xlo=root_bracket(F(target.hi),L,d)[0]
    xhi=root_bracket(F(target.lo),L,d)[1]
    nlo=W*xlo*(T-D)/(L+d);nhi=W*xhi*(T-D)/(L+d)
    necessary_visits=ceil(nlo)
    # Exactly one pending terminal operation; one not-yet-started aperture
    # can touch T because of the deterministic +/-J enlargement.
    # R_core >4J proves at most one nominal anchor in the terminal 2J strip.
    assert R_core*NS>4*J and h>d+2*J/NS
    edge=2
    complete=max(0,necessary_visits-edge)
    expectation_factor=1-delta
    expected_reads=expectation_factor*complete
    app=cfg['application']
    n_app=ceil(F(T*NS-app['first_ns']-app['read_offset_ns'],app['epoch_ns']))
    init_bus=F(W)*(3*s['write_beat_ns']+s['turnaround_ns'])*xm/NS-F(W)*J/NS
    init_core=F(W)*(s['encode39_ns']+3*s['write_beat_ns']+s['turnaround_ns'])*xm/NS-F(W)*J/NS
    app_bus=n_app*R_bus;app_core=n_app*R_core
    enclosure=lambda a,z:dict(lower=str(I(a).lo),upper=str(I(z).hi))
    return dict(
        status='OWN_RESULT_CONDITIONAL_SERVICE_PRICE_TRANSFER_NOT_HYBRID_ACCEPTANCE',
        units='physical seconds, counts, resource fractions of full T',
        scope='all deterministic robustly admissible local per-word calendars; not random mixtures or adaptive calendars',
        service=dict(clock_lower=xm,clock_upper=xp,J_ns=J,E_nominal_ns=E_nom,E_upper_ns=E_plus,
                     fixed_aperture_upper_ns=d*NS,R_bus_lower_ns=R_bus*NS,R_core_lower_ns=R_core*NS,
                     aperture='[xi*tick-J, xi*tick+E_plus+J]; fixed xi, envelopes independent of future errors',
                     future_boundary_strip_ns=2*J,nominal_anchor_spacing_lower_ns=R_core*NS-2*J,
                     terminal_edge_deductions=edge,initial_pending=False),
        witness=dict(rise_s=h,plateau_s=L,duration_s=D,shift_domain_s=T-D),
        inversion=dict(kappa=dict(lower=str(kappa.lo),upper=str(kappa.hi)),
                       H_epsilon=dict(lower=str(H.lo),upper=str(H.hi)),
                       target=dict(lower=str(target.lo),upper=str(target.hi)),
                       x_star=enclosure(xlo,xhi),visits_enclosure=enclosure(nlo,nhi),
                       necessary_integer_visits_lower=necessary_visits,
                       OFF_excluded_by_necessary_count=necessary_visits>0),
        geometric_good_execution=dict(completed_reads_lower=complete,
                       read_bus_fraction_lower=complete*R_bus/T,
                       read_core_fraction_lower=complete*R_core/T),
        expected_price=dict(delta_exec=delta,factor=expectation_factor,
                       completed_reads_lower=expected_reads,
                       protection_read_bus_fraction_lower=expected_reads*R_bus/T,
                       protection_read_core_fraction_lower=expected_reads*R_core/T,
                       uniform_for_every_fixed_r=True,conditions=['deterministic ex-ante calendar and fixed admissible clock',
                         'fixed envelopes contain every good-execution repair',
                         'on good execution all planned visits occur; at most one pending and one future boundary aperture',
                         'joint coupling failure probability at most delta_exec for each allowed r; no independence assumed',
                         'cost nonnegative on failure histories; all accounting continues after memory A'],
                       counter_error_budget_charged=False,
                       implementation_verified=False),
        common_price=dict(application_reads=n_app,useful_writes=0,
                       good_application_bus_fraction_lower=app_bus/T,
                       good_application_core_fraction_lower=app_core/T,
                       good_initial_bus_fraction_lower=init_bus/T,
                       good_initial_core_fraction_lower=init_core/T,
                       expected_shared_bus_lower_if_same_good_contract=expectation_factor*(app_bus+init_bus)/T,
                       expected_shared_core_lower_if_same_good_contract=expectation_factor*(app_core+init_core)/T,
                       ECC_included_in_full_read=True),
        unpriced=dict(repairs='omitted from a lower bound, not physically zero',
                     controller_CPU_ns_per_action=None,energy_J_per_action=None,idle_protection_W=None,
                     controller_bus_average=None,controller_bus_peak=None,
                     physical_execution_failure_evidence=None),
        no_new_hybrid_Q=True,no_gain_claim=True,old_Q_recomputed=False)
