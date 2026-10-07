"""Native-bin diagnostics only: no interpolation, ERR inference or risk proof."""
from __future__ import annotations

from bisect import bisect_right
import math
import numpy as np


STRATA = ('unassigned_no_crossing', 'confirmed_entry', 'repeat_pre_peak',
          'repeat_post_peak', 'repeat_peak_unknown', 'censored_first',
          'censored_repeat')


def h_transform(x, level):
    x = np.asarray(x, dtype=float)
    if level <= 0 or np.any(x < 0) or not np.all(np.isfinite(x)):
        raise ValueError('H requires finite nonnegative response and positive level')
    return np.where(x <= level, x / level, 1 + np.log(np.maximum(x, 1e-300) / level))


def segments(t, x, valid, signature, cadence):
    """Half-open index ranges, broken by quality, missing bins or signatures."""
    t, x, valid, signature = map(np.asarray, (t, x, valid, signature))
    valid = valid.astype(bool)
    ok = valid & np.isfinite(x) & (x >= 0)
    if not len(t):
        return []
    adjacency = ok[1:] & ok[:-1] & (np.diff(t) == cadence) & (signature[1:] == signature[:-1])
    starts = np.flatnonzero(ok & ~np.r_[False, adjacency])
    stops = np.flatnonzero(ok & ~np.r_[adjacency, False]) + 1
    return list(zip(starts.tolist(), stops.tolist()))


def first_efold(x, cadence):
    """Shortest observed >=e rise within one continuous above-level excursion.

    A later smaller value dominates an earlier larger one for all future targets.
    The increasing frontier therefore finds the latest eligible left endpoint.
    No monotonicity of the measured trajectory is imposed.
    """
    frontier, indices, best = [], [], None
    for j, value in enumerate(x):
        if not math.isfinite(value) or value <= 0:
            raise ValueError('e-fold excursion must be finite and positive')
        k = bisect_right(frontier, value / math.e) - 1
        if k >= 0:
            i = indices[k]
            item = ((j - i) * cadence, i, j)
            if best is None or item < best:
                best = item
        while frontier and frontier[-1] >= value:
            frontier.pop()
            indices.pop()
        frontier.append(value)
        indices.append(j)
    return best


def pair_metrics(x, level, cadence):
    """Return signed H slopes and log slopes (NaN outside above-level pairs)."""
    x = np.asarray(x, dtype=float)
    h = np.diff(h_transform(x, level)) / cadence
    log = np.full(len(h), np.nan)
    select = (x[:-1] >= level) & (x[1:] >= level)
    log[select] = np.log(x[1:][select] / x[:-1][select]) / cadence
    return h, log


def extremum(values, offset=0):
    valid = np.isfinite(values) & (np.asarray(values) > 0)
    if not np.any(valid):
        return None
    i = int(np.argmax(np.where(valid, values, -np.inf)))
    return float(values[i]), offset + i, offset + i + 1


def classify(first, quiet_reference, catalogue_phase):
    if not quiet_reference:
        return 'censored_first' if first else 'censored_repeat'
    if first:
        return 'confirmed_entry'
    return {'pre_peak': 'repeat_pre_peak', 'post_peak': 'repeat_post_peak',
            'unknown_peak': 'repeat_peak_unknown'}[catalogue_phase]


def hold_interval(below_start, upcross_start, cadence, w, h):
    """Bin-label bounds, NOT bounds on a physical crossing or actual ERR state.

    Label transitions lie between the preceding/current bin starts. For physical
    sub-bin trajectories even that localization would require an extra assumption.
    """
    if below_start is None or upcross_start <= below_start:
        return {'status': 'left_censored_decline', 'duration_bin_starts_s': None,
                'label_duration_lower_s': None, 'label_duration_upper_s': None,
                'longer_than_h_by_labels': None, 'longer_than_w_plus_h_by_labels': None,
                'h_not_excluded_by_label_bracket': None, 'w_plus_h_not_excluded_by_label_bracket': None}
    duration = float(upcross_start - below_start)
    lower, upper = max(0., duration - cadence), duration + cadence
    return {'status': 'resolved_bin_labels_only', 'duration_bin_starts_s': duration,
            'label_duration_lower_s': lower, 'label_duration_upper_s': upper,
            'longer_than_h_by_labels': lower >= h,
            'longer_than_w_plus_h_by_labels': lower >= w + h,
            'h_not_excluded_by_label_bracket': upper >= h,
            'w_plus_h_not_excluded_by_label_bracket': upper >= w + h,
            'last_alarm_deadline_relative_to_upcross_s': -h,
            'LOW_window_start_if_exit_at_upcross_relative_s': -w,
            'actual_ERR_state': 'unknown_requires_count_law_history_phase_delivery_and_exit_rule'}


def quiet_episodes(t, x, valid, signature, cadence, quiet, history):
    """Observed quiet exits and ends, including left/right censoring.

    Ends use the *end* of the last required quiet bin. No unknown sample counts
    as quiet. A segment starting active is left censored even when it later ends.
    """
    rows = []
    for a, b in segments(t, x, valid, signature, cadence):
        quiet_bins = 0
        active = None
        for i in range(a, b):
            if x[i] > quiet:
                if active is None:
                    active = {'start_index': i, 'confirmed_start': quiet_bins * cadence >= history,
                              'left_censored': quiet_bins * cadence < history}
                quiet_bins = 0
            else:
                quiet_bins += 1
                if active is not None and quiet_bins * cadence >= history:
                    rows.append({**active, 'end_index': i, 'end_time': float(t[i] + cadence),
                                 'right_censored': False, 'end_status': 'observed_24h_quiet'})
                    active = None
        if active is not None:
            rows.append({**active, 'end_index': b - 1, 'end_time': None,
                         'right_censored': True, 'end_status': 'segment_or_window_end'})
    return rows


def class_contract(rho_entry, rho_held):
    """Parameter carrier, never a claim that the data identify controller state."""
    if rho_entry <= 0 or rho_held <= 0:
        raise ValueError('positive conditional cones required')
    return {
        'rho_entry_s_inv': rho_entry, 'rho_held_s_inv': rho_held,
        'entry_scope': 'new entry and every repeat after any possible causal exit',
        'held_scope': 'only intervals with separately proved uninterrupted FAST',
        'continuous_condition': 'H_L(lambda) absolutely continuous; H_L(lambda(t2))-H_L(lambda(t1)) <= integral_[t1,t2] rho(u) du for every t1<t2; rho_held only on proved uninterrupted FAST, rho_entry elsewhere',
        'unknown': ['within_bin_growth', 'future_coverage', 'data32_to_full38_spectral_transfer',
                    'ERR_law_under_E', 'causal_exit_and_hold_history'],
        'physical_qualification': False,
    }
