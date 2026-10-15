"""Independent T106 whole-horizon FAST arithmetic and delivery-scope checks.

This is an additional check of the price/table, not a second memory oracle.
The calculation below imports neither the simulator nor its price helpers.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HORIZONS = {1: 272_000_000_000, 2: 363_900_000_000_000,
            3: 362_000_000_000, 4: 48_000_000, 5: 362_000_000_000}
APPLICATIONS = {1: 0, 2: 0, 3: 0, 4: 48, 5: 40}


def fixed_slots(horizon):
    """Eight 92ns controls per 1568ns frame, starts 164ns apart."""
    frames, tail = divmod(horizon, 1568)
    work = frames * 8 * 92
    completed = frames * 8
    partial = 0
    for i in range(8):
        age = tail - i * 164
        work += max(0, min(92, age))
        completed += int(age >= 92)
        partial += int(0 < age < 92)
    return work, completed, partial


def check_fixed(row):
    work, complete, partial = fixed_slots(row['horizon_ns'])
    # In these five declared horizons the last control has age <92ns or
    # >=148ns. Correction cannot change the completed/partial classification.
    tail = row['horizon_ns'] % 1568
    assert all(not 92 <= tail - i * 164 < 148 for i in range(8))
    costs = row['bus_work_ns']
    assert costs['control_base_including_partial'] == work, 'FAST baseline work'
    assert row['completed_operations'] == complete + row['application_completed'], 'FAST completion count'
    assert row['unfinished_operations'] == partial, 'FAST terminal partial'
    assert row['CPU']['ARM_instructions_runtime'] == 0
    return dict(scenario=row['scenario'], base_work_ns=work,
                completed_controls=complete, partial_controls=partial)


def check_delivery(table):
    assert table['status'] == 'complete_digital_evidence_pending_review'
    assert not table['missing']
    assert len(table['rows']) == 10
    keys = [(r['scenario'], r['mode']) for r in table['rows']]
    assert len(set(keys)) == 10
    assert set(keys) == {(s, m) for s in HORIZONS for m in ('adaptive', 'fixed')}
    assert table['actual_ARM_time_ns'] is None and table['ARM_WCET_ns'] is None
    assert table['Q_T_certified_by_emulation'] is False
    checked = []
    for row in table['rows']:
        case = row['scenario']
        assert row['horizon_ns'] == HORIZONS[case]
        assert row['application_completed'] == APPLICATIONS[case]
        c = row['bus_work_ns']
        assert all(type(x) is int and x >= 0 for x in c.values())
        assert c['total'] == sum(v for k, v in c.items() if k != 'total')
        assert row['mean_bus_fraction'] == c['total'] / HORIZONS[case]
        assert 0 <= row['mean_bus_fraction'] <= row['peak_any_1ms_fraction'] <= 0.8
        if APPLICATIONS[case]:
            assert 0 < row['max_application_delay_ns'] <= 3000
        else:
            assert row['max_application_delay_ns'] is None
        assert row['CPU']['actual_ARM_time_ns'] is None
        assert row['CPU']['CPU_use_fraction_measured'] is None
        assert row['CPU']['allocated_cores'] == int(row['mode'] == 'adaptive')
        if row['mode'] == 'fixed':
            checked.append(check_fixed(row))
        else:
            assert row['model_full_service_ns'] == 188160
    return checked


if __name__ == '__main__':
    from five_scenarios import collect, markdown
    current = collect()
    stored = json.loads((HERE/'outputs/five-scenarios.json').read_text())
    assert current == stored, 'published table is stale or changed'
    assert (HERE/'outputs/five-scenarios.md').read_text() == markdown(current)
    print(json.dumps(dict(scope='independent FAST arithmetic; digital table only',
                          checked=check_delivery(current)), indent=2))
