"""Directed independent checks of the new risk/service/price calculation."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import product

from codec import Code,t187
from comparison import NS,calculate,risk,service,period,read_bounds,count_apps,ceil
from parents import projected_groups,witness_coefficients


def run(cfg,result):
    passed=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        passed.append(name)

    # Direct cell integration of independently chosen varying rate profiles,
    # compared to the new moment/cross majorant (no calls to risk()).
    profiles=[[(F(0),F(1),F(1,100)),(F(1),F(3),F(3,100))],
              [(F(0),F(1,3),F(1,20)),(F(1,3),F(3),F(1,200))]]
    cases=0
    for t,n,p,segments in product((1,2),(5,7),({1:F(1)},{1:F(3,4),2:F(1,4)}),profiles):
        if t==1 and len(p)>1:continue # size2 belongs to direct, not Phi1.
        groups=projected_groups(n,p);co=witness_coefficients(n,t,groups)
        P=F(2,3);d=F(1,100);W=2;T=3;B=max(v for _,_,v in segments)
        moments={q:sum((b-a)*r**q for a,b,r in segments) for q in (1,2,3)}
        case=dict(W=W,n=n,t=t,T=F(T),P=P,D=d,
                  segments=[(a,b,(groups[1]*r,groups[2]*r)) for a,b,r in segments])
        u,v,x=t187.fixed_upper(case,'E')
        cm=W*(2*co['quadratic']*B*d*moments[1]+3*co['cubic']*(B*d*P*moments[2]+B*B*d*d*moments[1]))
        vm=W*(co['quadratic']*P*moments[2]+co['cubic']*P*P*moments[3])
        check(f'cell integral E-cross majorant t{t} n{n} case{cases}',x<=cm and v<=vm and u<=cm+vm)
        if cases in (0,8,12):
            lo,hi=t187.exact_e(case,terms=20,places=40)
            check(f'certified small CTMC below witness bound case{cases}',0<=lo<=hi<=u)
        cases+=1

    rows=result['rows'];eps=F(cfg['epsilon'])
    for name,row in rows.items():
        n,t,k=row['n'],row['t'],row['k_passes'];r=row['risk'];tm=row['timing'];c=row['cost']
        check(name+' one lifetime quota',r['terms']['lifetime_exceptions']==F(cfg['lifetime_other_budget']))
        check(name+' terms sum and positive E-cross',sum(r['terms'].values())==r['unclipped'] and
              r['terms']['E_cross_quadratic']+r['terms']['E_cross_cubic']>0)
        check(name+' half epsilon sufficient',r['upper']<=eps/2)
        if name!='t1_adaptive':
            nxt=risk(cfg,n,t,period(cfg,k+1)['upper_ns'],service(cfg,n)['upper']['E'])
            check(name+' adjacent larger period rejected by target',nxt['upper']>eps/2)
        check(name+' all service apertures nonnegative',tm['control_slack_ns']>0 and tm['application_aperture_slack_ns']>0)
        check(name+' hard time/peak constraints',tm['app_deadline_slack_ns']>0 and tm['peak_bus_remaining_for_other_work']>0)
        check(name+' target response shortfall retained',tm['app_target_slack_ns']<0)
        check(name+' lower <= expected upper <= hard',0<c['core_SRAM_fraction_lower']<=c['core_SRAM_fraction_upper']<=c['all_history_SRAM_core_upper'])
        check(name+' initialization paid',c['initialization']['encodes']==cfg['words'] and c['initialization']['amortized_fraction']>0)
        check(name+' full32 RMW plus initialization counted once',
              c['full_cost_rates']['encodes']==(count_apps(cfg)['write']+cfg['words'])/cfg['mission_s'])
        check(name+' nonzero repair upper incl bad histories',c['repair_count_upper']>=r['upper']*read_bounds(cfg,1 if name=='t1_adaptive' else k)['upper'])
        check(name+' full horizon pending and post-A',c['bad_history_paid'] and c['pending_paid'] and c['after_A_paid'])
        if name!='t1_adaptive':
            check(name+' no avoidable monitor cost',all(c['full_cost_rates'][z]==0 for z in ('cuts','captures','records')) and c['transport_plus_loss_state_bytes']==0)
        # Delay limit is service-constrained, and rechecking E risk at it stays
        # within the HARD epsilon. It does not preserve a claimed optimal grid.
        d2=service(cfg,n)['upper']['E']+tm['extra_decode_nominal_ns_limit']*service(cfg,n)['xplus']
        check(name+' allowed decode perturbation keeps hard risk',risk(cfg,n,t,row['period']['upper_ns'],d2)['upper']<=eps)
    check('t2 map peak target shortfall retained',rows['t2_constant']['timing']['peak_target_slack']<0)
    a=rows['t1_adaptive']['cost'];ad=a['adaptive']
    check('extra-veto slope positive and hard cap available',a['veto_core_fraction_slope_per_notification_per_s']>0 and a['veto_hard_cap_reached_per_s']>0)
    check('NR and long hold cover birth delay',ad['timers']['NR_covers_h_plus_tau'] and ad['timers']['guard_holds_cover_tau'])
    check('34-bit timer fits with no wrap',ad['timers']['counts_fit_34_bits'])
    check('read-repeat condition actually checked',ad['app_same_word_revisit_s']>ad['mandatory_age_s'])
    check('controller and energy retained parametrically',a['CPU_fraction_coefficients']['cuts_ns']>0 and a['energy_coefficients_per_second']['decisions']>0)
    check('all capacities remain unknown, not PASS',all(x is None for x in cfg['constraints']['capacity_caps'].values()))
    check('physical risk and ranking not inferred',all(r['risk']['physical_unconditional_probability'] is None for r in rows.values()) and result['physical_winner'] is None)
    check('class optimum not inferred from selected k',all(r['class_optimum_lower'] is None for r in rows.values()))

    # Small-domain counting oracle: startup and kth passes over the same phases.
    toy=deepcopy(cfg);toy['words']=8;toy['mission_s']=1
    for k in (1,3,11):
        H=20000;toy['mission_s']=F(H,NS)
        actual=sum(1 for j in range(8*15) if (j//8==0 or (j//8)%k==0) and
                   (j//8)*1568+(j%8)*164<H)
        rb=read_bounds(toy,k)
        check(f'whole started work count against finite calendar k{k}',rb['lower']<=actual<=rb['upper'])
    # Count potentially intersecting frames at ALL frame endpoint alignments.
    for n in (39,44):
        E=service(cfg,n)['upper']['E'];L=1000000;tm=rows['t1_constant' if n==39 else 't2_constant']['timing']
        starts=[frame*1568+j*164 for frame in range(-2,650) for j in range(8)]
        max_count=max(sum(F(a)-E<=s<F(a)+L for s in starts) for a in [0,1,163,164,1311,1312,1567])
        check(f'peak counts include arbitrary phase and pending n{n}',max_count<=tm['counted_control_operations'])
    # A two-bit corrected word is ONE logical nonzero syndrome, not two
    # virtual parents or three x16 events. The functional decoder makes the
    # required full-word observation available; transport implementation is
    # deliberately outside this test and remains frozen.
    code=Code(2);word=code.encode(0x13579bdf);dirty=word^(1<<7)^(1<<36)
    dec=code.decode(dirty)
    check('full word handles errors in separate bus beats',dec['data']==0x13579bdf and dec['corrected_word']==word and dec['ERR'] is True)

    check('12 frozen group slices, baseline matches main table',len(result['sensitivity'])==12 and
          all(result['sensitivity'][0]['risk'][k]['upper']==v['risk']['upper'] for k,v in rows.items()))
    high=result['sensitivity'][-1]['risk']
    check('direct p2/p3 retained, mixed terms nonzero',high['t1_constant']['terms']['direct']>0 and
          high['t2_constant']['terms']['direct']>0 and high['t2_constant']['terms']['quadratic']>0)
    check('sensitivity never refits periods',all(set(p['risk'])==set(rows) for p in result['sensitivity']))
    check('decode limit recalculates probability and repair cost',
          result['conditional_bus_comparison']['t2_at_service_decode_limit']['Q_upper']>rows['t2_constant']['risk']['upper'] and
          result['conditional_bus_comparison']['t2_at_service_decode_limit']['below_selected_adaptive_lower'])
    return dict(count=len(passed),checks=passed,small_cell_cases=cases,
                monte_carlo_runs=0,scope='directed calculation tests, not independent scientific acceptance')


if __name__=='__main__':
    import json
    from pathlib import Path
    config=json.loads((Path(__file__).resolve().parent/'common-input.json').read_text(encoding='utf-8'))
    print(json.dumps(run(config,calculate(config)),indent=2))
