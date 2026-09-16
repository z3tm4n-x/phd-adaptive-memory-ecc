"""Deterministic input diagnostics. No controller, policy trial or physical fit."""
import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parent


def reduced_generator(words, bits, bit_rate, group_size):
    """Safe states: number of singly erroneous words; last state is first E_cap.

    Parent rate bit_rate/group_size; a parent hits a uniform distinct subset
    of words, with independent uniform bit positions. No scrubbing in witness.
    """
    if not 1 <= group_size <= words or bits < 2 or bit_rate < 0:
        raise ValueError('Invalid witness domain')
    q = np.zeros((words + 2, words + 2))
    rate = bit_rate / group_size
    for k in range(words + 1):
        for r in range(max(0, group_size - (words-k)), min(k, group_size)+1):
            probability = math.comb(k, r)*math.comb(words-k, group_size-r)/math.comb(words, group_size)
            survive = bits ** (-r)
            q[k, k + group_size - 2*r] += rate*probability*survive
            q[k, -1] += rate*probability*(1-survive)
        q[k, k] -= rate
    return q


def calculations():
    c = json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
    raw = json.loads((ROOT/'source_rows.json').read_text(encoding='utf-8'))
    rows = {}
    for name, capacity in [('ISSI_32Mbit', 32*2**20), ('Renesas_8Mbit', 8*2**20)]:
        rows[name] = [dict(facility=f, LET=l, SBU=s, logic_MBU=m,
            fluence=fluence, literal_nominal_sigma=sigma,
            SBU_over_full_capacity_fluence=s/(capacity*fluence),
            implied_tested_bits=s/(fluence*sigma) if sigma else None,
            nominal_to_full_capacity_ratio=sigma*capacity*fluence/s if s else None)
            for f,l,fluence,s,m,sigma in raw[name]]
    r = c['source_row']
    s = c['diagnostic_scenario']
    sigma = r['SBU'] / (r['fluence_cm_minus2']*c['chip_bits'])
    protected = c['words']*c['protected_bits_per_word']
    physical = c['chips']*c['chip_bits']
    rate = sigma*protected*s['flux_cm_minus2_s_minus1']
    zero_upper = -math.log(s['alpha_one_sided']) / r['fluence_cm_minus2']
    total_device_fluence = c['chips']*s['flux_cm_minus2_s_minus1']*s['horizon_s']
    hazard = total_device_fluence*zero_upper
    max_allowed_hazard = -math.log1p(-s['epsilon_research'])
    w = c['witness']
    witness = {}
    for g in [1, 2]:
        q = reduced_generator(w['words'], w['bits_per_word'],
                              w['total_expected_bit_arrivals']/w['duration'], g)
        distribution = expm(q*w['duration'])[0]
        witness[str(g)] = dict(F_first_cap=float(distribution[-1]),
            safe_dirty_word_distribution=distribution[:-1].tolist(),
            total_arrival_mean=w['total_expected_bit_arrivals'],
            total_arrival_variance=g*w['total_expected_bit_arrivals'],
            no_arrival_probability=math.exp(-w['total_expected_bit_arrivals']/g),
            per_word_arrival_mean=w['total_expected_bit_arrivals']/w['words'],
            same_parent_same_word_pairs=0)
    return dict(status='INPUT_NOT_CLOSED_NOT_POLICY_RESULTS', normalization=rows,
        candidate=dict(data_bits=c['words']*c['data_bits_per_word'], protected_bits=protected,
            physical_bits=physical, padding_bits=physical-protected,
            nominal_SBU_cross_section_cm2_per_bit=sigma,
            nominal_protected_SBU_exposure_rate_s_minus1=rate,
            nominal_protected_SBU_exposure=rate*s['horizon_s']),
        optimistic_complete_detection_diagnostic=dict(
            is_validated_physical_bound=False,
            assumption='Counterfactually treat logic_MBU=0 as complete Poisson detection of every excluded parent group; treat every group as coupling failure and use all three chips, including padding conservatively. Fluence treated exact.',
            one_sided_confidence=1-s['alpha_one_sided'],
            per_device_group_cross_section_upper_cm2=zero_upper,
            three_device_group_mean_upper=hazard,
            Poisson_at_least_one_upper=-math.expm1(-hazard),
            union_upper=min(1.0,hazard),
            allowable_group_cross_section_if_entire_budget_assigned_cm2=max_allowed_hazard/total_device_fluence,
            zero_count_test_fluence_required_even_if_entire_budget_assigned=-math.log(s['alpha_one_sided'])*total_device_fluence/max_allowed_hazard),
        joint_mark_nonidentification_witness=witness,
        policy_trials=0)


if __name__ == '__main__':
    target = ROOT/'diagnostics.json'
    target.write_text(json.dumps(calculations(), indent=2, sort_keys=True)+'\n', encoding='utf-8', newline='\n')
    print(target)
