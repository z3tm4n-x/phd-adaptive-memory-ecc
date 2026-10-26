"""Offline applicability predicates and microhistories, not a new transport."""
from fractions import Fraction as F
from common import NS,ceil,wire_functions

def slot_start(j,calendar):
    return j//calendar['batch_size']*calendar['frame_ticks']+j%calendar['batch_size']*calendar['c_ticks']

def close_counter(records, *, W, calendar, service, scan_start, previous_decision, decision_tick,
                  entry_G, current_G, processed_G, prefix_certificate,
                  source_healthy=True, unknown_at_entry=False, epoch_known=True,
                  guard_outside_scan=False, main_pass_complete=True, pending=False,
                  decision_computation_ready=True):
    """Sufficient local binding. Inputs are explicit visible fields/contracts.
    No physical births, drop/arrival annotations or simulator journals are read.
    A missing guarantee yields invalid; invalid never authorizes a new action.
    """
    invalid=[]
    if not prefix_certificate or current_G is None:
        invalid.append('no coherent closed-prefix certificate')
    elif current_G != processed_G:
        invalid.append('unprocessed source generation, including possible lost tail')
    if not source_healthy: invalid.append('source health false')
    if unknown_at_entry: invalid.append('unknown interval already active')
    if not epoch_known: invalid.append('source/calendar epoch not established')
    if guard_outside_scan: invalid.append('extra E outside mandatory scan')
    if not main_pass_complete: invalid.append('mandatory scan incomplete')
    if pending: invalid.append('pending at decision boundary')
    if not decision_computation_ready: invalid.append('decision deadline not established')
    expected=entry_G+1; count=0; last_j=-1; last_source=previous_decision
    xm=F(service['clock_lower']);J=F(service['operation_endpoint_span_ns'])
    # Conservative mapping envelope in shared source-clock ticks:
    # 4 ticks quantization + both endpoint errors. Adjacent slots cannot alias.
    guard=F(4)+2*J/xm
    R_nom=3*service['read_beat_ns']+service['decode39_ns']
    for r in records:
        g=r['g'];t=r['t'];causes=set(r['causes'])
        if g != expected:
            invalid.append('G hole, duplicate, stale or reordered delivery')
        expected=max(expected,g+1)
        if t<previous_decision:
            invalid.append('record predates the closed entry prefix')
        if t>decision_tick or t<last_source:
            invalid.append('source-time outside decision fence or out of order')
        last_source=max(last_source,t)
        if 'GAP' in causes:
            invalid.append('GAP in observation interval; RESTORE does not erase it')
        if 'FALSE' in causes:
            invalid.append('explicit FALSE notification: conservative skip')
        if 'ERR' not in causes: continue
        if 'word' not in r or r.get('origin')!='control':
            invalid.append('ERR has no unambiguous control transaction payload')
            continue
        word=r['word']
        if not 0<=word<W:
            invalid.append('word outside bank')
            continue
        j=(pow(3,-1,W)*word)%W
        start=scan_start+slot_start(j,calendar)
        if not start-guard<=t<=start+R_nom+guard:
            invalid.append('ERR source-time does not identify the mandatory visit')
            continue
        if j<=last_j:
            invalid.append('repeated visit identifier or reordered transaction')
            continue
        last_j=j;count+=1
    if expected-1!=processed_G:
        invalid.append('records do not cover the processed prefix since entry')
    if count>W: invalid.append('counter overflow')
    return dict(C=None if invalid else count,invalid=bool(invalid),reasons=sorted(set(invalid)),
                full_service_boundary=main_pass_complete and not pending,
                no_action_authorized=True)

