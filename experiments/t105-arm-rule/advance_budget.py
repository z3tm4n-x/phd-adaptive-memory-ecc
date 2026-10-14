"""Exact conditional preparation/service bounds, NOT a Cortex-A9 WCET.

Author's Issue105 update 2026-10-13T11:42:08Z explicitly replaces the
internal 10us fresh-history clause. Accepted T135 files are not changed.
The selected 1ms service allocation is NOT an established ARM service bound.
"""
import json
import math
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent


def encode(x):
    if isinstance(x, F):
        return {'rational': str(x), 'decimal': float(x)}
    if isinstance(x, dict):
        return {k: encode(v) for k, v in x.items()}
    return x


def calculate():
    cfg = json.loads((HERE/'config.json').read_text())
    lo, hi, jitter = F('0.99999'), F('1.00001'), F('.5')
    upper = lambda n: F(n)*hi+jitter
    # Accepted source/FIFO: no ARM in this stage. Source value is checked
    # independently against the accepted calculator in test_advance.py.
    history = F('531869457677237/102498975000')
    external = upper(80)
    # The old T105 batch_budget omitted this SECOND CDC. It is present in
    # accepted B and budget.py: loss_slow -> loss_fast -> source event.
    # Do not rewrite those historical outputs or pretend history includes it.
    loss_to_fast = upper(36)
    tick = upper(20)
    # Add one refresh-at-expiry slow edge to the previous link allocation.
    derived_link = 2*upper(112)+upper(320)+tick
    certificate = upper(600)
    assert derived_link < certificate
    calendar = upper(420+320+8)
    holds = {k: (cfg[k]-1)*20*lo-jitter for k in ('NW','NH','NR')}
    shortest = min(holds.values())
    # Deliberately sufficient, not necessary: even source/FIFO, one cut
    # edge and a complete link allocation fit BEFORE the minimum hold.
    # Actual link transmits at expiry; it is separately charged below.
    prep_fixed = external+loss_to_fast+history+tick+certificate
    prep_limit = (shortest-prep_fixed)/2
    # A source interval can exceed its processing interval by FIFO delay.
    # Two endpoint edges + jitter are retained; no empirical event cap.
    pair_min = cfg['PAIR_WINDOW']*4*lo-jitter
    pair_limit = pair_min-history-2*tick
    # Collector consumes at most one event per slow edge. Reserve two edge
    # endpoints and require strict headroom below UINT32_MAX.
    count_limit = (2**32-3)*20*lo-jitter
    limit = min(prep_limit, pair_limit, count_limit)
    old_limit = (10000-external-history-certificate-calendar)/2
    literal_limit = (10000-external-loss_to_fast-history-certificate-calendar)/2
    expiry_tail = tick+certificate+calendar
    paid_non_hold_tail = external+loss_to_fast+history+expiry_tail
    count_at_limit = math.ceil((limit+jitter)/(20*lo))+2
    selected = F(1000000)  # Author-selected complete round, not a sleep.
    selected_ticks = math.floor((selected-jitter)/(20*hi))
    selected_counts = math.ceil((selected+jitter)/(20*lo))+2
    selected_margin = shortest-prep_fixed-2*selected
    assert selected_margin > 0
    assert count_at_limit < 2**32-1
    assert paid_non_hold_tail < 10000
    assert F('1.1')*certificate < 1000
    # Mission upper from the unchanged 10-year source-edge contract.
    mission_edges = math.ceil((F(315576000)*10**9+jitter)/(4*lo))+1
    assert mission_edges < 2**57 < 2**64-1
    return {
      'status': 'CONDITIONAL_PREPARATION_THEOREM; author permits new V contract; ARM upper open',
      'base': 'e8b1225fe71ceb34bb3684a6b8890c8f1f3adb67',
      'issue105_updated_at': '2026-10-13T11:42:08Z',
      'theory146_read': 'f7763ad91699bec47c6c5b766794d14438724f3d',
      'selected_service_allocation_ns': selected,
      'selected_service_is_WCET': False,
      'selected_max_nominal_slow_ticks': selected_ticks,
      'selected_source_span_upper_ns': selected+history+2*tick,
      'selected_collector_count_upper': selected_counts,
      'selected_preparation_margin_ns': selected_margin,
      'selected_first_event_reply_upper_ns': external+loss_to_fast+history+2*selected+tick,
      'hold_lower_ns': holds,
      'historical_published_B_limit_ns': old_limit,
      'old_literal_fresh_history_B_limit_ns': literal_limit,
      'history_ns': history, 'external_loss_ns': external,
      'loss_slow_to_fast_ns': loss_to_fast,
      'historical_ledger_correction': 'batch_budget.py omitted loss_slow->loss_fast 36.500360ns; corrected here, accepted B unchanged',
      'cut_refresh_edge_ns': tick,
      'derived_link_with_refresh_ns': derived_link,
      'certificate_allocation_ns': certificate,
      'certificate_10pct_ns': F('1.1')*certificate,
      'calendar_ns': calendar,
      'prepare_fixed_ns': prep_fixed,
      'preparation_B_limit_ns': prep_limit,
      'source_span_B_limit_ns': pair_limit,
      'count32_B_limit_ns': count_limit,
      'joint_B_limit_ns': limit,
      'joint_B_limit_s': limit/10**9,
      'max_collector_events_in_B': count_at_limit,
      'mission_fast_edges_upper': mission_edges,
      'expiry_to_first_usable_operation_ns': expiry_tail,
      'non_hold_tail_including_history_ns': paid_non_hold_tail,
      'remaining_to_10us_ns': 10000-paid_non_hold_tail,
      'B_definition': 'cut-to-cut including accepted reply and next CLAIM; first cut within B',
      'preparation_inequality': 'external + loss_fast_CDC + history + 2*B + slow_edge + certificate <= min hold lower',
      'literal_processed_G_10us_implied': False,
      'new_physical_ARM_upper_ns': None,
      'CPU_nominal_hz': 600000000,
      'conditional_CPU_frequency_min_hz': F(600000000)/hi,
      'conditional_CPU_frequency_max_hz': F(600000000)/lo,
      'CPU_clock_scope': 'chosen +/-10ppm period envelope, not qualified PS oscillator/PLL',
      'platform_model': 'isolated A9/OCM/Device GP0 with symbolic finite service B; no CPI assigned',
      'platform_service_established': False,
      'Q_recalculated': False, 'mission_price_recalculated': False,
      'production_changed': False,
      'finite_B_violation': 'local FAST may remain safe but its unbounded extra price is NOT certified'}


if __name__ == '__main__':
    data = encode(calculate())
    (HERE/'outputs/advance-budget.json').write_text(json.dumps(data, indent=2)+'\n')
    print(json.dumps(data, indent=2))
