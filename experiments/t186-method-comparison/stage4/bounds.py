"""Exact interface/application checks and typed use of the T196 snapshot."""
from fractions import Fraction as F
import json
from reuse import HERE

def exact(x):return F(x['exact'])
def show(x):return dict(exact=str(x),value=float(x))

def calculate(cfg):
    th=json.loads((HERE/'theory-report.json').read_text())
    env=cfg['environment'];W=cfg['memory']['words'];T=F(env['mission_s']);eps=F(env['epsilon'])
    b,B,FS=map(F,[env['background_per_s'],env['peak_per_s'],env['solar_fluence_budget']])
    D=exact(th['environment']['D']);S2=b*b*T+(B+b)*FS;beta=F(37,76*W)
    assert S2==exact(th['environment']['S2exact'])
    xm,xp,J=F('0.99999'),F('1.00001'),F('.5')
    Ps=W*196*xp/10**9;E=F('148.501480')/10**9;R=F('92.500920')/10**9
    t0=Ps+E;X=F('.0001')+F(209,10**9)/T;app=F('402.004')/10**9*1000
    def support(P,delta):return delta+D+B*t0/W+beta*P*S2+beta*(E+P/W)*S2
    assert support(Ps,F(6,10**6))==exact(th['general_mandatory_support']['1']['risk_upper'])
    assert support(27*Ps,F(6,10**6))==exact(th['general_mandatory_support']['27']['risk_upper'])
    Pc=cfg['fixed']['period_ns']*xp/10**9
    assert support(Pc,F(3,10**6))==exact(th['fixed_candidate']['risk_upper'])
    assert support((cfg['fixed']['period_ns']+4)*xp/10**9,F(3,10**6))>eps
    d=cfg['delivery'];cut_plus=d['cut_ns']*xp+J;cut_minus=d['cut_ns']*xm-J
    gate=320*xp+J
    delays={str(gap):F(d['ingress_ns'])+cut_plus+d['batch_ready_ns']+gate+gap*xp+J for gap in (420,552)}
    assert delays['420']/10**9==exact(th['delivery']['source_to_applicable_fresh_rule_s'])
    assert delays['552']/10**9==exact(th['fixed_candidate']['common_transport_fresh_install_upper_s'])
    assert max(delays.values())<=10000 and d['batch_ready_ns']<cut_minus
    ceil=lambda x:-(-x.numerator//x.denominator)
    packet=2+ceil((cut_plus+d['ingress_ns']+J)/(4*xm));flight=2+ceil((d['ingress_ns']+J)/(4*xm))
    assert packet==1253 and flight==253 and 2*packet+flight<=d['banks']*d['bank_records'] and packet<=d['bank_records']
    apps={}
    for p in cfg['application']['profiles']:
        rate=F(p['pairs_per_epoch']*10**9,p['epoch_ns']);K=1000;TQ=F(9,10)*T
        eff=rate+K*(p['pairs_per_epoch']+rate*F(3,10**6))/TQ
        assert eff==exact(th['application_edges'][p['id']]['strict_20ns_expanded_quiet_rate_upper']) and eff<=1000
        assert rate*T+p['pairs_per_epoch']<=1000*T
        apps[p['id']]=dict(rate_per_type_s=show(rate),expanded_quiet_rate_upper_s=show(eff),
                          aggregate_cap=True,individual_component_cap=False)
    V=F(W,1)/(W*196*xm/10**9)+3*W/T
    Ftotal=b*T+FS
    Ufast=support(Ps,F(6,10**6))
    fixed_fast_price=R*V+(E-R)*(Ftotal*(1+F(1,W))/T+1/T+F(1,10**6)+Ufast*V)+app+X
    universal_price=E*V+app+X
    rows={}
    for id_ in cfg['method_ids']:
        if id_=='our_r4':u=exact(th['our_r4']['risk_upper']);price=exact(th['our_r4']['full_bus_mission']);rule='T119/r4 full information/coupling contract'
        elif id_=='constant_sufficient':u=exact(th['fixed_candidate']['risk_upper']);price=exact(th['fixed_candidate']['full_mission_price_upper']);rule='T196 fixed schedule, three relevant lifetime quotas'
        elif id_=='constant_1':u=Ufast;price=fixed_fast_price;rule='T196 deterministic support1, conservative six-quota upper'
        else:u=support(27*Ps,F(6,10**6));price=universal_price;rule='T196 support27; price uses hard always-E envelope on every history'
        rows[id_]=dict(lifetime_Q_upper=show(u),epsilon=str(eps),
                       risk_status='conditionally established' if u<=eps else 'not established; upper above epsilon is not rejection',
                       risk_basis=rule,full_expected_SRAM_price_upper=show(price),
                       price_scope='full lifetime conditional bound, not the sampled history mean; includes app, X and global bad histories',
                       missing_risk_term=None if u<=eps else 'rule-specific joint-skip upper or independent necessary counterexample',
                       CPU_price=None,energy_price=None)
    return dict(status='OWN RESULT / implementation applicability pending theorist agreement and independent review',
                theory_sha=cfg['theory_sha'],S2=show(S2),delivery_upper_ns={k:show(v) for k,v in delays.items()},
                queue=dict(packet_upper=packet,inflight_upper=flight,simultaneous_safe_upper=2*packet+flight,
                           allocated_records=d['banks']*d['bank_records'],processing_before_next_cut=True),
                application=apps,methods=rows,necessary_fixed_class=th['necessary_classes'],
                source_terms=dict(direct_expected_count=show(D),initial=show(B*t0/W),global_six_quotas='6e-6 once per lifetime',
                                  false='expected rate on the required time intervals; no pathwise count cap',
                                  outage='pathwise <=1e-4 T; recoveries<=1000; loss-rises<=1001',
                                  our_price_bad_coupling='full accepted beta0 U119 in imported price; not replaced by physical beta',
                                  extra_protected_SRAM='all extra work must satisfy the existing X envelope; numerical allocation uses a separate transport/state store'))
