"""Unchanged scientific input plus one technical same-edge regression."""
from burst_run_inputs import build as frozen_build


def build(case='burst', pilot_events=0):
    if case != 'boundary':
        return frozen_build(case, pilot_events)
    assert not pilot_events
    # First fixed-mode safe query is absolute80740ns, T0=670ns. The
    # injection is pending on that exact fast/slow negative edge.
    return dict(scenario='boundary', horizon_ns=2_000_000,
        initial_data='0xa5a50000 XOR word', initial_errors=0,
        injections=[dict(at_ns=80070, word=212333, bit=10, parent=3476)],
        applications=[], false_ERR_interval_ns=[0, 0],
        loss_slow_interval_ns=[0, 0], ready_low_ns=80, ready_period_ns=340)
