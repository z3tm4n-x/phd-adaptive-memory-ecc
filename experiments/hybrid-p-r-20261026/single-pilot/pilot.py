"""Offline single-query controller consuming explicit visible certificates.

Certificates are conditional fixtures of the existing source/processed/health
contract, NOT values obtained from a hidden physical/drop journal. No new wire.
"""
from hashlib import sha256
from sources import bindings, encoded
from risk import M, USED, TAIL, BASE, RARE, THRESHOLD, ALPHA

CASES=('admit','count_reject','invalid','late')

def run_case(name, inp, cfg, hist, *, count_override=None, missing_prefix=False,
             guard_action=None, loss_action=None, incomplete=False, pending=False):
    encode,decode,close=bindings(hist)
    W=inp['fixed']['words']; cal=cfg['calendar']; svc=cfg['service']
    block=W*cal['g_ticks']+7*cal['frame_ticks']
    count = 4 if name=='count_reject' else 0
    if count_override is not None: count=count_override
    loss = (2 if name=='invalid' else None) if loss_action is None else loss_action
    total=0; invalid=False; g=0; reasons=set(); digest=sha256()
    raw_records=repairs=0; used_closed=0; checkpoint=[]
    for j in range(1,M+1):
        start=BASE*j*block; previous=(BASE*(j-1)+1)*block; end=(BASE*j+1)*block
        entry=g; records=[]
        if j<=count:
            g+=1
            records.append(decode(encode(dict(t=start+68,g=g,word=0,origin='control',causes=['ERR']))))
            repairs+=1
        if j==loss:
            g+=1
            # Existing coalesced GAP destroys ERR payload; restored now, invalid stays sticky.
            records.append(decode(encode(dict(t=start+232,g=g,word=3,origin='control',
                                              causes=['GAP','ERR','RESTORE'],covers=[g,g]))))
            repairs+=1
            invalid=True; reasons.add('loss in whole learning group; restore does not reset it')
        raw_records+=len(records)
        if j<=USED:
            # Offline slices of one closed group prefix. C may be accumulated
            # provisionally; no action uses it before the final health/prefix fence.
            # The historical close_counter's per-slice G is derived from that
            # certified ordered stream, not from simulator source truth.
            c=close(records,W=W,calendar=cal,service=svc,scan_start=start,
                    previous_decision=previous,decision_tick=end,entry_G=entry,
                    current_G=None if missing_prefix else g,processed_G=g,
                    prefix_certificate=not missing_prefix,guard_outside_scan=j==guard_action)
            used_closed+=1
            invalid |= c['invalid']; reasons.update(c['reasons'])
            if c['C'] is not None: total=min(THRESHOLD+1,total+c['C'])
            digest.update(f"{j}:{c['C']}:{int(c['invalid'])}:{g}\n".encode())
        # Tail C is not used. Loss up to the query still invalidates the entire group.
        if j in (1,2,4,USED,M):
            checkpoint.append(dict(action=j,processed_G=g,saturated_sum=total,invalid=invalid))
    deadline=(BASE*M+1)*block
    ready=deadline+BASE*block if name=='late' else deadline
    timely=ready<=deadline
    service_ok=not incomplete and not pending
    permit=service_ok and not invalid and timely and total<=THRESHOLD
    branch=('service_contract_violation' if not service_ok else
            'invalid' if invalid else 'late' if not timely else 'admit' if permit else 'count_reject')
    return dict(name=name,branch=branch,admit=permit,attempted_used_pass_counts=used_closed,
        certified_used_pass_counts=used_closed if not invalid else 0,
        C_saturated_at_4=total,sum_C_valid=not invalid,invalid=invalid,reasons=sorted(reasons),
        observed_prefix_contract='ASSUMPTION: coherent existing source/processed/health, usable on empty batches',
        prefix_mechanism_verified=False,hidden_generation_or_birth_log_used_by_decision=False,
        intermediate_C_provisional_until_whole_group_prefix_closed=True,
        query_source_healthy=True,query_epoch_known=True,
        service_preserved=service_ok,pending=pending,certificate_applicable=service_ok,
        ready_tick=ready,deadline_tick=deadline,timely=timely,
        next_period_blocks=RARE if permit else BASE,
        scheduled_queries=1,statistical_comparisons=int(service_ok and not invalid and timely),
        alpha_reserved=ALPHA,queries_after_restore=0,queries_after_extension=0,
        training_main_passes=M,startup_main_passes=1,uncounted_tail=TAIL,
        trace_sha256=digest.hexdigest(),checkpoints=checkpoint,
        fixture_counts=dict(raw_records=raw_records,repairs=repairs,
            loss_episodes=int(loss is not None),restores=int(loss is not None),false_records=0,
            extra_guard_reads=int(guard_action is not None)),
        fixture_cost_scope='directed path; unlisted parents/guards absent on this path only, not zero class costs',
        nominal_fixture_continues_to_T=True,no_state_phase_or_risk_reset=True)

def weak_E_witness(block):
    """Single-word physical witness kept separate from observations and policy."""
    start=BASE*M*block  # last unused tail action, word zero
    parent=start+20
    snapshot,release=start+68,start+124
    births={parent}
    first_err=bool([b for b in births if b<=snapshot])
    births={b for b in births if b>=start}  # weak E may retain a new birth
    residue_at_query=len(births)
    next_start=(BASE*M+RARE)*block
    second_err=bool(births)
    births={b for b in births if b>=next_start}
    return dict(first_ERR=first_err,second_ERR=second_err,parent_count=1,
        repair_transactions=int(first_err)+int(second_err),residual_at_query=residue_at_query,
        residual_after_next_E=len(births),tail_C_not_used=True,
        controller_reads_physical_residual=False,query_does_not_clean_memory=True,
        rare_K_paid_separately=True,
        late_parent_tick=parent,first_snapshot_tick=snapshot,first_release_tick=release,
        query_tick=(BASE*M+1)*block,next_main_visit_tick=next_start,
        extra_path_cost_over_zero_parent_fixture_ns=dict(bus=112,serial_core=112),
        these_exact_times_are_directed_witness_not_stochastic_samples=True)
