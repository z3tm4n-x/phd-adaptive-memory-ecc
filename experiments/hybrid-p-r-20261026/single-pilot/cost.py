"""Exact calendar counts and explicit whole-horizon cost coordinates."""
from fractions import Fraction as F
from sources import NS,ceil
from risk import M,BASE,RARE,USED,DELTA_C_REQUIREMENT

def scheduled_reads_before(ticks,W,cal,block,admit=False):
    """Started reads in [0,ticks), including the terminal incomplete scan."""
    ticks=F(ticks)
    if ticks<=0: return 0
    period=BASE*block
    full=int(ticks//period); rem=ticks-full*period
    assert W%cal['batch_size']==0
    count=full*W
    for phase in range(cal['batch_size']):
        count+=max(0,min(W//cal['batch_size'],ceil((rem-phase*cal['c_ticks'])/cal['frame_ticks'])))
    if admit:
        # Only the 5999 scans strictly before the rare terminal scan are removed.
        first=(BASE*M+BASE)*block
        for scan in range(RARE//BASE-1):
            dt=ticks-first-scan*period
            for phase in range(cal['batch_size']):
                count-=max(0,min(W//cal['batch_size'],ceil((dt-phase*cal['c_ticks'])/cal['frame_ticks'])))
    return count

def read_count_fast(ticks,W,cal,block,admit=False):
    """O(8) at full T: both ends of removed region are strictly inside horizon."""
    n=scheduled_reads_before(ticks,W,cal,block)
    if admit:
        last_removed=(BASE*M+RARE-BASE)*block+(W//8-1)*cal['frame_ticks']+7*cal['c_ticks']
        if ticks<=last_removed:
            return scheduled_reads_before(ticks,W,cal,block,True)
        n-=(RARE//BASE-1)*W
    return n

def calculate(inp,cfg,risk,cases,hist):
    W=inp['fixed']['words']; T=F(inp['fixed']['mission_s']); cal=cfg['calendar']; svc=cfg['service']
    obs=cfg['observation']; app=cfg['application']; block=risk['timing']['block_ticks']
    xm,xp,J=map(F,(svc['clock_lower'],svc['clock_upper'],svc['operation_endpoint_span_ns']))
    tnom=T*NS; tlo=(tnom-J)/xp; thi=(tnom+J)/xm
    base=read_count_fast(tnom,W,cal,block)
    base_lo=read_count_fast(tlo,W,cal,block); base_hi=read_count_fast(thi,W,cal,block)
    saving=(RARE//BASE-1)*W
    hard=W*(ceil(T/((W*cal['g_ticks']*xm-J)/NS))+2)
    rb=3*svc['read_beat_ns']; dr=3*svc['write_beat_ns']+svc['turnaround_ns']
    rc=rb+svc['decode39_ns']; ec=rc+dr
    rbp=rb*xp+J; dbp=dr*xp+J
    rcp=rc*xp+J; ecp=ec*xp+J; dcp=ecp-rcp
    n_app=ceil((T*NS-app['first_ns']-app['read_offset_ns'])/app['epoch_ns'])
    initial_core=F(W)*(svc['encode39_ns']+dr)*xp+W*J
    initial_bus=F(W)*dr*xp+W*J
    hard_cuts=ceil(T*NS/(obs['cut_ns']*xm))+2
    hard_raw=ceil(T*NS/(4*xm))+2
    fp=F(inp['proposed_environment']['background'])*T+F(inp['proposed_environment']['total_solar_mass'])
    q=risk['exact']['Q_upper_if_example_requirement_met']
    de=F(inp['fixed']['lifetime_other_budget'])+DELTA_C_REQUIREMENT
    repair_upper=2*fp+q*hard
    assert repair_upper<hard
    out=[]
    for case in cases:
        admit=case['admit']; reads=base-saving*admit
        nr=case['fixture_counts']['repairs']; guard=case['fixture_counts']['extra_guard_reads']
        read_total=reads+guard
        decode=read_total+n_app
        # A directed no-extra-event path is not a point estimate of class mean cost.
        out.append(dict(branch=case['branch'],startup_reads=W,learning_reads=M*W,
            remaining_reads=reads-(M+1)*W,main_reads_nominal=reads,
            main_reads_physical_lower=base_lo-saving*admit,
            main_reads_physical_upper=base_hi-saving*admit,
            removed_passes=5999*admit,removed_reads=saving*admit,
            path_fixture_extra_guards=guard,path_fixture_repairs=nr,
            path_nominal_protection_bus_s=F(read_total*rb+nr*dr,NS),
            path_nominal_protection_core_s=F(read_total*rc+nr*dr,NS),
            path_nominal_full_bus_s=F(read_total*rb+nr*dr+n_app*rb+W*dr,NS),
            path_nominal_full_core_s=F(read_total*rc+nr*dr+n_app*rc+W*(svc['encode39_ns']+dr),NS),
            full_read_beats=3*decode,full_write_beats=3*(nr+W),
            full_decodes=decode,initial_encodes=W,
            path_unknown_cost='add cuts/raw handling/counter/timers/controller/CPU/energy; not zero',
            price_continues_after_A=True))
    # Shared expected upper: bad executions may consume the hard stream. No independence.
    # p_g = P(good execution AND admission) for each fixed admissible r/channel.
    # G_g counts extra reads on good executions only (incl loss/false/restore/hold).
    return dict(units='counts; physical seconds; resource fractions of entire T',
      branch_paths=out, calendar=dict(nominal_base_started_reads=base,
        physical_base_started_reads_lower=base_lo,physical_base_started_reads_upper=base_hi,
        terminal_partial_scan_reads=base%W,terminal_started_work_paid_in_full=True,
        nominal_base_full_scans=base//W,retained_base_phase_after_rare=True,
        saved_main_passes_if_admitted=5999,saved_main_reads_if_admitted=saving,
        saved_fraction_of_base_reads=F(saving,base),
        saved_nominal_bus_seconds=F(saving*rb,NS),saved_nominal_core_seconds=F(saving*rc,NS),
        saving_is_main_read_component_only=True,
        all_history_slot_cap=hard,all_history_resource_release_required=True),
      shared_price=dict(application_read_count=n_app,useful_writes=0,
        app_bus_upper_fraction=F(n_app)*rbp/(T*NS),app_core_upper_fraction=F(n_app)*rcp/(T*NS),
        initial_bus_upper_fraction=initial_bus/(T*NS),initial_core_upper_fraction=initial_core/(T*NS),
        app_payload_nominal_ns_each=32,app_ECC_increment_nominal_ns_each=36,
        ECC_already_in_full_core_read=True,app_read_repairs=0,app_ERR=0,
        initial_encodes=W,initial_write_beats=3*W,initial_outside_0_paid_amortized_over_T=True,
        initial_read_counter_or_channel_does_not_reset_memory=True),
      expected_upper=dict(scope='each fixed admissible r and allowed channel; no distribution over r',
        variables={'p_g':'P(good execution and the single admission), unknown in [0,1]',
                   'G_g':'E[extra guard reads on good execution], unknown in [0,Nhard]',
                   'delta_exec':'<=delta0+delta_C, only if stated service and counter coverage hold',
                   'delta_C':None},
        read_formula='S=min(Nhard,Nbase_plus-D*p_g+G_g+delta_exec*Nhard)',
        repair_formula='H=min(S,2*Fparent+U_joint*Nhard)',
        protection_pure_bus_fraction='(Rbus_plus*S+Drepair_bus_plus*H)/(T*1e9)+B_controller',
        protection_serial_core_fraction='(Rcore_plus*S+Drepair_core_plus*H)/(T*1e9)+C_controller',
        coefficients=dict(Nhard=hard,Nbase_plus=base_hi,D=saving,Fparent=fp,
            Rbus_plus_ns=rbp,Drepair_bus_plus_ns=dbp,Rcore_plus_ns=rcp,Drepair_core_plus_ns=dcp,
            U_joint_if_deltaC_requirement=q,delta_exec_if_deltaC_requirement=de,
            repair_upper_before_min_if_deltaC_requirement=repair_upper),
        no_guard_no_credit_component_upper_if_deltaC_requirement=dict(
            reads=base_hi+de*hard,
            pure_bus_fraction=(rbp*(base_hi+de*hard)+dbp*repair_upper)/(T*NS),
            serial_core_fraction=(rcp*(base_hi+de*hard)+dcp*repair_upper)/(T*NS),
            condition='G_g=0 only as a labelled algebraic component, p_g=0; not physical full mean'),
        guard_cause_partition='G_g=G_ERR+G_false+G_loss+G_restore+G_hold+G_veto after disjoint attribution; overlapping causes counted once',
        old_hold_coefficients_reused=False,loss_restore_false_not_mandatory_lower_cost=True,
        repair_factor_two_preserves_weak_E=True,no_stop_after_A=True),
      hard_upper=dict(protection_bus_fraction=F(hard)*(rbp+dbp)/(T*NS),
        protection_core_fraction=F(hard)*ecp/(T*NS),
        including_app_init_bus_fraction=(hard*(rbp+dbp)+n_app*rbp+initial_bus)/(T*NS),
        including_app_init_core_fraction=(hard*ecp+n_app*rcp+initial_core)/(T*NS),
        unknown_controller_CPU_energy_not_included_as_zero=True,
        meaning='all potential slots always-E, including all causes and post-A; not predicted mean'),
      observation=dict(cuts_upper=hard_cuts,raw_records_upper=hard_raw,
        transported_record_bytes_upper=32*hard_raw,bytes_are_moved_not_resident=True,
        valid_used_pass_finalizations=USED,group_decisions=1,online_bound_inversions=0,
        full_T_slot_gates_upper=hard,
        false_notifications_expected_upper=F(inp['retained_quotas']['ordinary_false_expected_per_s'])*T,
        ordinary_outage_s_upper=F(inp['retained_quotas']['ordinary_outage_fraction'])*T,
        ordinary_loss_episodes_upper=inp['retained_quotas']['ordinary_loss_episodes_upper'],
        restores_upper=inp['retained_quotas']['recoveries_upper'],
        extra_raw_veto_expected=None,episode_count_is_not_raw_confirmation_count=True,
        source_generation_bits_required=hard_raw.bit_length(),
        raw_records_expected=None,logical_ERR_expected_upper_if_deltaC_requirement=repair_upper),
      resource_vector=dict(raw_data_SRAM_bytes=6*W,retained_transport_and_loss_bytes=131136,
        example_full_counter_bytes=64,example_extra_group_state_bytes=32,
        example_metadata_total_bytes=131232,group_sum_bits=3,
        packed_layout_is_not_compiler_or_hardware_resource_measurement=True,
        CPU_formula='sum_i E[N_i]*c_i_ns/(T*1e9), plus idle CPU; all c_i unknown',
        energy_formula='sum_i E[N_i]*e_i_J+T*idle_W; nonoverlapping increments; all e_i and idle_W unknown',
        disjoint_unit_cost_operations=['init encode/write','app read/decode','control read/decode',
            'repair increment','cut/ready','raw decode','ERR handler','FALSE handler',
            'GAP handler','RESTORE handler','extra veto handler','used pass close',
            'saturating group add','one decision/install','calendar gate/timer'],
        CPU_ns_per_operation=None,energy_J_per_operation=None,idle_W=None,
        controller_bus_average=None,controller_bus_peak=None,controller_core_fraction=None,
        code_stack_heap_bytes=None,LUT=None,BRAM=None,WCET_measured=None),
      lower_price_reference=dict(source='PR272@ed85, PRICE.md and result.json; not recomputed',
        interpretation='conditional lower read price of declared deterministic schedule class, not optimum',
        published_conservative_bus_percent_lower='0.4854605',
        published_conservative_core_percent_lower='0.6898650',
        equality_or_gain_inferred=False),
      full_mean_gain_claimed=False,full_scalar_price_available=False)
