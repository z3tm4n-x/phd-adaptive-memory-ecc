"""Addressed checks using pinned RES-004 kernels, not an independent solver.

Only a short prescribed observation history is used; no missions or tuning.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys
import numpy as np
from checks_word import decode,encode

PIN={'model.py':'5bbb873592600d5224fd0d56ec08754233ada72a',
     'config.json':'21725338224f8b48b5198da078ef6ead6f688277'}


def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def run(cfg,reference):
    reference=Path(reference);identities={}
    for name,expected in PIN.items():
        data=(reference/name).read_bytes();actual=git_blob(data)
        if actual!=expected: raise ValueError(f'Input identity mismatch: {name}')
        identities[name]=dict(git_blob=actual,sha256=hashlib.sha256(data).hexdigest())
    spec=importlib.util.spec_from_file_location('accepted_unknown_d_model',reference/'model.py')
    model=importlib.util.module_from_spec(spec);sys.modules[spec.name]=model
    spec.loader.exec_module(model)
    original=json.loads((reference/'config.json').read_text())
    b=model.build_bank(original)
    args=model.controller_args(b);G=float(cfg['G'])
    guard=float(cfg['b_high_per_s'])*cfg['rmw_guard_window_ns']/1e9*3600
    slack=b.slack.copy()-guard/G
    minimum_initial=float(slack.min());assert minimum_initial>0
    q=b.initial;logs=np.zeros(len(q));rejected=np.zeros(len(q),dtype=np.bool_)
    rem=int(cfg['horizon_s']/original['controller']['time_tick_seconds'])
    backup=args[-1];tick=args[5]
    max_identity=max_backup_delta=max_ack_error=0.;identities_checked=0;traces=[]
    memory={w:encode(0x12345678) for w in range(max(cfg['budget_trace_counts']))}
    for step,injected in enumerate(cfg['budget_trace_counts']):
        active=model.retained(rejected)
        proposal,proposed_slack,_=model.choose(q,slack,active,rem,*args)
        assert b.periods[proposal]>=1
        late=step in cfg['budget_trace_late_steps']
        actual=backup if late else proposal
        # Construct errors in distinct words during idle, before the ACTUAL scan.
        # Carry the memory state; never reinitialize it at a pass boundary.
        count=0
        for w in range(injected): memory[w]^=1<<2
        for w in memory:
            latched,pos,due=decode(memory[w])
            if due: raise AssertionError('Unexpected first passage in the local witness')
            memory[w]=latched;count+=int(pos>0)
        assert count==injected
        new_slack=slack.copy();dt=min(rem,int(b.ticks[actual]));nr=rem-dt
        for j in range(len(q)):
            if not active[j]: continue
            delta,one,cur=model.action_delta(q,j,actual,rem,*args[:-1])
            db,_,_=model.action_delta(q,j,backup,rem,*args[:-1])
            max_backup_delta=max(max_backup_delta,abs(db))
            # Charge only the acknowledged action, never the speculative proposal.
            new_slack[j]=max(0.,slack[j]-delta)
            if not late: max_ack_error=max(max_ack_error,abs(new_slack[j]-proposed_slack[j]))
            expected_future=0.
            for y in range(2):
                unnormalized=q[j,:4]@b.kernels[j,actual,y]
                mass=unnormalized[:4].sum()
                stats=np.array([unnormalized[0]+unnormalized[2],
                    unnormalized[1]+unnormalized[3],unnormalized[4],unnormalized[5]])
                expected_future+=stats@b.value[j,nr]+mass*new_slack[j]
            max_identity=max(max_identity,abs(one+expected_future-cur-slack[j]))
            identities_checked+=1
        traces.append(dict(step=step,done_before_s=(36000-rem)*tick,count=count,
            proposed_period_s=float(b.periods[proposal]),executed_period_s=float(b.periods[actual]),
            late_rejected=late,
            count_origin='Distinct-word idle fault injection, actual read/decode/commit',
            minimum_active_slack_after=float(new_slack[active].min())))
        threshold=math.log(G/float(cfg['beta']))+original['controller']['test_log_margin']
        q=model.observe(q,logs,rejected,actual,count,b.kernels,threshold,True)
        slack=new_slack;rem=nr
    # Concrete kernel witness: updating with a requested but unexecuted action is wrong.
    p0=b.initial[0,:4]
    wrong=abs(float((p0@b.kernels[0,3,0])[:4].sum()-(p0@b.kernels[0,2,0])[:4].sum()))
    assert wrong>1e-6
    assert max_identity<1e-12 and max_backup_delta<1e-12 and max_ack_error<1e-12
    return dict(reference_files=identities,rmw_guard=guard,
        initial_slack_after_guard=minimum_initial,one_step_identities=identities_checked,
        maximum_identity_residual=max_identity,maximum_backup_delta=max_backup_delta,
        maximum_ack_slack_error=max_ack_error,wrong_action_zero_likelihood_difference=wrong,
        trace=traces,shared_dependencies='Accepted model, kernels, value tables, arithmetic backend',
        status='Constructed action-dependent word traces, not stochastic missions or new RES-004 validation')
