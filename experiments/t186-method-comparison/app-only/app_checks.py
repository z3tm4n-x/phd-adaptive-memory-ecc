"""Directed app-only calendar/service/accounting checks, no old campaign."""
from copy import deepcopy
from fractions import Fraction as F
from math import comb
from app_only import NS,calendar_audit,service_audit,full_cost,evaluate


def run(cfg,basis,accepted,result):
    checks=[]
    def check(name,value):
        if not value:raise AssertionError(name)
        checks.append(name)
    cal=result['calendar'];svc=result['service']
    check('all word phases and finite-horizon edges covered',cal['words_checked']==cfg['words'] and cal['first_and_last_cells_bounded'])
    check('no fictitious terminal E or realized-start substitution',not cal['synthetic_E_at_T'] and not cal['realized_starts_used_as_fixed'])
    check('same grants, no dedicated or startup scrub',svc['application_slots_preserved'] and svc['control_starts']==svc['startup_scrub_starts']==0)
    check('conditional response/slot/spacing and any-window peak fit hard caps',svc['hard_service_conditions_hold'])
    check('response reserve target shortfall remains explicit',svc['map_response_target_slack_ns']<0)
    check('no new claim before specific theorist basis',(result['Q_upper'] is None)==(basis['status']!='applicable'))

    toy=deepcopy(cfg);toy['words']=8
    toy['application'].update(epoch_ns=10002,first_ns=1000,read_offset_ns=0,write_offset_ns=5000)
    for H in (0,5999,6000,6001,80016,88033):
        toy['mission_s']=F(H,NS)
        audit=calendar_audit(toy)
        visits=[(6000+q*10002,5*q%8) for q in range(H//10002+2) if 6000+q*10002<H]
        counts=[sum(w==word for _,w in visits) for word in range(8)]
        check(f'direct finite oracle including strict endpoint T={H}',
              audit['writes_before_T']==len(visits) and audit['min_writes_per_word']==min(counts)
              and audit['max_writes_per_word']==max(counts)
              and audit['terminal_apertures_clipped']==sum(t+3000>H for t,_ in visits))

    # A missing whole-word visit creates a gap of 2P; the unchanged strict
    # workload is essential, not a conclusion valid for arbitrary writes.
    P=8*10002
    visits=[6000+j*P for j in range(4)]
    skipped=[v for i,v in enumerate(visits) if i!=1]
    check('a skipped write invalidates the proposed P aperture cover',max(b-a for a,b in zip(skipped,skipped[1:]))==2*P>P)
    bad=deepcopy(cfg);bad['constraints']['application_deadline_ns']=2000
    check('unmet arrival deadline is exposed, not silently used',not service_audit(bad)['hard_service_conditions_hold'])
    bad=deepcopy(cfg);bad['application']['address_multiplier']=2
    try:calendar_audit(bad)
    except ValueError:check('non-permutation workload rejected',True)
    else:raise AssertionError('non-permutation workload accepted')

    # Stronger actual start-E implies weaker arrival-E on all allowed
    # causal start positions; no extra repair is inserted in an app write.
    arrival=10000;deadline=arrival+3000;duration=153
    valid=True
    for start in (arrival,arrival+400,deadline-duration):
        births=[arrival-1,arrival+1,start+1,deadline-1]
        survivors=[b for b in births if b>=start]
        valid &= start>=arrival and start+duration<=deadline and all(b>=arrival for b in survivors)
    check('causal start-E leaves no survivor older than arrival',valid)

    # Arithmetic of full app-only costs on a small explicit workload.
    toy['mission_s']=F(1,1000)
    cost=full_cost(toy,accepted)
    reads=[1000+q*10002 for q in range(101) if 1000+q*10002<1000000]
    writes=[6000+q*10002 for q in range(101) if 6000+q*10002<1000000]
    counts={k:v*toy['mission_s'] for k,v in cost['full_cost_rates'].items()}
    check('toy workload count oracle for full pre-read/encode/write',
          counts['read_beats']==3*(len(reads)+len(writes)) and counts['write_beats']==3*(len(writes)+8)
          and counts['decodes']==len(reads)+len(writes) and counts['encodes']==len(writes)+8)
    check('no repair double write; initialization paid once',counts['turnarounds']==len(writes)+8 and counts['scrub_repairs']==0)
    check('all-history price retains useful work after A and pending',cost['post_A_and_bad_history_work_paid'] and cost['full_started_work_and_pending_paid']
          and cost['expected_core_SRAM_upper']==cost['all_history_core_SRAM_upper']>0)
    check('CPU/controller and energy not replaced by zero',cost['CPU_fraction_coefficients']['application_grants_ns']>0
          and cost['energy_coefficients_per_second']['transport_requests']>0 and cost['unknown_memory_addends'])
    check('unknown caps and scalar price stay unknown',cost['scalar_price'] is None and all(v is None for v in cost['unknown_hardware_caps'].values()))

    epoch=cfg['application']['epoch_ns'];D=cal['aperture_ns'];L=svc['peak_window_ns']
    for offset in (cfg['application']['first_ns'],cfg['application']['first_ns']+cfg['application']['write_offset_ns']):
        offers=[offset+q*epoch for q in range(-4,6)]
        endpoints=[x for v in offers for x in (v+D-1,v+D,v-L,v-L+1)]
        max_count=max(sum(t-D<=v<=t+L for v in offers) for t in endpoints)
        check(f'expanded-window endpoint count stream {offset}',max_count<=svc['offers_each_in_expanded_peak_window'])

    if result['Q_upper'] is not None:
        e=cfg['environment'];den=e['reference_words']*e['reference_bits'];T=F(cfg['mission_s'])
        b=F(e['reference_background_per_s'])/den;B=F(e['reference_peak_per_s'])/den;FS=F(e['reference_solar_mass'])/den
        M1=min(B*T,b*T+FS);M2=min(B*B*T,B*M1,b*b*T+(B+b)*FS)
        M3=min(B**3*T,B*B*M1,b**3*T+(B*B+B*b+b*b)*FS)
        p=F(cal['period_ns'],NS);d=F(D,NS)
        direct=F(cfg['lifetime_other_budget'])+cfg['words']*comb(44,3)*(p*p*M3+3*B*d*p*M2+3*B*B*d*d*M1)
        check('independent singleton cubic and every E-cross term',result['Q_upper']==min(F(1),direct))
        check('clean/direct/lifetime terms explicit',result['risk']['terms']['initial']==result['risk']['terms']['direct']==0
              and result['risk']['terms']['lifetime_exceptions']==F(cfg['lifetime_other_budget']))
        check('complete main cost has zero dedicated observation',all(result['full_price']['full_cost_rates'][k]==0 for k in
              ('scrub_reads','scrub_repairs','scrub_decisions','scrub_timer_events','cuts','captures','records')))
    return dict(count=len(checks),checks=checks,old_campaigns_repeated=False,monte_carlo_runs=0,
                risk_evaluated=result['Q_upper'] is not None,scientific_acceptance=False)
