"""T135: read-only applicability check of r4 against the final T104 SHA.

No Q/price search, RTL, solver, STA, or physical campaign is run.
Published proof/STA results are bound to source hashes, not re-proved here.
"""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
THEORY='fa4b4c150e668422e36a6c7a0e30810b26604e7c'
ENGINEER='8ce9104462d34f6d7daede73b3346e6dfa91f19a'
PREVIOUS_ENGINEER='99c0a4147048da57c8b59f6a2d4cfd5183cbcf0f'
BASE='experiments/t104-rtl-resume/'
OWN='experiments/t135-demo-operating-point/'
PINS={}


@lru_cache(None)
def git_bytes(sha,path):
    return subprocess.check_output(['git','show',f'{sha}:{path}'],cwd=ROOT)


def engineer(path):
    raw=git_bytes(ENGINEER,BASE+path)
    PINS[BASE+path]=hashlib.sha256(raw).hexdigest()
    return raw


def data(path):
    return json.loads(engineer('physical/'+path))


def decode(x):
    if isinstance(x,dict):
        if 'rational' in x:return F(x['rational'])
        return {k:decode(v) for k,v in x.items()}
    if isinstance(x,list):return [decode(v) for v in x]
    return x


def serial(x):
    if isinstance(x,F):return str(x)
    if isinstance(x,dict):return {k:serial(v) for k,v in x.items()}
    if isinstance(x,list):return [serial(v) for v in x]
    return x


def source_digest(path):
    return hashlib.sha256(engineer(path)).hexdigest()


def repeat_bounds():
    old=engineer('integrated/bounds.py')
    assert old==git_bytes(PREVIOUS_ENGINEER,BASE+'integrated/bounds.py')
    mod=types.ModuleType('integrated.bounds')
    mod.__file__=str(ROOT/BASE/'integrated/bounds.py')
    exec(compile(old,mod.__file__,'exec'),mod.__dict__)
    saved={n:sys.modules.get(n) for n in ('integrated','integrated.bounds')}
    pkg=types.ModuleType('integrated');pkg.__path__=[]
    sys.modules['integrated']=pkg;sys.modules['integrated.bounds']=mod
    scope={'__name__':'read_only_physical_bounds','__file__':str(ROOT/BASE/'physical/bounds.py')}
    try:
        exec(compile(engineer('physical/bounds.py'),scope['__file__'],'exec'),scope)
        result=scope['calculate']()
        encoded=json.dumps(scope['encode'](result),indent=2,ensure_ascii=False)+'\n'
        assert encoded.encode()==engineer('physical/outputs/bounds.json')
        return result
    finally:
        for name,value in saved.items():
            if value is None:sys.modules.pop(name,None)
            else:sys.modules[name]=value


def proof_bindings():
    rows={}
    source={
        'backend':'physical/e_backend_registered.sv',
        'candidate':'physical/candidate_link.sv',
        'guard':'physical/candidate_link.sv',
        'crc':'physical/candidate_link.sv',
        'history':'physical/executor.sv','chain':'physical/executor.sv',
        'join':'physical/executor.sv','map':'physical/address_map.sv',
        'transport':'registered/handshake_channel.sv',
        'progress':'registered/handshake_channel.sv'}
    for name,path in source.items():
        d=data('outputs/proofs/'+name+'.json')
        digest=source_digest(path)
        if name=='guard':
            assert d['status']=='proved' and d['source_sha256']==digest
            rows[name]='reported induction; arbitrary packets, per-bit generation factorization'
            continue
        labels=('slow-fast','fast-slow') if name=='progress' else (
            ('actual','prevalidated') if name=='backend' else ('normal',) if name=='map' else ('actual',))
        for label in labels:
            case=next(c for c in d['cases'] if c['case']==label)
            assert case.get('status')=='proved' or case.get('proved') is True or case.get('passed') is True
            assert case.get('counterexample',False) is False
            assert case.get('source_sha256',d.get('source_sha256'))==digest
        rows[name]='reported normal cases verified and source hash matched'
    components=data('outputs/proofs/components.json')
    mapping={'counter':'physical/segmented_counter.sv','frame':'physical/frame_engine.sv',
             'warmup':'physical/frame_engine.sv','rule':'integrated/slow_rule.sv'}
    for name,path in mapping.items():
        case=next(c for c in components['cases'] if c['case']==name)
        assert case['status']=='proved' and case['source_sha256']==source_digest(path)
    rows['components']='reported counter/frame/warmup/production-rule induction, source hashes matched'
    assert engineer('integrated/slow_rule.sv')==git_bytes(PREVIOUS_ENGINEER,BASE+'integrated/slow_rule.sv')
    return rows


