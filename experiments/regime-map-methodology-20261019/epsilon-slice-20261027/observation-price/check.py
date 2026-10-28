"""Read accepted results and check this resource application; no model replay.

Python standard library only. Historical references require the local Git
objects listed in SOURCES.json. No fetch, simulation, fitting or new grid.
"""
import argparse
import hashlib
import json
from decimal import Decimal, localcontext, ROUND_FLOOR
from fractions import Fraction as F
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
NS = 10**9


def sha(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def encoded(value):
    return (json.dumps(value, default=str, ensure_ascii=False,
                       sort_keys=True, indent=2) + '\n').encode('utf-8')


def decimal(value, places=12):
    value = F(value)
    with localcontext() as context:
        context.prec = 90
        return str((Decimal(value.numerator) / Decimal(value.denominator)).quantize(
            Decimal(1).scaleb(-places), rounding=ROUND_FLOOR))


def calculate():
    manifest = json.loads((HERE / 'SOURCES.json').read_text(encoding='utf-8'))
    for name, expected in manifest['current_sha256_LF'].items():
        assert sha((ROOT / name).read_bytes()) == expected, name
    for entry in manifest['historical_references']:
        raw = subprocess.check_output(['git', 'cat-file', 'blob',
                                       entry['commit'] + ':' + entry['path']], cwd=ROOT)
        assert sha(raw) == entry['sha256_LF'], entry['path']
    parent = HERE.parent / 'cell-service'
    saved = json.loads((parent / 'result.json').read_text(encoding='utf-8'))
    row = next(r for r in saved['rows'] if F(r['epsilon']) == F(1, 100))
    a = row['adaptive']
    assert (a['k_base'], a['k_rare']) == (403, 719)
    assert a['M_b'] == 4090586595328
    assert F(saved['constants']['deltaC_design']) == F(1, 20000)
    rates = {key: F(v) for key, v in a['handling']['rates_good_or_explicitly_bad_capped'].items()}
    coords = {}
    for name, c in a['coordinates'].items():
        comparisons = {}
        for rival, comparison in c['comparison'].items():
            allowance = F(comparison['allowance_20'])
            assert allowance == F(4, 5) * F(comparison['class_necessary_read_lower']) - F(c['V'])
            axis = comparison['axis_limits_not_simultaneous_or_assigned']['handler_unit_ns']
            # Independent dimensional check of saved projections, not a new search.
            for operation, rate in rates.items():
                assert F(axis[operation]) * rate / NS == allowance
            comparisons[rival] = dict(
                allowance_fraction=allowance,
                allowance_us_per_second_down=decimal(allowance * 10**6, 6),
                unit_axis_ns_not_simultaneous={k: decimal(v) for k, v in axis.items()},
                zero_other_additions_are_not_a_physical_assignment=True)
        assert comparisons['constant']['allowance_fraction'] == comparisons['schedule']['allowance_fraction']
        coords[name] = dict(comparisons=comparisons,
                           extra_invalid_coefficient=F(c['A_z']),
                           escape_coefficient=F(c['escape_coefficient']),
                           V=F(c['V']))
    # A placement illustration, not an estimated or mandatory unit cost.
    access16 = rates['cut_ready'] * 16 / 1000
    packet_budget = F(saved['timing']['per_record_packet_WCET_ns'])
    packet_max = saved['timing']['max_records_per_packet']
    assert packet_max == 1253 and packet_budget == 3900
    return dict(
        scope='Only application of accepted epsilon=.01 coefficients; no new risk or grid',
        accepted_result_sha256=sha((parent / 'result.json').read_bytes()),
        input_sha256=sha((ROOT / 'experiments/hybrid-p-r-20261026/inputs.json').read_bytes()),
        implementation_sha256=sha(Path(__file__).read_bytes()),
        manifest_sha256=sha((HERE / 'SOURCES.json').read_bytes()),
        rates_per_second_exact=rates,
        rates_per_second_down={k: decimal(v) for k, v in rates.items()},
        coordinates=coords,
        placement_example=dict(
            assumed_ns_per_cut_access=16,
            us_per_second_exact=access16,
            us_per_second_down=decimal(access16),
            not_a_lower_bound_on_all_architectures=True),
        deadlines=dict(packet_total_ns=packet_budget,
                       packet_max_records=packet_max,
                       serial_unit_ceiling_before_overhead_ns=F(packet_budget, packet_max),
                       serial_unit_ceiling_before_overhead_ns_down=decimal(F(packet_budget, packet_max)),
                       serial_ceiling_scope='All packet record work starts at cut; streaming pre-cut work is a different paid placement',
                       serial_model_not_required_for_parallel_logic=True,
                       final_gate_install_ns=F(saved['timing']['final_gate_install_after_fresh_lower_ns']),
                       hardware_verified=False),
        storage=dict(transport_loss_reserved_bytes=131136,
                     proposed_extra_policy_bytes=144,
                     sum_reserved_and_proposed_bytes=131280,
                     deployed_total_unknown=True),
        common_cost=dict(
            exact_shared_cost_formula='R_total_x = R_protection_x - C_common_x/5',
            directed_bounds_formula='R_total_x = R_protection_x - C_common_upper_x + 4*C_common_lower_x/5',
            no_common_observation_cost_with_fixed=True,
            whole_system_CPU_energy_20_percent_not_claimed=True),
        conclusion='Existing sources do not establish one complete implemented cost/timing/availability point; retain conditional region')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    data = encoded(calculate())
    path = HERE / 'result.json'
    if args.write:
        path.write_bytes(data)
        print('Wrote application result; accepted sources unchanged.')
    else:
        assert path.read_bytes().replace(b'\r\n', b'\n') == data, 'Application result drift'
        print('Sources, both class budgets, units and result bytes verified; no model replay.')
        print('SHA256 ' + sha(data))
