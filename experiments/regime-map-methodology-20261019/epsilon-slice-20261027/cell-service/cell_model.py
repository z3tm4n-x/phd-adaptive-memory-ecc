"""Small scheduling/price witness. No transport, hardware, tuning or Monte Carlo."""
from fractions import Fraction as F
from pathlib import Path
import hashlib,json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
NS=10**9
BLOCK=25701088
K=24000
W=131072
T=315576000

def ceil(x):
    x=F(x);return -(-x.numerator//x.denominator)
def sha(raw):return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()
def encoded(x):return (json.dumps(x,default=str,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()

def load():
    manifest=json.loads((HERE/'SOURCES.json').read_bytes())
    for path,h in manifest['source_sha256'].items():
        if sha((ROOT/path).read_bytes())!=h:raise ValueError('Changed source: '+path)
    snap=HERE/'reference-C3.json'
    ext=next(x for x in manifest['external_references'].values() if 'local_snapshot' in x)
    if sha(snap.read_bytes())!=ext['sha256']:raise ValueError('Changed C3 reference')
    source=json.loads((HERE.parent/'theory/result.json').read_bytes())
    reference=json.loads(snap.read_bytes())
    inp=json.loads((ROOT/'experiments/hybrid-p-r-20261026/inputs.json').read_bytes())
    cfg=json.loads((ROOT/inp['fixed']['source']).read_bytes())
    assert sha((ROOT/'experiments/hybrid-p-r-20261026/inputs.json').read_bytes())==source['canonical_input_sha256']
    return manifest,source,reference,inp,cfg

def ends(k):return tuple([2]+list(range(2+k,K,k))+[K])
def fence(j):return BLOCK*(1+j*K)
def slot(j,cal):return (j//cal['batch_size'])*cal['frame_ticks']+(j%cal['batch_size'])*cal['c_ticks']

class CellSelector:
    """Read-only schedules selected once at the fence, by a scalar report only.

    This reference policy does not implement the old OUR transport wrapper.
    Messages may invalidate future queries; they cannot emit a scrub command.
    Corruption of private epoch/calendar state is outside value-error B_C.
    """
    def __init__(self,kb,ks):
        self.plans={'base':ends(kb),'rare':ends(ks)}
        self.next_cell=0;self.selected={};self.bad_cells=set();self.scheduled_extra_E=0
    def begin(self,j,*,C=None,valid=False,ready_tick=None,prefix=False,healthy=False,
              main_complete=True,pending=False):
        if j!=self.next_cell:raise ValueError('Duplicate install or epoch reset')
        if not main_complete or pending:raise ValueError('Service violation; invalid is not a substitute')
        legal=isinstance(C,int) and not isinstance(C,bool) and C>=0
        past=not any(i in self.bad_cells for i in range(max(0,j-6),j))
        timely=ready_tick is not None and ready_tick<=fence(j)
        mode='rare' if j>=6 and legal and C<=4 and valid and prefix and healthy and past and timely else 'base'
        self.selected[j]=mode;self.next_cell+=1
        return self.plans[mode]
    def late_result(self,j,**report):
        if j not in self.selected:raise ValueError('Cell not selected')
        return self.plans[self.selected[j]]  # never union, restart or replace
    def observe_invalid(self,j,causes=()):
        # GAP+ERR+RESTORE remains sticky; no mutation of already installed plans.
        self.bad_cells.add(j)
    def restore(self):pass  # no reset of history, epoch, calendars or budgets

def timing(cfg,source):
    cal=cfg['calendar'];s=cfg['service'];obs=cfg['observation']
    xm,xp,J=map(F,(s['clock_lower'],s['clock_upper'],s['operation_endpoint_span_ns']))
    E=124*xp+J;R=68*xp+J
    last=slot(W-1,cal)
    drain=(BLOCK-last)*xm-J-E
    final=drain-cfg['adaptive']['source_to_fresh_rule_upper_ns']
    ap=(cal['frame_ticks']-cal['application_grant_phase_ticks'])*xm-J
    assert BLOCK%cal['frame_ticks']==0 and BLOCK//cal['frame_ticks']==16391
    assert (BLOCK*xp+J)/NS<=F(source['constants']['P_obs'])
    assert final>0 and cal['c_ticks']*xm-J>E
    # Same conservative 1ms envelope as PR250; retain even the unused write stream.
    aw=144*xp+J;L=cfg['constraints']['peak_window_ns']
    frames=2+ceil((F(L)+max(E,aw)+J)/(cal['frame_ticks']*xm))
    app_each=1+ceil(F(L+cfg['constraints']['application_deadline_ns'],cfg['application']['epoch_ns']))
    peak=(8*frames*E+app_each*(R+aw))/L
    return dict(block_ticks=BLOCK,frames_per_block=16391,cell_ticks=K*BLOCK,
        cell_fence_formula='BLOCK*(1+24000*j), fixed common epoch',
        physical_anchor='epoch + xi*tick; independent of parents and C at fixed xi; J bounds operation endpoints',
        first_scan_start_after_fence_lower_ns=BLOCK*xm-J,
        last_E_release_to_fence_lower_ns=drain,
        final_gate_install_after_fresh_lower_ns=final,
        per_record_packet_WCET_ns=obs['batch_ready_ns'],max_records_per_packet=1253,
        control_slot_slack_ns=cal['c_ticks']*xm-J-E,
        app_read_aperture_slack_ns=ap-R,conservative_app_write_aperture_slack_ns=ap-aw,
        old_potential_slot_peak_core_upper=peak,
        peak_extra_bus_core_fraction_limit=F(cfg['constraints']['peak_bus_fraction'])-peak,
        P_obs_accepted_s=source['constants']['P_obs'],H_lower=source['constants']['H_lower'],
        H_upper=source['constants']['H_upper'],
        fixed_anchors_are_additional_algorithmic_correspondence_not_implied_by_duration_bounds_alone=True,
        production_WCET_or_clock_independence_measured=False)

def calculate():
    manifest,src,ref,inp,cfg=load()
    xm,xp,J=map(F,(cfg['service'][x] for x in ('clock_lower','clock_upper','operation_endpoint_span_ns')))
    delta0=F(inp['fixed']['lifetime_other_budget']);dc=F('0.00005')
    hard=src['constants']['hard_reads'];mass=F(src['constants']['parent_mass'])
    N=src['constants']['query_upper'];Hlo=F(src['constants']['H_lower'])
    cut_rate=F(NS)/(cfg['observation']['cut_ns']*xm)+F(2,T)
    source_rate=F(NS)/(4*xm)+F(2,T)
    gate_rate=F(hard,T)
    rates_common=dict(cut_ready=cut_rate,potential_slot_gate=gate_rate,cell_close_and_choice=F(N,T),
                      rolling_ring_update=F(N,T),prefix_check_at_cell=F(N,T))
    q=inp['retained_quotas'];false=F(q['ordinary_false_expected_per_s'])*T
    ordinary_notices=q['ordinary_loss_episodes_upper']+q['recoveries_upper']
    all_rows=[]
    for old,reference in zip(src['rows'],ref['rows']):
        assert old['epsilon']==reference['epsilon']
        a=old['adaptive'];rv=old['rivals']
        row=dict(epsilon=old['epsilon'],mandatory=F(old['epsilon'])>=F('.001'),
                 rivals=rv,adaptive_status=a['status'])
        # The p-aware candidate has only bus exported in PR281; the same operation
        # counts give core here. No periods or physical masks are recalculated.
        ps=rv.get('p_schedule_candidate')
        if ps:
            nr=ps['reads_upper'];repair=min(F(nr),2*mass+(F(ps['Q_upper'])-delta0)*nr)
            row['p_schedule_core_upper']=(nr*(68*xp+J)+repair*56*xp)/(T*NS)+delta0*F(src['constants']['hard_core'])
            row['schedule_core_feasible_upper']=min(row['p_schedule_core_upper'],F(rv['constant_candidate']['known_core_upper']))
        else:row['schedule_core_feasible_upper']=F(rv['constant_candidate']['known_core_upper'])
        if 'k_base' not in a:
            row['conclusion']='Optional point: accepted sufficient adaptive bound fails; no impossibility claim.'
            all_rows.append(row);continue
        kb,ks=a['k_base'],a['k_rare'];eb,es=ends(kb),ends(ks)
        nb,ns=len(eb),len(es);mb=W*(1+N*nb)
        assert mb==a['main_reads_hard_on_good_execution'] and mb==reference['adaptive']['M_b']
        assert min(y-x for plan in (eb,es) for x,y in zip((0,)+plan,plan))>=2
        data=dict(k_base=kb,k_rare=ks,base_passes_per_cell=nb,rare_passes_per_cell=ns,
            base_final_interval_blocks=eb[-1]-eb[-2],rare_final_interval_blocks=es[-1]-es[-2],
            M_b=mb,N_cells=N,unsafe_double_install_passes=len(set(eb)|set(es)),
            Q_upper_at_design=a['Q_upper_at_deltaC_design'],risk_margin=a['risk_margin_at_design'],
            budgets={k:a[k] for k in ('alpha_total','alpha_each','zeta_total','delta0','deltaC_design_cap','deltaC_risk_allowable')},
            basic_settings={k:a[k] for k in ('u','U','threshold','eta','history_cells','cell_blocks')},
            coordinates={})
        # Raw-source witness: <= one ERR / transaction, <=2 per parent before A;
        # H0 pays q0 main tail, deltaC pays all Mb, extras all G, service failures
        # pay the existing physical source-edge cap. Ordinary loss/false separately.
        raw0=(F(a['main_repairs_upper'])+dc*mb+false+ordinary_notices)/T+delta0*source_rate
        assert raw0<source_rate
        pass_rate=F(1+N*nb,T)
        rates={**rates_common,'pass_close_and_prefix':pass_rate,'raw_record_bundle':raw0,
               'main_command_dispatch':F(mb,T)+delta0*gate_rate}
        data['handling']=dict(rates_good_or_explicitly_bad_capped=rates,
            raw_record_rate_formula='min(source_edge_rate, raw0 + G/T + v)',raw0=raw0,
            source_edge_rate_upper=source_rate,extra_raw_v_domain=[0,source_rate],
            raw_record_bundle='capture/source checks + record decode/map + increment + cause/invalid handling; no duplicate charge',
            slot_gate_vs_dispatch='slot eligibility and command preparation are distinct; word ECC is already in operation price',
            pass_closes_bound_includes_B_C_and_A=True,
            counts_on_uncovered_bad_controller='delta0 * controller_hard_cost; additional escape if not covered',
            unpriced_unit_costs='Every listed rate has separate nonnegative bus_ns/core_ns/CPU_ns/energy_J parameters',
            nonzero_CPU_energy_or_controller_measured=False,
            observed_group_sum_bits=(6*nb*W).bit_length(),cell_sum_bits=(nb*W).bit_length(),
            suggested_extra_policy_packed_bytes=144,retained_transport_loss_bytes=131136,
            code_stack_workspace_LUT_BRAM_bytes=None)
        for x in ('bus','core'):
            r=(48*xp+J)/NS if x=='bus' else (68*xp+J)/NS
            d=(56*xp+J)/NS if x=='bus' else 56*xp/NS
            ch=F(src['constants']['hard_'+x]);cb=F(mb,T)*(r+d)
            v=F(a[x+'_intercept_U0'])+dc*cb
            az=F(a[x+'_additional_invalid_coefficient']);ag=F(a[x+'_guard_read_coefficient'])
            oracle=reference['adaptive']['coordinates'][x]
            assert (cb,v,az,ag)==tuple(F(oracle[k]) for k in ('new_C_b','V_at_design_delta_C','A_z','A_G'))
            comps={}
            for target in ('constant','schedule'):
                lower=F(rv[target+'_read_'+x+'_lower'])
                a20=F(4,5)*lower-v;a30=F(7,10)*lower-v
                comp=dict(class_necessary_read_lower=lower,allowance_20=a20,allowance_30=a30,
                          bound_type='sufficient parametric comparison with full class necessary lower; not optimum',
                          passed_for_actual_hardware=False)
                assert a20==F(oracle['comparison'][target]['allowance_20'])
                if a20>0:
                    comp['axis_limits_not_simultaneous_or_assigned']=dict(
                        z=a20/az,extra_E_per_second=a20/(ag*T),delta_escape=a20/(ch-cb),
                        extra_unavailable_seconds=a20/az*N*Hlo,
                        instantaneous_veto_rate_if_7_queries_affected=a20*N/(az*7*T),
                        handler_unit_ns={key:a20*NS/rate for key,rate in rates.items()},
                        aggregate_handling_fraction=a20)
                comps[target]=comp
            data['coordinates'][x]=dict(V=v,U0=F(a[x+'_intercept_U0']),C_b=cb,deltaC_price=dc*cb,
                C_h=ch,escape_coefficient=ch-cb,A_z=az,A_G=ag,
                comparison=comps,formula='V + A_z*z + A_G*G + (C_h-C_b)*delta_escape + c_all_handling',
                full_handler_formula='sum(rate_i*cost_i_ns)/1e9 + (G/T+v)*cost_raw_bundle_ns/1e9 + (G/T)*cost_extra_dispatch_ns/1e9 + delta0*C_other_controller_hard + idle_controller')
        data['operation_account']=dict(
            main_reads_zero_extra_invalid_upper=F(a['main_reads_upper_excluding_additional_invalid'])+dc*mb+delta0*hard,
            main_reads_per_unit_z=W*N*(nb-ns),
            main_repairs_upper=F(a['main_repairs_upper'])+dc*mb+delta0*hard,
            main_control_expected_upper_including_bad_execution=mb+delta0*hard,
            extras='G additional reads + G worst-case repair + G decodes + extra dispatch; includes B_C and post-A',
            beats='3 per read, 3 per repair; turnaround once per repair',
            codec='20ns decode already in core R; repair encoding if required is in SERVICE E, not a second free operation',
            CPU_energy_use_same_counts=True)
        data['policy_extra_E']=dict(selected_reference_emits_extra_E=0,
            reason='Only installed main-calendar commands can start E; notifications only update observation state',
            legacy_OUR_wrapper_unchanged_would_not_establish_zero=True,
            external_guard_G_remains_parameter=True)
        data['additional_invalid']=dict(
            formula='z <= min(1,(D_extra/H_lower + 7*N_extra_episodes + N_late)/N)',
            scope='union bound for recognised additional unavailability; N_extra may include G and v*T only if their unresolved durations also enter D_extra',
            all_missing_prefix_means_z=1,ordinary_loss_false_already_in_E10=True,
            accepted_loss_bad_upper=F(q['ordinary_outage_fraction'])*T/Hlo+7*q['ordinary_loss_episodes_upper'],
            accepted_false_bad_upper=7*false,restore_cost_in_raw_and_state_handlers=True)
        all_rows.append({**row,'adaptive':data})
    app=cfg['application'];appN=ceil(F(T*NS-app['first_ns'],app['epoch_ns']))
    return dict(status='CONDITIONAL_CELL_SERVICE_AND_COMPLETE_PARAMETER_REGION',
        acceptance_or_hardware_gain_claimed=False,direction_A_closed=False,
        manifest_sha256=sha((HERE/'SOURCES.json').read_bytes()),
        implementation_sha256={f:sha((HERE/f).read_bytes()) for f in ('cell_model.py','run.py','test_cell.py','plot.py')},
        constants=dict(W=W,T=T,N_h=hard,delta0=delta0,deltaC_design=dc,source_edge_rate=source_rate,rate_basis=rates_common),
        timing=timing(cfg,src),rows=all_rows,
        shared_application=dict(reads=appN,useful_writes=0,
            bus_fraction_upper=appN*(48*xp+J)/(T*NS),core_fraction_upper=appN*(68*xp+J)/(T*NS),
            init_encodes=W,init_write_beats=3*W,
            init_bus_fraction_upper=W*(56*xp+J)/(T*NS),init_core_fraction_upper=W*(76*xp+J)/(T*NS),
            CPU_energy_dispatch_headers_buffers='separate common terms, not zero; full39 codec counted once'),
        full_vector=dict(CPU='sum E[N_i]*cpu_i_ns/(T*1e9)+idle_CPU+delta0*CPU_hard; unknown capacity/coefficients',
            energy='sum E[N_i]*energy_i_J + T*idle_W + delta0*energy_hard; no inferred energy gain',
            codec='main and G decodes, main/G repair writes, app decodes and init encodes; no double codec charge',
            memory='6W encoded bytes + old transport/loss131136 + proposed policy144 + cFE/stacks/code/codec/workspace unknown',
            processing_peak='packet work <=3900ns incl new work; final gate/install <=1270.8848ns; shared SRAM window/peak constraints also required'),
        unchanged=dict(scientific_input=src['canonical_input_sha256'],settings='PR281 threshold4 only, all budgets/periods preserved',old_A11_not_run=True),
        remainder=['fixed physical anchors require scheduled starts, not release/ERR driven drift',
                   'source/processed/health binding, packet/final WCET and nonzero processing coefficients remain conditional',
                   'epoch/queue corruption outside covered G0 keeps delta_escape coefficient',
                   '20percent at .01 only inside the displayed joint region; .1/.001 comparison insufficient, .0001 adaptive uncertified'])
