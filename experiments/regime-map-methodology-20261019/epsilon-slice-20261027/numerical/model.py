"""Exact/directed epsilon transfer; published bounds separated from candidate optima."""
import ast,hashlib,importlib.util,json
from fractions import Fraction as F
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]; NS=10**9
def sha(raw): return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()
def encode(x): return (json.dumps(x,default=str,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def ceil(x): x=F(x); return -(-x.numerator//x.denominator)

spec=importlib.util.spec_from_file_location('epsilon_intervals',ROOT/'experiments/t114-two-stage-err/intervals.py')
intervals=importlib.util.module_from_spec(spec); spec.loader.exec_module(intervals); I=intervals.I

def load():
    manifest=json.loads((HERE/'manifest.json').read_bytes())
    for path,expected in manifest['source_sha256'].items():
        if sha((ROOT/path).read_bytes())!=expected: raise ValueError('Changed source: '+path)
    raw=(ROOT/manifest['canonical_input']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['canonical_raw_sha256']: raise ValueError('Canonical input bytes changed')
    canonical=json.loads(raw); cases=[]
    for name,expected in manifest['inputs_sha256'].items():
        raw=(HERE/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError('Changed epsilon input')
        data=json.loads(raw); restored=json.loads(raw); restored['fixed']['epsilon']=canonical['fixed']['epsilon']
        assert restored==canonical, 'Only epsilon may change'
        cases.append((name,data))
    cfg=json.loads((ROOT/canonical['fixed']['source']).read_bytes())
    return manifest,canonical,cfg,cases

def setup(inp,cfg):
    e=inp['proposed_environment']; s=cfg['service']; cal=cfg['calendar']
    W=inp['fixed']['words']; T=F(inp['fixed']['mission_s'])
    xm,xp,J=map(F,(s['clock_lower'],s['clock_upper'],s['operation_endpoint_span_ns']))
    b,amp,B,Fs=map(F,(e['background'],e['p']['amplitude_above_background'],e['total_peak'],e['total_solar_mass']))
    R,g,Fr=(F(e['residual'][k]) for k in ('cap_R','growth_g','mass_F_r'))
    assert B==b+amp+R and Fs==2*Fr and e['residual']['distribution_over_paths'] is None
    assert (W,T,inp['fixed']['code'])==(131072,315576000,[39,32,1])
    assert inp['fixed']['useful_writes']==0 and not inp['fixed']['ordinary_reads_repair']
    fast=W*cal['g_ticks']; block=fast+7*cal['frame_ticks']
    S2=b*b*T+b*Fs+amp*Fs/3+(2*(b+amp)+R)*Fr
    return dict(W=W,T=T,b=b,pmax=b+amp,B=B,R=R,g=g,Fr=Fr,Fs=Fs,S2=S2,xm=xm,xp=xp,J=J,
        fast=fast,block=block,cal=cal,delta0=F(inp['fixed']['lifetime_other_budget']),
        deltaC_requirement=F('.00005'),Fp=b*T+Fs,
        Rbus_minus=48*xm-J,Rcore_minus=68*xm-J,Rbus_plus=48*xp+J,
        Rcore_plus=68*xp+J,Drepair_bus_plus=56*xp+J,Drepair_core_plus=56*xp,
        Ecore_plus=124*xp+J,dE=(124*xp+3*J)/NS,
        Nhard=W*(ceil(T/((fast*xm-J)/NS))+2),
        Pobs=(block*xp+J)/NS)

def count_reads(ticks,c,cycle,k):
    ticks=F(ticks)
    if ticks<=0: return 0
    q=int(ticks//(k*cycle)); r=ticks-q*k*cycle; cal=c['cal']; n=q*c['W']
    for phase in range(cal['batch_size']):
        n+=max(0,min(c['W']//cal['batch_size'],ceil((r-phase*cal['c_ticks'])/cal['frame_ticks'])))
    return n

def horizon_reads(c,cycle,k):
    return dict(lower=count_reads((c['T']*NS-c['J'])/c['xp'],c,cycle,k),
        nominal=count_reads(c['T']*NS,c,cycle,k),
        upper=count_reads((c['T']*NS+c['J'])/c['xm'],c,cycle,k))

def risk_base(c,cycle,k):
    return ((k+1)*cycle*c['xp']+2*c['J'])/NS*c['S2']/c['W']

def maximal_base(c,cycle,budget):
    return max(0,int(((budget*c['W']/c['S2']*NS-2*c['J'])/(cycle*c['xp'])-1)//1))

def lower_classes(c,eps):
    # Unmodified f/root_bracket from accepted PR272, exact rational bisection.
    tree=ast.parse((ROOT/'experiments/hybrid-p-r-20261026/interface-price/price.py').read_text(encoding='utf-8'))
    scope={'F':F}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('f','root_bracket')],type_ignores=[]),'accepted-PR272-root','exec'),scope)
    root=scope['root_bracket']; R,g,Fr,W,T=c['R'],c['g'],c['Fr'],c['W'],c['T']
    rise=R/g; L=Fr/R-rise/2; D=rise+L; d=c['dE']; delta=c['delta0']
    assert 0<L and D<T and rise>(c['fast']*c['xp']+c['J'])/NS
    assert 0<eps+delta<1
    kappa=I(F(38,78)*((c['b']+R)/W)**2)*I(-c['B']*L/W).exp()
    H=I(0)-I(1-eps-delta).ln(); target=H/(kappa*I(W))
    xl=root(F(target.hi),L,d)[0]; xh=root(F(target.lo),L,d)[1]
    necessary=ceil(W*xl*(T-D)/(L+d)); expected=(1-delta)*max(0,necessary-2)
    # Constant-class consequence: n_w <= L/P+2 on a plateau after startup.
    # Hence P <= L/(x_*-2), without restricting phases or to the numerical grid.
    Pcap=L/(xl-2) if xl>2 else None
    local_fixed=(1-delta)*W*max(F(0),T/(Pcap+c['J']/NS)-2) if Pcap else F(0)
    nfixed=max(expected,local_fixed)  # constant class is a subset of schedules
    assert nfixed>=0 and expected>=0
    return dict(status='CONDITIONAL_NECESSARY_CLASS_BOUNDS',
        H_exact_enclosure=dict(lower=H.lo,upper=H.hi),linear_H_not_used=eps+delta,
        x_root_lower=xl,x_root_upper=xh,necessary_scheduled_visits=necessary,
        OFF_excluded=necessary>0,witness=dict(rise_s=rise,plateau_s=L,duration_s=D),
        schedule_bus_lower=expected*c['Rbus_minus']/(T*NS),
        schedule_core_lower=expected*c['Rcore_minus']/(T*NS),
        constant_period_cap_s=Pcap,
        constant_bus_lower=nfixed*c['Rbus_minus']/(T*NS),
        constant_core_lower=nfixed*c['Rcore_minus']/(T*NS),
        constant_transfer_status='local consequence proposed to #196; not an optimality theorem',
        source='hybrid-p-r (9)-(14), PR272 G and edge deductions',
        delta_exec=delta,statistical_budget_charged_to_competitor=0)

def fixed_candidate(c,eps):
    k=maximal_base(c,c['fast'],eps-c['delta0'])
    if k<1: return dict(status='NOT_CERTIFIED_BY_A7_A8',k=None)
    qb=risk_base(c,c['fast'],k); q=qb+c['delta0']; reads=horizon_reads(c,c['fast'],k)
    assert q<=eps<risk_base(c,c['fast'],k+1)+c['delta0']
    # Deterministic all-history gate: no off-calendar operation, even after A.
    H=min(F(reads['upper']),2*c['Fp']+q*reads['upper'])
    price=lambda r,d:(r*reads['upper']+d*H)/(c['T']*NS)
    return dict(status='SUFFICIENT_CONSTANT_CANDIDATE_NOT_CLASS_OPTIMUM',k=k,
        period_upper_s=(k*c['fast']*c['xp']+c['J'])/NS,Q_upper=q,
        budget=dict(base_pairs=qb,delta0=c['delta0'],alpha=0,zeta=0,deltaC=0),reads=reads,
        repair_expected_upper=H,
        bus_upper=price(c['Rbus_plus'],c['Drepair_bus_plus']),
        core_upper=price(c['Rcore_plus'],c['Drepair_core_plus']),
        unknown_bus_controller=None,unknown_CPU_energy=None,
        all_history_count_cap_condition='configured deterministic starts only; missed starts lower cost; service duration bounded even after A',
        if_bad_execution_can_start_off_calendar_extra_reads_upper=c['delta0']*c['Nhard'],
        fixed_counter_observation_cost=0,
        schedule_class_upper_is_this_member=True,
        optimal_nonconstant_schedule_identified=False)

def exposure(c,k,M):
    # Relative to the actual predictable group origin; no physical clock reset.
    a0=(k*c['block']*c['xm']-c['J'])/NS; a1=(k*c['block']*c['xp']+c['J'])/NS
    span=M*(a1-a0); w=a0-c['Pobs']; q=ceil(span/a0)+1
    if w<=0 or q>=M: return None
    u=c['R']/2; first=q+1; last=min(M,ceil((u/c['g']-span)/a0)-1); n=max(0,last-first+1)
    mu=w*((M-q)*c['b']+n*(u-c['g']*span)-c['g']*a0*F(n*(first+last),2))
    assert (M-q-1)*a1+w<=M*a0
    return dict(M=M,q=q,used=M-q,w=w,span=span,mu=mu,a0=a0,a1=a1)

def poisson_K(x,zeta):
    K=0; bound=x
    while bound>zeta:
        K+=1; bound=bound*x/(K+1)
        if K>100: raise ValueError('Unexpected quantile range')
    return K,bound

def excursion(c,k,K):
    a=(k*c['block']*c['xp']+c['J'])/NS
    mass=(c['pmax']+c['R']/2)*a+c['g']*a*a/2
    return (K*mass+mass*mass/2)/c['W']

def largest_multiplier(c,k,K,beta,max_m):
    if max_m<2 or excursion(c,2*k,K)>beta: return 0
    lo,hi=2,max_m+1
    while lo+1<hi:
        mid=(lo+hi)//2
        if excursion(c,mid*k,K)<=beta: lo=mid
        else: hi=mid
    return lo

def adaptive_candidate(c,eps):
    e=eps-c['delta0']-c['deltaC_requirement']
    if e<=0: return dict(status='NOT_CERTIFIED_BY_THIS_FAMILY',reason='physical budgets exhaust epsilon')
    qb_allow=e/2; astar=zstar=e/10; bstar=3*e/10
    k=maximal_base(c,c['block'],qb_allow)
    if k<2:
        return dict(status='NOT_CERTIFIED_BY_THIS_FAMILY',k_base=k,
            reason='A5 needs a positive scrub-free prefix; k>=2 does not fit allocated base risk',
            minimum_k2_Q_excluding_deltaC=risk_base(c,c['block'],2)+c['delta0'],
            eps=eps,deltaC_requirement=c['deltaC_requirement'])
    a0=(k*c['block']*c['xm']-c['J'])/NS
    M=ceil(c['R']/(c['g']*a0)); ex=exposure(c,k,M)
    if ex is None: return dict(status='NOT_CERTIFIED_BY_THIS_FAMILY',reason='no finite informative group')
    # Finite design search only over the predeclared number of attempts.
    # K>=0 gives a necessary lower bill for 2*k; no feasible N lies above this cap.
    Ncap=min(int(bstar//excursion(c,2*k,0)),
             int(c['T']*NS//((M*k+2*k)*c['block']*c['xp'])))
    # Tighten the same cap monotonically; no need to enumerate infeasible N.
    lo,hi=0,Ncap+1
    while lo+1<hi:
        mid=(lo+hi)//2; Km,_=poisson_K(c['B']*c['Pobs'],zstar/mid)
        if mid*excursion(c,2*k,Km)<=bstar: lo=mid
        else: hi=mid
    Ncap=lo
    best=None; feasible=0
    for N in range(1,Ncap+1):
        alpha,zeta,beta=astar/N,zstar/N,bstar/N
        K,tail=poisson_K(c['B']*c['Pobs'],zeta)
        max_m=int(((c['T']*NS-c['J'])/(c['block']*c['xp'])-1)//(N*k))-M
        mult=largest_multiplier(c,k,K,beta,max_m)
        if mult<2: continue
        score=(I(1)-(I(0)-I(1)).exp())*I(ex['mu'])-(I(1)/I(alpha)).ln()
        cutoff=ceil(F(score.lo))-1  # strict A3, eta=1
        if cutoff<0: continue
        feasible+=1
        potential=N*(mult-1)
        if best is None or potential>best['saved_passes_all_success']:
            best=dict(N=N,k_rare=mult*k,multiplier=mult,alpha=alpha,zeta=zeta,beta=beta,K=K,
                residue_tail=tail,C_max=cutoff,score_lower=score.lo,score_upper=score.hi,
                saved_passes_all_success=potential,rare_bill=excursion(c,mult*k,K))
    if best is None: return dict(status='NOT_CERTIFIED_BY_THIS_FAMILY',reason='no useful finite repeated candidate',N_design_cap=Ncap)
    N=best['N']; duration=(1+N*(M*k+best['k_rare']))*c['block']*c['xp']/NS+c['J']/NS
    qb=risk_base(c,c['block'],k); q=qb+c['delta0']+c['deltaC_requirement']+astar+zstar+bstar
    assert duration<c['T'] and q<=eps
    reads=horizon_reads(c,c['block'],k); D=best['saved_passes_all_success']*c['W']
    de=c['delta0']+c['deltaC_requirement']; necessary=(1-de)*max(0,reads['lower']-D-2)
    H=min(F(c['Nhard']),2*c['Fp']+q*c['Nhard'])
    S=min(F(c['Nhard']),reads['upper']+de*c['Nhard'])
    best.update(status='CONDITIONAL_REPEATED_FAMILY_PENDING_THEORY_COORDINATION',k_base=k,
        group=ex,base_period_upper_s=(k*c['block']*c['xp']+c['J'])/NS,
        rare_period_upper_s=(best['k_rare']*c['block']*c['xp']+c['J'])/NS,
        Q_upper=q,budget=dict(base_pairs=qb,base_allowance=qb_allow,delta0=c['delta0'],deltaC_requirement=c['deltaC_requirement'],
            alpha_total=astar,zeta_total=zstar,extension_total=bstar),
        N_design_cap=Ncap,feasible_N=feasible,learning_and_reserved_epochs_upper_s=duration,
        reads_base=reads,saved_reads_all_success=D,nominal_main_reads_all_success=reads['nominal']-D,
        mandatory_expected_bus_lower=necessary*c['Rbus_minus']/(c['T']*NS),
        mandatory_expected_core_lower=necessary*c['Rcore_minus']/(c['T']*NS),
        no_guard_no_credit_bus_upper_component=(c['Rbus_plus']*S+c['Drepair_bus_plus']*H)/(c['T']*NS),
        no_guard_no_credit_core_upper_component=(c['Rcore_plus']*S+c['Drepair_core_plus']*H)/(c['T']*NS),
        hard_bus_upper=c['Nhard']*(c['Rbus_plus']+c['Drepair_bus_plus'])/(c['T']*NS),
        hard_core_upper=c['Nhard']*c['Ecore_plus']/(c['T']*NS),
        admission_law=None,expected_saved_passes=None,extra_guard_expected=None,
        control_CPU_energy_WCET=None,deltaC_proved=False,
        comparison_lower_is_family_specific=True,
        full_cost_formulas=dict(S='min(Nhard,Nbase_plus-W*(multiplier-1)*E[good successful attempts]+G_good+delta_exec*Nhard)',
            H='min(S,2*F_parent+U_joint*Nhard)',
            bus='(Rbus_plus*S+Drepair_bus_plus*H)/(T*1e9)+u_A',
            core='(Rcore_plus*S+Drepair_core_plus*H)/(T*1e9)+v_A',
            scope='fixed admissible r and channel; all attempts including invalid paid; no distribution over environments'),
        finite_budget_never_refilled=True,mandatory_work_after_A=True,
        relative_group_clock_transfer='proposed conditional application of A1-A5; #196 confirmation pending')
    best['accounted_observation_work']=dict(used_pass_closes=N*ex['used'],group_adds=N*ex['used'],
        prepaid_attempts=N,online_exp_log_inversions=0,tail_base_passes=N*ex['q'],
        no_new_transport=True,no_reset_on_invalid=True)
    best['all_attempts_invalid_loss_witness']=dict(possible=N<=1000,episodes=N,restores=N,
        outage_seconds=F(N,10000),one_outage_seconds=F(1,10000),
        meaning='one recognized 100 us outage per group; same retained quotas, no environment prior')
    return best

class Series:
    """Small offline ledger: fixed epoch ends and no refund of invalid attempts."""
    def __init__(self,settings):
        self.a=settings; self.used=0; self.block_cursor=1; self.saved_passes=0
    def step(self,count,valid=True,timely=True,main_complete=True,pending=False,healthy=True):
        if self.used>=self.a['N']: raise ValueError('No prepaid attempt remains')
        service=main_complete and not pending
        admit=service and valid and timely and healthy and 0<=count<=self.a['C_max']
        start=self.block_cursor
        self.block_cursor+=(self.a['group']['M']*self.a['k_base']+self.a['k_rare'])
        self.used+=1
        if admit: self.saved_passes+=self.a['multiplier']-1
        return dict(admit=admit,service_valid=service,epoch_start_block=start,
            epoch_end_block=self.block_cursor,alpha_spent=self.used*self.a['alpha'],
            zeta_reserved=self.used*self.a['zeta'],beta_reserved=self.used*self.a['beta'],
            remaining_attempts=self.a['N']-self.used,clean_reset=False)