def calculate(inp,cfg,history):
    W=inp['fixed']['words'];T=F(inp['fixed']['mission_s']);cal=cfg['calendar'];s=cfg['service']
    xm,xp,J=map(F,(s['clock_lower'],s['clock_upper'],s['operation_endpoint_span_ns']))
    fresh=F(inp['diagnostic']['counter_drain_source_ns'])
    frames=ceil((fresh+J)/(cal['frame_ticks']*xm))
    ticks=W*cal['g_ticks']+frames*cal['frame_ticks']
    Pminus=(ticks*xm-J)/NS;Pplus=(ticks*xp+J)/NS
    last=slot_start(W-1,cal)
    Eplus=(3*s['read_beat_ns']+s['decode39_ns']+3*s['write_beat_ns']+s['turnaround_ns'])*xp+J
    drain=(ticks-last)*xm-J-Eplus
    finalization=drain-fresh
    source_guard=F(4)+2*J/xm
    Rnom=3*s['read_beat_ns']+s['decode39_ns']
    encode,decode=wire_functions(history['adapter.py'])
    raw=lambda t,g,word=0,causes=('ERR',),**extra: encode(dict(t=t,g=g,word=word,origin='control',causes=list(causes),**extra))
    kwargs=dict(W=W,calendar=cal,service=s,scan_start=0,previous_decision=0,
                decision_tick=ticks,entry_G=0,current_G=2,processed_G=2,prefix_certificate=True)
    records=[decode(raw(68,1,0)),decode(raw(232,2,3))]
    complete=close_counter(records,**kwargs)
    empty_args=dict(kwargs,current_G=0,processed_G=0)
    empty=close_counter([],**empty_args)
    # Wire-only consumer sees [] in both histories; actual count differs.
    invisible=decode(raw(68,1,0))
    tail_with_G=close_counter([],**dict(kwargs,current_G=1,processed_G=0))
    tail_wire_only=close_counter([],**dict(kwargs,current_G=None,processed_G=0,prefix_certificate=False))
    mixed=decode(raw(68,1,0,causes=('GAP','ERR','RESTORE'),covers=[1,1]))
    mixed_result=close_counter([mixed],**dict(kwargs,current_G=1,processed_G=1))
    doubled=close_counter([records[0],records[0]],**dict(kwargs,current_G=1,processed_G=1))
    no_scrub_stats=close_counter(records,**dict(kwargs,guard_outside_scan=True))
    source_ticks_max=ceil(T*NS/(4*xm))+2
    counts=dict(full_decisions_upper=int(T/Pminus),started_blocks_upper=ceil(T/Pminus),
                old_nominal_floor_for_comparison_only=int(T/(F(ticks,NS))),
                source_G_upper=source_ticks_max,source_ticks_upper=source_ticks_max)
    # One possible explicit packed persistent layout; no workspace/WCET claim.
    layout=dict(pass_id=8,previous_decision_tick=8,scan_start_tick=8,decision_tick=8,
                C=4,last_transaction_index=4,entry_processed_G=8,closing_current_G=8,
                invalid_causes=4,flags=4)
    return dict(
      status='CONDITIONAL_LOCAL_BINDING_SPECIFIED_EXISTING_WIRE_UNCHANGED',
      production_full_counter_implemented=False,wire_only_completeness=False,
      source_to_counter_binding_verified_in_hardware=False,
      timing=dict(block_ticks=ticks,P_lower_s=Pminus,P_upper_s=Pplus,
                  drain_after_last_release_lower_ns=drain,source_to_fresh_upper_ns=fresh,
                  post_fresh_finalize_invert_install_budget_lower_ns=finalization,
                  condition='new per-packet work inside existing 3900 ns; finalization/inversion/install before boundary within residual window, else pre-certified fallback',
                  timestamp_mapping_guard_ticks=source_guard,
                  timestamp_aperture_ticks=Rnom+2*source_guard,
                  minimum_control_start_gap_ticks=cal['c_ticks'],
                  source_epoch_max_drift_from_nominal_s=(xp-1)*T+J/NS,
                  physical_time_rule='clip xi_minus*tick-J and xi_plus*tick+J to mission; do not integrate p on nominal times without clock binding',
                  nominal_k1_free_time_after_decision_ns=0),
      counts=counts,
      state=dict(counter_bits=(W+1).bit_length(),pass_id_bits=(counts['started_blocks_upper']+1).bit_length(),
                 raw_ns_time_bits=int(T*NS).bit_length(),wire_source_ticks_bits=source_ticks_max.bit_length(),
                 source_G_bits=source_ticks_max.bit_length(),
                 persistent_layout_bytes=layout,persistent_counter_bytes=sum(layout.values()),
                 retained_transport_and_loss_bytes=131136,
                 total_retained_plus_example_counter_bytes=131136+sum(layout.values()),
                 solver_workspace_bytes=None,code_bytes=None,CPU_ns=None,energy_J=None,
                 reuse_of_existing_64_loss_bytes=False),
      witnesses=dict(complete_two_ERR=complete,healthy_closed_empty=empty,
                     identical_wire_empty_vs_dropped_tail=dict(wire_records_both=[],true_C=[0,1],
                         hidden_record_for_proof_only=invisible,receiver_must_not_read_hidden_record=True,
                         with_existing_generation_gate=tail_with_G,without_prefix_binding=tail_wire_only),
                     simultaneous_GAP_ERR_RESTORE=dict(decoded=mixed,result=mixed_result,
                         receiver_unknown_after_restore_can_be_false=True,interval_invalid_must_stay_true=True),
                     duplicate_delivery=doubled,guard_outside_main_pass=no_scrub_stats),
      obligations=dict(full_prefix='atomic processed/current generation and source-health fence, including empty ready and lost-tail alarm contract',
                       interval_invalid='sticky over whole observation interval; RESTORE never repairs missing historical C',
                       transaction='bind decoded word/origin and shared source-time to own fixed scan; reject ambiguity/repeated visit',
                       epoch='single mission epoch, no source time/G reset or wrap; keep pass identifier locally',
                       guard='log own extra E; invalidate observation without changing mandatory scan/phases/pending',
                       counter_errors='prove coverage by joint old execution bound or provide delta_C inside epsilon',
                       new_delta_C=None),
      no_new_transport=True,no_hardware_measurement=True,no_hybrid_admission_claim=True)