def report():
    r4=json.loads(git_bytes(THEORY,OWN+'report-r4.json'))
    contract=json.loads(git_bytes(THEORY,OWN+'common-contract.json'))
    rec=contract['recommended']
    unchanged={}
    for path in [OWN+'common-contract.json',OWN+'report-r4.json',OWN+'config.json',
                 OWN+'integrated_check.py',*r4['accepted_source_sha256']]:
        raw=(ROOT/path).read_bytes()
        assert raw==git_bytes(THEORY,path)
        unchanged[path]=hashlib.sha256(raw).hexdigest()
    for name in ('HANDOFF.md','VALIDATION.md','CONTRACT.md','bounds.py',
                 'prove_progress.py','prove_transport.py'):
        engineer('physical/'+name)
    bounds=repeat_bounds();app=bounds['application'];history=bounds['history']
    candidates=bounds['candidates']
    assert bounds['unchanged_theory_inputs']['T135_r4']==THEORY
    for name,key in [('R','R_s'),('E','E_s'),('read32','read32_s'),
                     ('observed_write32','observed_write32_s')]:
        assert bounds['operations_ns'][name]==F(rec[key])*10**9
    assert app['inbound_to_eligible_ns']==F('177.001760')<=F(rec['application_inbound_s'])*10**9
    assert app['outbound_ns']==F('232.502320')<=F(rec['application_outbound_s'])*10**9
    assert app['backpressure_budget_ns']==F(rec['backpressure_s'])*10**9
    recycle=app['post_response_recycling']
    assert recycle['three_FWFT_and_credit_composition_ns']==F('581.0058')<1000
    assert recycle['remaining_after_response_and_tail_ns']==F('96221.930376')>0
    assert recycle['allocated_tail_ns']<F(rec['application_transport_recycle_after_response_budget_s'])*10**9
    assert app['response_with_10pct_ns']==F(r4['rows']['selected_r3_original']['resources']['response_upper'])*10**9
    assert app['bus_any_1ms_upper']==F(r4['rows']['selected_r3_original']['resources']['whole_bus_peak'])
    assert history['full_flag_occupancy_upper']==275<history['FIFO_depth']==512
    assert history['last_history_to_fresh_applicable_including_loss_CDC_ns']<10000
    assert candidates['with_10pct_ns']<F(rec['candidate_precompute_and_delivery_s'])*10**9
    assert candidates['roundtrip_budget_ns']<1568*F('.99999')
    assert bounds['generation']['mission_fast_edges_upper']<=rec['generation_clock_bound']['max_edges_upper']<2**57
    proofs=proof_bindings()
    sta=data('outputs/sta.json')
    assert sta['part']=='xc7z020clg484-1' and sta['top']=='board_top'
    assert sta['frequency_MHz']==[250,50] and sta['uncertainty_ns']=={'setup':.5,'hold':.1}
    assert sta['timing']['setup_ns']>=.1 and sta['timing']['hold_ns']>0
    assert all(v==0 for v in sta['check_timing'].values())
    for path,digest in sta['compiled_inputs'].items():
        assert source_digest(path)==digest
    io=decode(data('outputs/io.json'))
    assert len(io['checks'])==20 and io['all_met']
    for c in io['checks']:
        assert c['met'] and c['margin_ns']==c['available_lower_ns']-c['required_min_ns']>0
    assert min(c['margin_ns'] for c in io['checks'])==F('.346600')
    top=engineer('physical/board_top.sv').decode()
    assert 'phase==9999' in top and 'phase==5000' in top
    assert '.src_in(loss_switch),.dest_clk(slow_clk),.dest_out(loss_slow)' in top
    assert 'DEST_SYNC_FF(3),.SRC_INPUT_REG(0)' in top
    # Optional outer board switch cut: three destination stages plus one
    # conservative use-edge, under the SAME declared digital CDC premise.
    outer_loss=4*20*F('1.00001')+F('.5')
    raw_loss=history['last_history_to_fresh_applicable_including_loss_CDC_ns']+outer_loss
    assert raw_loss<10000
    shell_nominal_total=F(10**9,5000*20)
    shell_fast_spacing=5000*20*F('.99999') # admissible zero-jitter witness
    assert shell_nominal_total>rec['mean_reads_s']+rec['mean_writes_s']
    assert shell_fast_spacing<F(10**9,rec['application_joint_rate_s'])
    return dict(theory_sha=THEORY,engineer_sha=ENGINEER,
        verdict='r4 applies to the executor under r4 inputs; NOT a lifetime-price certificate for continuous board_top timing-shell traffic',
        recalculated_Q_or_price=False,RTL_solver_STA_rerun=False,
        bounds_reproduced_byte_for_byte=True,
        eligible_ns=app['inbound_to_eligible_ns'],outbound_ns=app['outbound_ns'],
        recycle_ns=recycle['three_FWFT_and_credit_composition_ns'],
        allocated_recycle_tail_ns=F(1000),remaining_until_next_arrival_ns=recycle['remaining_after_response_and_tail_ns'],
        reaction_from_loss_slow_ns=history['last_history_to_fresh_applicable_including_loss_CDC_ns'],
        additional_board_loss_prefix_ns=outer_loss,reaction_from_stable_loss_switch_ns=raw_loss,
        raw_loss_scope='conditional 3-stage digital CDC + one use edge; level persists to capture; no analog metastability/physical monitor-latency claim',
        source_generation_exact_upper=str(bounds['generation']['mission_fast_edges_upper']),
        r4_conservative_JSON_generation_upper=str(rec['generation_clock_bound']['max_edges_upper']),
        source_time_and_rule_unchanged=True,proof_result_source_bindings=proofs,
        engineer_reported_STA={k:sta[k] for k in ('part','top','frequency_MHz','timing','resources')},
        IO_checks=20,IO_min_margin_ns=min(c['margin_ns'] for c in io['checks']),
        conditional_map='A_byte=4*w+2*h+b; A_x16=2*w+h; lane=b. Not physical ECC qualification.',
        shell_scope=dict(nominal_total_requests_s=shell_nominal_total,
            r4_max_sum_of_mean_requests_s=rec['mean_reads_s']+rec['mean_writes_s'],
            fast_clock_interarrival_witness_ns=shell_fast_spacing,
            r4_joint_min_interarrival_ns=F(10**9,rec['application_joint_rate_s']),
            actual_continuous_shell_in_r4_workload=False),
        preserved_r4_outcome={k:r4['rows']['selected_r3_original'][k] for k in
            ('risk_upper','slack','relative_slack','full_bus_quiet','full_bus_mission','resources')},
        unchanged_source_sha256=unchanged,engineer_source_sha256=dict(sorted(PINS.items())))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');args=ap.parse_args()
    out=report();encoded=json.dumps(serial(out),ensure_ascii=False,indent=2)+'\n'
    dest=HERE/'report-final.json'
    if args.write:dest.write_text(encoded)
    else:assert dest.read_text()==encoded,'final contract report differs'
    print('T135 final applicability: r4 executor contract retained; continuous STA-shell workload excluded.')
    print('Engineer bounds JSON byte-identical; proof-result/source/STA-input hashes checked, not solver or STA rerun.')
    for key in ('eligible_ns','outbound_ns','recycle_ns','remaining_until_next_arrival_ns',
                'reaction_from_loss_slow_ns','reaction_from_stable_loss_switch_ns'):
        print(key,str(out[key]),float(out[key]))
    print('r4 contract, outcome, calculator/config and 14 accepted sources byte-identical.')
    print('Report-final written.' if args.write else 'Report-final reproduced byte-for-byte.')


if __name__=='__main__':main()
