"""One-time construction of v3; no numerical comparison is performed here."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
c=json.loads((HERE/'common-input.v2.proposed.json').read_text(encoding='utf-8'))
c.update(revision=3,status='ENGINEERING_INPUT_ALIGNED_SERVICE_POINT_SUBMITTED_FOR_THEORY')
c['initial']={'state':'common clean conditional initial state','K0':0,'pending':False,
 'paid_initialization':'W encodes + 3W x16 writes before t=0; separately reported and amortized over T',
 'physical_initialization_escape_probability':None}
c['lifetime_other_budget']='0.000006'
c['risk_budget']={'metric':'first weight>t in any full codeword at any time in [0,T]',
 'conditional_six_quota_sum_upper':'0.000006','reset_per_pass':False,
 'scope':'conditional on environment class and clean initial state; common bound on all required service/execution exceptions',
 'physical_unconditional':'min(1,U_conditional+delta_env+delta_init+other_nonoverlapping_unpaid_terms)',
 'physical_delta_env':None,'physical_delta_init':None,'quota_evidence':'explicit conditional model premise, not hardware measurement'}
c['environment']['baseline_p_s']={'1':'1'}
c['application']['write']='full useful32 write; read/decode old full word, encode/write new full word'
c['application'].update(read_repair=False,inbound_ns=320,ready_ns=80,outbound_ns=320,backpressure_ns=100)
c['service'].update(read_beat_ns=16,write_beat_ns=16,turnaround_ns=8,
 decode39_ns=20,decode44_ns=24,encode39_ns=20,encode44_ns=24,controller_ns=None,
 point_status='conditional numerical point, not measured hardware',
 bus_reservation='decode/encode latency included in serial bus reservation; no overlap discount',
 correction='E: old births removed, new births preserved; no created error relative to new payload',
 operation_endpoint_span_ns='0.5',clock_lower='0.99999',clock_upper='1.00001',
 service_validated=False)
c['calendar']={'c_ticks':164,'g_ticks':196,'batch_size':8,'frame_ticks':1568,
 'application_grant_phase_ticks':1312,'freeze_ticks':320,
 'word_at_control_index':'(3*index) mod W',
 'mandatory':'startup full fast pass; then every kth full pass; fixed predetermined support',
 'additional_adaptive_reads':'only at unchanged potential starts; cannot suppress mandatory support',
 'initialization_outside_horizon':True}
c['fixed'].update(selection='largest integer k>=1 with conditional E moment upper<=epsilon/2; P=k*W*g',
 search_cap_k=4294967296)
c['adaptive'].update(selection='largest k in [3,5,9,27] with same mandatory-support risk target',
 candidate_ka=[3,5,9,27],short_hold_s='90',long_hold_s='180',
 risk_basis='T196(5) mandatory support, ignoring extra correct E actions; informational refinement remains open',
 ordinary_false_expected_per_s='0.000001',ordinary_outage_fraction='0.0001',
 ordinary_loss_episodes_upper=1001,recoveries_upper=1000,
 source_to_fresh_rule_upper_ns=10000,
 timer_quantum_ticks=20, source_pair_window_s='90',
 all_history='controller and accounting continue after first exceedance')
c['observation']['fixed_monitor_price_policy']='no adaptive observation/cuts/records for fixed; common app and fixed timing hardware charged separately'
c['observation']['external_codec_to_source_delay_ns']='included in full read/decode aperture'
c['observation']['extra_source_veto_parameter']='v=E[N_v]/T per second; range[0,250002500.1], no physical selected rate'
c['observation']['veto_zero_slice']='explicit conditional slice only; also report unconstrained hard upper'
c['constraints'].update(clock_and_reserve='conditional common clock bounds in service',
 map_targets={'risk_fraction_of_epsilon':'0.5','response_ns':2400,'peak_bus_fraction':'0.64','other_resource_fraction_of_cap':'0.8'},
 capacity_caps={'raw_SRAM_bytes':None,'controller_RAM_bytes':None,'LUT':None,'BRAM':None,'CPU_fraction':None,'energy_J':None})
c['cost'].update(fixed_observation='omitted because unused; timer/controller costs stay explicit',
 source_veto_count_coefficient='T196(11), full started work; no handler changes',
 repair_count_bound='parent count before global bad event + Q_upper*hard reads afterwards; also always-E upper',
 adaptive_good_source_bound='<=2 publications per parent if app revisit exceeds mandatory age; otherwise use hard upper')
c['sources']['T196_three_variants']='7259964f17e1aea01937df0c0e3134be69a70d7f'
c['coordination']={'map_reply':'https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/pull/211#issuecomment-6334240420',
 'orchestrator':'https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/pull/211#issuecomment-6334315499',
 'theory_parent_law':'https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/186#issuecomment-6334139214',
 'numerical_reply':'https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/186#issuecomment-6334225337'}
raw=(json.dumps(c,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
path=HERE/'common-input.json'
if path.exists() and path.read_bytes()!=raw: raise ValueError('v3 already exists with different contents')
path.write_bytes(raw)
print(hashlib.sha256(raw).hexdigest())
