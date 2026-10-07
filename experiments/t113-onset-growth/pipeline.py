"""T113 tables; accepted T72 crossings/counts are read, never rewritten."""
from __future__ import annotations

from collections import defaultdict
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import numpy as np

from onset_growth import (STRATA, classify, class_contract, extremum, first_efold,
                          hold_interval, pair_metrics, quiet_episodes, segments)

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
T67, T72 = EXP / 't67-goes-growth', EXP / 't72-r0a-onset-inputs'


def iso(t):
    return datetime.fromtimestamp(float(t), timezone.utc).isoformat()


def stamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def csv_bytes(rows):
    stream = io.StringIO(newline='')
    fields = list(dict.fromkeys(k for r in rows for k in r))
    writer = csv.DictWriter(stream, fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def serialize(name, data):
    if name.endswith('.json'):
        return (json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    raw = csv_bytes(data)
    if name.endswith('.gz'):
        # GzipFile fixes timestamp/name/OS header for platform-neutral byte checks.
        out = io.BytesIO()
        with gzip.GzipFile(fileobj=out, mode='wb', filename='', mtime=0) as f:
            f.write(raw)
        return out.getvalue()
    return raw


def verify_inputs(config):
    for name, digest in config['source_sha256'].items():
        if sha(EXP / name) != digest:
            raise ValueError('Accepted input changed: ' + name)


def verify_t67_extrema(distributions):
    """Independent new native-pair computation must recover the accepted envelope."""
    old = defaultdict(list)
    for row in read_csv(T67 / 'outputs/rho_candidates.csv'):
        if int(row['cadence_s']) == int(row['window_s']):
            old[(int(row['cadence_s']), row['mask'], float(row['level_s-1']))].append(row)
    checked = []
    for (cad, mask, level), rows in sorted(old.items()):
        witness = max(rows, key=lambda r: float(r['rho_observed_s-1']))
        new = next(r for r in distributions if r['response'] == 'main_loglog' and r['cadence_s'] == cad
                   and r['mask'] == mask and r['target_level_s_inv'] == level and r['metric'] == 'H'
                   and r['zone'] == 'whole' and r['stratum'] == 'all_retained')
        before, after = float(witness['rho_observed_s-1']), new['max_positive']
        # None remains a missing positive slope; only compare it with T67's
        # positive-part convention 0 when a native pair was actually retained.
        actual = after if after is not None else 0.
        if not math.isclose(before, actual, rel_tol=5e-13, abs_tol=5e-16):
            raise AssertionError(f'T67 native envelope mismatch: {cad}/{mask}/{level}: {before} != {after}')
        checked.append({'cadence_s': cad, 'mask': mask, 'level_s_inv': level,
                        'T67_native_H_s_inv': before, 'T113_native_H_s_inv': after,
                        'absolute_difference': abs(actual-before), 'status': 'agrees_at_float_tolerance',
                        'T67_witness_event': witness['event_id'], 'T67_witness_start_utc': witness['start_utc'],
                        'T113_witness_start_utc': new.get('maximum_from_utc')})
    return checked


def row_key(row):
    return (row['event_id'], int(row['satellite']), int(row['cadence_s']),
            row['response'], row['mask'], row['direction'])


def counts_index():
    """Exact row witnesses for extrema, preserving settings instead of mixing laws."""
    groups = defaultdict(list)
    for r in read_csv(T72 / 'outputs/available_counts.csv.gz'):
        groups[int(r['record_id'])].append(r)
    result, selected = {}, {}
    for rid, rows in groups.items():
        low = min(rows, key=lambda r: float(r['ERR_oracle_expected_lower']))
        high = max(rows, key=lambda r: float(r['ERR_oracle_expected_upper']))
        record = {'record_id': rid, 'source_rows': len(rows),
                  'status': 'T72 ideal_U_expectation_only_not_ERR_under_E',
                  'time_origin': 'quiet_exit; NOT a reset at a repeat or a count in the new 40/60s window'}
        for prefix, witness, key in [('lower', low, 'ERR_oracle_expected_lower'),
                                     ('upper', high, 'ERR_oracle_expected_upper')]:
            record[prefix + '_expected'] = float(witness[key])
            for k in ['period_s', 'phase_fraction', 'delivery_s', 'phase_layout',
                      'availability_deadline_utc', 'initial_state']:
                record[prefix + '_' + k] = witness[k]
        result[rid] = record
        selected[rid] = {}
        for r in rows:
            if float(r['phase_fraction']) == 0 and float(r['delivery_s']) == 0:
                if float(r['period_s']) in (.05, 6.) and r['phase_layout'] == 'uniform_full_period':
                    selected[rid][float(r['period_s'])] = r
    return result, selected


def annotate_witness(prefix, pair, group, sources, direction_index):
    if pair is None:
        return {prefix + '_value': None}
    value, i, j = pair
    output = {prefix + '_value': float(value)}
    for label, k in [('from', i), ('to', j)]:
        source = sources[int(group['file_index'][k])]
        stem = prefix + '_' + label + '_'
        output.update({stem + 'utc': iso(group['time'][k]),
                       stem + 'source_name': source['name'], stem + 'sha256': source['sha256'],
                       stem + 'version': source['version'], stem + 'signature': int(group['signature'][k])})
        for flag in ['screened', 'strict', 'core_strict']:
            output[stem + flag] = bool(group[flag][k, direction_index])
    return output


def quantiles(values):
    values = np.asarray(values)
    positive = values[np.isfinite(values) & (values > 0)]
    return {'positive_pairs': len(positive),
            **{name: float(np.quantile(positive, q)) if len(positive) else None
               for name, q in [('p50_positive', .5), ('p90_positive', .9), ('p99_positive', .99)]},
            'max_positive': float(np.max(positive)) if len(positive) else None}


def analyze(config, manifest, series):
    accepted = read_csv(T72 / 'outputs/onsets.csv.gz')
    old_availability = read_csv(T72 / 'outputs/availability.csv')
    by_key, avail_by_key = defaultdict(list), defaultdict(list)
    for r in accepted:
        by_key[row_key(r)].append(r)
    for r in old_availability:
        avail_by_key[row_key(r)].append(r)
    count_index, count_selected = counts_index()
    crossings, holds, coverage, episodes, extrema, distributions = [], [], [], [], [], []
    seen_ids, aggregate = set(), defaultdict(list)
    audit = {'checked_T72_target_rows': 0, 'checked_T72_availability_rows': 0,
             'checked_T72_integrals': 0, 'ambiguous_class_membership_pairs': 0,
             'retained_unique_pair_instances_across_thresholds_models_masks': 0}

    for sat, cad in itertools.product([16, 18, 19], config['cadences_s']):
        path = series / f'g{sat}_{cad}.npz'
        if not path.exists():
            raise ValueError(f'Missing derived group G{sat}/{cad}; not zero-filled')
        with np.load(path) as z:
            group = dict(z)
        sources = sorted([r for r in manifest['files'] if r['satellite'] == sat and r['cadence_s'] == cad], key=lambda r: r['date'])
        time, signature = group['time'], group['signature']
        for model, mask, direction in itertools.product(config['responses'], config['masks'], ['E', 'W']):
            d = ['E', 'W'].index(direction)
            full_x = group[model][:, d]
            full_valid = np.isfinite(full_x) & (full_x >= 0)
            if mask != 'reported':
                flag = 'core_strict' if model == 'core_only' and mask == 'strict' else mask
                full_valid &= group[flag][:, d]
            # One bit per causal stratum. A pair can have conflicting window histories.
            membership = {L: np.zeros(max(0, len(time) - 1), dtype=np.uint16) for L in config['levels_s_inv']}
            approach_membership = {L: np.zeros_like(v) for L, v in membership.items()}
            above_membership = {L: np.zeros_like(v) for L, v in membership.items()}
            for event in manifest['events']:
                start, end, bg = [stamp(event[k]) for k in ['analysis_start', 'analysis_end_exclusive', 'background_start']]
                peak = None if event['kind'] == 'special_full_month' else stamp(event['peak_utc'])
                pick = np.flatnonzero((time >= bg) & (time < end))
                t, x, valid, sig = time[pick], full_x[pick], full_valid[pick], signature[pick]
                key = (event['id'], sat, cad, model, mask, direction)
                base = dict(event_id=event['id'], satellite=sat, cadence_s=cad, response=model, mask=mask,
                            direction=direction, catalogue_peak_utc=iso(peak) if peak is not None else None)
                spans = segments(t, x, valid, sig, cad)
                span_stop = np.full(len(t), -1, int)
                span_start = np.full(len(t), -1, int)
                for a, b in spans:
                    span_stop[a:b] = b
                    span_start[a:b] = a
                on_window = (t >= start) & (t < end)
                adjacent = valid[:-1] & valid[1:] & (np.diff(t) == cad) & (sig[:-1] == sig[1:])
                adjacent &= on_window[:-1] & on_window[1:]
                index = {float(value): i for i, value in enumerate(t)}
                classes = {L: np.zeros(max(0, len(t) - 1), dtype=np.uint16) for L in config['levels_s_inv']}
                approach_classes = {L: np.zeros_like(v) for L, v in classes.items()}
                above_classes = {L: np.zeros_like(v) for L, v in classes.items()}
                local_rows = []
                for old in by_key.get(key, []):
                    rid = int(old['record_id'])
                    i = index[stamp(old['target_bin_start_utc'])]
                    assert valid[i] and span_stop[i] > i, (key, rid)
                    assert math.isclose(float(old['target_bin_response_s_inv']), x[i], rel_tol=2e-13, abs_tol=0)
                    src = sources[int(group['file_index'][pick[i]])]
                    assert src['sha256'] == old['target_source_sha256'] and src['name'] == old['target_source_name']
                    assert src['version'] == old['processing_version'] and int(sig[i]) == int(old['signature_id'])
                    for flag in ['screened', 'strict', 'core_strict']:
                        assert bool(group[flag][pick[i], d]) == (old['target_' + flag] == 'True')
                    audit['checked_T72_target_rows'] += 1
                    root = index[stamp(old['quiet_exit_bin_start_utc'])] if old['quiet_exit_bin_start_utc'] else None
                    rise = index[stamp(old['repeat_rise_start_utc'])] if old['repeat_rise_start_utc'] else None
                    L = float(old['target_level_s_inv'])
                    # T72's `seen` starts collecting crossings at the analysis
                    # window, even though background bins precede it. Keep its
                    # field verbatim; T113's definition also checks that background.
                    history_start = root if root is not None else int(span_start[i])
                    first = not bool(np.any(x[history_start:i] >= L))
                    phase = 'unknown_peak' if peak is None else 'post_peak' if t[i] > peak else 'pre_peak'
                    stratum = classify(first, root is not None, phase)
                    a = root if first and root is not None else rise if rise is not None else i
                    assert a <= i and span_stop[a] == span_stop[i]
                    b = int(span_stop[i])
                    below = np.flatnonzero(x[i:b] < L)
                    if len(below):
                        below_index = i + int(below[0])
                        last, right_censored = below_index - 1, False
                        end_status = 'observed_below_level'
                    else:
                        below_index, last, right_censored = None, b - 1, True
                        end_status = ('window_end' if b == len(t) and len(t) and t[-1] + cad >= end
                                      else 'quality_time_or_signature_gap_or_missing_data')
                    h, log = pair_metrics(x[a:last + 1], L, cad)
                    hm, lm = extremum(h, a), extremum(log, a)
                    above_h, above_log = pair_metrics(x[i:last + 1], L, cad)
                    approach_h, _ = pair_metrics(x[a:i + 1], L, cad)
                    efold = first_efold(x[i:last + 1], cad)
                    efold = (efold[0], efold[1] + i, efold[2] + i) if efold else None
                    new = {**old, 'instrument': f'GOES-{sat} SGPS', 'stratum': stratum, 'catalogue_phase': phase,
                           'first_crossing_in_available_continuous_history': first,
                           'T72_first_label_differs_from_continuous_history': first != (old['first_target_in_quiet_episode'] == 'True'),
                           'observed_repeat': not first, 'quiet_reference_confirmed': root is not None,
                           'T113_approach_start_utc': iso(t[a]), 'above_level_last_bin_start_utc': iso(t[last]),
                           'below_level_bin_start_utc': iso(t[below_index]) if below_index is not None else None,
                           'right_censored': right_censored, 'end_status': end_status,
                           'T113_approach_expected_inversions': float(np.sum(x[a:i]) * cad) if a < i else None,
                           'approach_max_H_s_inv': max(0., float(np.max(approach_h, initial=0.))),
                           'above_level_max_H_s_inv': max(0., float(np.max(above_h, initial=0.))),
                           'equivalent_bin_efold_s': 1 / lm[0] if lm else None,
                           'count_status': count_index[rid]['status'] if rid in count_index else 'no_T72_count_for_this_record'}
                    for prefix, witness in [('H', hm), ('log', lm), ('observed_efold_s', efold),
                                            ('approach_H', extremum(approach_h, a)),
                                            ('above_H', extremum(above_h, i))]:
                        global_pair = (witness[0], int(pick[witness[1]]), int(pick[witness[2]])) if witness else None
                        new.update(annotate_witness(prefix, global_pair, group, sources, d))
                        if witness:
                            new[prefix + '_from_response_s_inv'] = float(x[witness[1]])
                            new[prefix + '_to_response_s_inv'] = float(x[witness[2]])
                            new[prefix + '_catalogue_phase'] = ('unknown_peak' if peak is None else
                                'pre_peak' if t[witness[2]] <= peak else
                                'post_peak' if t[witness[1]] >= peak else 'straddles_peak')
                    for seconds in config['candidate_efold_s']:
                        new[f'H_exceeds_1_over_{seconds}'] = bool(hm and hm[0] > 1 / seconds)
                        new[f'log_exceeds_1_over_{seconds}'] = bool(lm and lm[0] > 1 / seconds)
                    if root is not None and root < i:
                        integral = float(np.sum(x[root:i]) * cad)
                        assert math.isclose(float(old['quiet_to_target_expected_inversions']), integral, rel_tol=3e-12, abs_tol=2e-12)
                        audit['checked_T72_integrals'] += 1
                    classes[L][a:last] |= np.uint16(1 << STRATA.index(stratum))
                    approach_classes[L][a:i] |= np.uint16(1 << STRATA.index(stratum))
                    above_classes[L][i:last] |= np.uint16(1 << STRATA.index(stratum))
                    crossings.append(new)
                    local_rows.append(new)
                    seen_ids.add(rid)
                    if not first:
                        for rule in config['hold_candidates']:
                            rec = {**base, 'record_id': rid, 'stratum': stratum, 'catalogue_phase': phase,
                                   'target_level_s_inv': L, 'w_s': rule['w_s'], 'h_s': rule['h_s'],
                                   'below_start_bin_utc': iso(t[rise]) if rise is not None else None,
                                   'upcross_bin_utc': iso(t[i]), 'upcross_earliest_data_available_utc': iso(t[i] + cad),
                                   'below_preceding_bin_utc': iso(t[rise] - cad) if rise is not None else None,
                                   'upcross_preceding_bin_utc': iso(t[i] - cad),
                                   **hold_interval(float(t[rise]) if rise is not None else None, float(t[i]), cad, rule['w_s'], rule['h_s'])}
                            rec['required_no_new_alarm_since_utc_for_exit_by_bin_start'] = iso(t[i] - rule['h_s'])
                            rec['hypothetical_LOW_window_start_utc_at_bin_start_exit'] = iso(t[i] - rule['w_s'])
                            rec['hypothetical_LOW_window_end_utc_at_bin_start_exit'] = iso(t[i])
                            rec['within_bin_LOW_counts_identified'] = False
                            holds.append(rec)
                # Preserve accepted availability, checking the new series against it.
                for old in avail_by_key.get(key, []):
                    L = float(old['target_level_s_inv'])
                    retained = int(np.sum(valid & on_window))
                    rr = [r for r in local_rows if float(r['target_level_s_inv']) == L]
                    assert retained == int(old['retained_bins']) and len(rr) == int(old['crossing_rows'])
                    audit['checked_T72_availability_rows'] += 1
                    coverage.append({**old, 'valid_adjacent_pairs': int(np.sum(adjacent)),
                                     'right_censored_crossings': sum(r['right_censored'] for r in rr),
                                     'left_or_reference_censored_crossings': sum(r['stratum'].startswith('censored') for r in rr),
                                     'confirmed_entries': sum(r['stratum'] == 'confirmed_entry' for r in rr),
                                     'repeat_crossings': sum(r['observed_repeat'] for r in rr)})
                    local_membership = classes[L]
                    local_membership[local_membership == 0] = 1  # unassigned
                    if len(pick) > 1:
                        ii = np.flatnonzero(adjacent)
                        membership[L][pick[ii]] |= local_membership[ii]
                        approach_membership[L][pick[ii]] |= approach_classes[L][ii]
                        above_membership[L][pick[ii]] |= above_classes[L][ii]
                for ep in quiet_episodes(t, x, valid, sig, cad, config['quiet_level_s_inv'], config['quiet_history_s']):
                    if t[ep['end_index']] < start:
                        continue
                    episodes.append({**base, **{k: v for k, v in ep.items() if not k.endswith('_index') and k != 'end_time'},
                                     'start_bin_utc': iso(t[ep['start_index']]),
                                     'last_observed_bin_utc': iso(t[ep['end_index']]),
                                     'observed_end_available_utc': iso(ep['end_time']) if ep['end_time'] is not None else None})
            # Window union: retain each source pair once within a stratum.
            # Different directional/model/mask strata are not independent samples.
            safe_x = np.where(full_valid, full_x, 0.)
            for L, bits in membership.items():
                h, log = pair_metrics(safe_x, L, cad)
                seen = bits != 0
                multi = seen & ((bits & (bits - 1)) != 0)
                audit['ambiguous_class_membership_pairs'] += int(np.sum(multi))
                audit['retained_unique_pair_instances_across_thresholds_models_masks'] += int(np.sum(seen))
                for zone, stratum in itertools.product(
                        ['whole', 'approach', 'above_level'], (*STRATA, 'all_retained')):
                    zone_bits = bits if zone == 'whole' else approach_membership[L] if zone == 'approach' else above_membership[L]
                    take = zone_bits != 0 if stratum == 'all_retained' else (zone_bits & (1 << STRATA.index(stratum))) != 0
                    if not np.any(take):
                        continue
                    base = dict(satellite=sat, cadence_s=cad, response=model, mask=mask, direction=direction,
                                target_level_s_inv=L, stratum=stratum, zone=zone, unique_adjacent_pairs=int(np.sum(take)),
                                ambiguous_window_history_pairs=int(np.sum(multi & take)))
                    for metric, values in [('H', h), ('log', log)]:
                        v = values[take]
                        item = {**base, 'metric': metric, **quantiles(v)}
                        item['instrument'] = f'GOES-{sat} SGPS'
                        indices = np.flatnonzero(take)
                        ex = extremum(v)
                        witness = (ex[0], int(indices[ex[1]]), int(indices[ex[1]]) + 1) if ex else None
                        item.update(annotate_witness('maximum', witness, group, sources, d))
                        if witness:
                            item['maximum_from_response_s_inv'] = float(full_x[witness[1]])
                            item['maximum_to_response_s_inv'] = float(full_x[witness[2]])
                            contexts = []
                            t0, t1 = time[witness[1]], time[witness[2]]
                            for e in manifest['events']:
                                if stamp(e['analysis_start']) <= t0 and t1 < stamp(e['analysis_end_exclusive']):
                                    pk = None if e['kind'] == 'special_full_month' else stamp(e['peak_utc'])
                                    phase = ('unknown_peak' if pk is None else 'pre_peak' if t1 <= pk
                                             else 'post_peak' if t0 >= pk else 'straddles_peak')
                                    contexts.append(e['id'] + ':' + phase)
                            item['maximum_all_covering_window_phases'] = '|'.join(contexts)
                        item['equivalent_bin_efold_s'] = 1 / ex[0] if ex else None
                        item['illustrative_2x_empirical_rho_s_inv'] = config['illustrative_empirical_margin'] * ex[0] if ex else None
                        for seconds in config['candidate_efold_s']:
                            item[f'pairs_exceed_1_over_{seconds}'] = int(np.sum(v > 1 / seconds))
                        item['pairs_exceed_legacy_rho'] = int(np.sum(v > config['legacy_rho_s_inv']))
                        extrema.append(item)
                        akey = (cad, model, mask, L, stratum, zone, metric)
                        aggregate[akey].append((item, v[np.isfinite(v) & (v > 0)]))
        print(f'T113 analyzed G{sat}/{cad}: {len(crossings)} T72 crossings checked', flush=True)

    if seen_ids != {int(r['record_id']) for r in accepted}:
        raise AssertionError('T72 record coverage mismatch')
    assert audit['checked_T72_availability_rows'] == len(old_availability)
    for akey, items in sorted(aggregate.items()):
        cad, model, mask, L, stratum, zone, metric = akey
        values = np.concatenate([v for _, v in items])
        best = max((r for r, _ in items), key=lambda r: r['max_positive'] or 0.)
        record = {k: v for k, v in best.items() if k not in ('unique_adjacent_pairs', 'ambiguous_window_history_pairs')}
        record.update(satellite='all_separate_directions_not_independent', direction='all', **quantiles(values),
                      unique_adjacent_pairs=sum(r['unique_adjacent_pairs'] for r, _ in items),
                      ambiguous_window_history_pairs=sum(r['ambiguous_window_history_pairs'] for r, _ in items),
                      extreme_satellite=best['satellite'], extreme_direction=best['direction'])
        for seconds in config['candidate_efold_s']:
            record[f'pairs_exceed_1_over_{seconds}'] = sum(r[f'pairs_exceed_1_over_{seconds}'] for r, _ in items)
        record['pairs_exceed_legacy_rho'] = sum(r['pairs_exceed_legacy_rho'] for r, _ in items)
        distributions.append(record)

    crossings.sort(key=lambda r: int(r['record_id']))
    event_table = make_event_table(manifest, crossings, count_selected, coverage)
    hold_sensitivity = summarize_hold_growth(holds, crossings, config)
    interval_envelopes = summarize_intervals(crossings)
    handoff = make_handoff(config, audit, crossings, holds, coverage, distributions, manifest)
    return {'crossings.csv.gz': crossings, 'declines_and_hold.csv.gz': holds,
            'coverage.csv.gz': coverage, 'quiet_episodes.csv.gz': episodes,
            'growth_extrema.csv.gz': extrema, 'growth_distribution.csv': distributions,
            'interval_envelopes.csv': interval_envelopes,
            'hold_sensitivity.csv': hold_sensitivity,
            'event_levels.csv': event_table,
            'count_index.csv.gz': [count_index[k] for k in sorted(count_index)], 'handoff.json': handoff}


def summarize_intervals(rows):
    """Maxima including full T72 approaches, even when they begin in background."""
    groups = defaultdict(list)
    for row in rows:
        groups[(row['response'], row['mask'], int(row['cadence_s']), float(row['target_level_s_inv']), row['stratum'])].append(row)
    result = []
    for key, rr in sorted(groups.items()):
        model, mask, cad, L, stratum = key
        entry = dict(response=model, mask=mask, cadence_s=cad, level_s_inv=L, stratum=stratum,
                     scope='entire_crossing_intervals_including_T72_background; overlapping_rows_not_independent',
                     crossing_context_rows=len(rr))
        for prefix in ['approach_H', 'above_H', 'H', 'log', 'observed_efold_s']:
            good = [r for r in rr if r[prefix + '_value'] is not None]
            choose = min if prefix == 'observed_efold_s' else max
            witness = choose(good, key=lambda r: r[prefix + '_value']) if good else None
            entry[prefix + '_extreme'] = witness[prefix + '_value'] if witness else None
            entry[prefix + '_record_id'] = witness['record_id'] if witness else None
        result.append(entry)
    return result


def summarize_hold_growth(holds, crossings, config):
    """Growth after declines with timer room; these are NOT inferred exits."""
    by_id = {int(r['record_id']): r for r in crossings}
    groups = defaultdict(list)
    for h in holds:
        for condition in ['longer_than_h_by_labels', 'longer_than_w_plus_h_by_labels',
                          'h_not_excluded_by_label_bracket', 'w_plus_h_not_excluded_by_label_bracket']:
            if h[condition] is True:
                key = (h['response'], h['mask'], h['cadence_s'], h['target_level_s_inv'], h['w_s'], h['h_s'], condition)
                groups[key].append(by_id[h['record_id']])
    output = []
    for key, rr in sorted(groups.items()):
        model, mask, cad, L, w, h, condition = key
        item = dict(response=model, mask=mask, cadence_s=cad, level_s_inv=L, w_s=w, h_s=h,
                    label_condition=condition, crossing_context_rows=len(rr),
                    unique_target_bins=len({(r['satellite'], r['direction'], r['target_bin_start_utc']) for r in rr}),
                    status='timer_room_diagnostic; actual_ERR_state_unknown; no_physical_crossing_bound')
        for prefix in ['approach_H', 'H', 'log']:
            good = [r for r in rr if r[prefix + '_value'] is not None]
            worst = max(good, key=lambda r: r[prefix + '_value']) if good else None
            item[prefix + '_max_s_inv'] = worst[prefix + '_value'] if worst else None
            item[prefix + '_witness_record_id'] = worst['record_id'] if worst else None
            item[prefix + '_from_utc'] = worst[prefix + '_from_utc'] if worst else None
            item[prefix + '_to_utc'] = worst[prefix + '_to_utc'] if worst else None
            item[prefix + '_illustrative_2x_rho_s_inv'] = config['illustrative_empirical_margin'] * worst[prefix + '_value'] if worst else None
            for sec in config['candidate_efold_s']:
                item[f'{prefix}_context_rows_exceed_1_over_{sec}'] = sum(r[prefix + '_value'] > 1 / sec for r in good)
        output.append(item)
    return output


def make_event_table(manifest, rows, counts, coverage):
    """47x3 index: fastest confirmed entry witness; no selection of four events."""
    output = []
    for event in manifest['events']:
        # Only the special product lacks 60s by construction; no quality-driven fallback.
        cad = 300 if event['kind'] == 'special_full_month' else 60
        for level in (.001, .01, .1):
            av = [r for r in coverage if r['event_id'] == event['id'] and r['response'] == 'main_loglog'
                  and r['mask'] == 'screened' and int(r['cadence_s']) == cad and float(r['target_level_s_inv']) == level]
            scope = [r for r in rows if r['event_id'] == event['id'] and r['response'] == 'main_loglog'
                     and r['mask'] == 'screened' and int(r['cadence_s']) == cad and float(r['target_level_s_inv']) == level]
            confirmed = [r for r in scope if r['stratum'] == 'confirmed_entry']
            entry = [r for r in confirmed if r['time_from_quiet_s']]
            witness = min(entry, key=lambda r: (float(r['time_from_quiet_s']), int(r['record_id']))) if entry else None
            log_rows = [r for r in scope if r['log_value'] is not None]
            fast = max(log_rows, key=lambda r: r['log_value']) if log_rows else None
            fold_rows = [r for r in scope if r['observed_efold_s_value'] is not None]
            fold = min(fold_rows, key=lambda r: r['observed_efold_s_value']) if fold_rows else None
            line = {'event_id': event['id'], 'catalogue_onset_utc': event['onset_utc'],
                    'catalogue_peak_utc': event['peak_utc'] if event['kind'] != 'special_full_month' else None,
                    'response': 'main_loglog', 'mask': 'screened', 'cadence_s': cad, 'level_s_inv': level,
                    'availability_statuses': '|'.join(sorted({r.get('status', 'synthetic_test') for r in av})),
                    'retained_directional_bins_not_independent': sum(int(r['retained_bins']) for r in av),
                    'crossing_rows': len(scope), 'confirmed_entry_rows': len(confirmed),
                    'resolved_confirmed_entry_rows': len(entry),
                    'repeat_rows': sum(r['observed_repeat'] for r in scope),
                    'censored_rows': sum(r['stratum'].startswith('censored') or r['right_censored'] for r in scope),
                    'entry_status': 'confirmed_bin_entry' if witness else 'confirmed_entry_unresolved_same_bin' if confirmed else 'no_confirmed_entry_see_coverage',
                    'entry_record_id': witness['record_id'] if witness else None,
                    'entry_satellite': witness['satellite'] if witness else None,
                    'entry_direction': witness['direction'] if witness else None,
                    'entry_target_bin_utc': witness['target_bin_start_utc'] if witness else None,
                    'time_to_level_s': witness['time_from_quiet_s'] if witness else None,
                    'expected_inversions_to_level': witness['quiet_to_target_expected_inversions'] if witness else None,
                    'min_equivalent_bin_efold_s': fast['equivalent_bin_efold_s'] if fast else None,
                    'min_equivalent_bin_efold_record_id': fast['record_id'] if fast else None,
                    'min_observed_bin_efold_s': fold['observed_efold_s_value'] if fold else None,
                    'min_observed_bin_efold_record_id': fold['record_id'] if fold else None,
                    'count_law': 'T72 ideal_U_only; phase=0; ERR_delivery=0; uniform_full_period; clean_at_quiet_exit'}
            for period in (.05, 6.):
                count = counts.get(int(witness['record_id']), {}).get(period) if witness else None
                for metric in ['ERR_oracle_expected_lower', 'ERR_oracle_expected_upper', 'pending_tokens_expected']:
                    line[f'P{period}_{metric}'] = count[metric] if count else None
            output.append(line)
    return output


def make_handoff(config, audit, rows, holds, coverage, distributions, manifest):
    main = [r for r in distributions if r['response'] == 'main_loglog' and r['mask'] == 'screened'
            and r['cadence_s'] == 60 and r['stratum'] != 'all_retained']
    return {
        'issue': 113, 'definition': 'METHOD.md; frozen before calculation in initial PR commit',
        'accepted_T67_sha': config['accepted_T67_sha'], 'accepted_T72_sha': config['accepted_T72_sha'],
        'scope': {'windows': len(manifest['events']), 'pinned_raw_files': len(manifest['files']),
                  'T72_crossings': len(rows), 'T72_availability_rows': len(coverage),
                  'not_independent_events': True, 'instrument': 'GOES SGPS E/W separately',
                  'response': 'data32 proton only 10mmAl; NOT full38 GCR+SEP 3g/cm2'},
        'audit': audit,
        'counts_by_stratum': {s: sum(r['stratum'] == s for r in rows) for s in STRATA},
        'T72_first_label_differs_from_continuous_background_history': sum(r['T72_first_label_differs_from_continuous_history'] for r in rows),
        'right_censored_crossings': sum(r['right_censored'] for r in rows),
        'hold_candidates': [{**rule,
            'repeat_crossings': sum(r['w_s'] == rule['w_s'] for r in holds),
            'label_declines_at_least_w_plus_h_even_after_one_bin_allowance':
                sum(r['w_s'] == rule['w_s'] and r['longer_than_w_plus_h_by_labels'] is True for r in holds),
            'actual_FAST_or_SLOW_identified': False,
            'comparison_status': 'bin-labelled opportunity only, not a sufficient controller exit test',
            'required_conditions': ['legal LOW under E at an actual window phase', 'delivery and late-exit bounds',
                'last alarm plus h elapsed; no subsequent reset', 'original budget and calendar preserved'],
            } for rule in config['hold_candidates']],
        'pair_distribution_scope': 'T67 analysis-window union; complete T72 approaches including background are in interval_envelopes.csv and crossings.csv.gz',
        'main_screened_60s_extrema_by_stratum_and_level': main,
        'candidate_classes': [class_contract(1 / sec, config['legacy_rho_s_inv']) for sec in config['candidate_efold_s']],
        'conservative_conditional_fallback': {
            **class_contract(config['legacy_rho_s_inv'], config['legacy_rho_s_inv']),
            'reason': 'No uncertain interval is exempted from the entry cone by a catalogue label. Slow candidates require a separately proved causal held-state partition.',
            'status': 'retains the old conditional cone; not a new physical or future-coverage certificate'},
        'illustrative_margin': {'factor_chosen_before_calculation': config['illustrative_empirical_margin'],
            'formula': 'rho_design = factor * measured_max_H; separate per cadence/model/mask/level/stratum',
            'status': 'design sensitivity only, no statistical or physical coverage'},
        'do_not_infer': ['catalogue post-peak means FAST', 'lambda low means zero ERR or LOW',
                        'oracle-U counts follow the E service law', 'bin extrema bound within-bin or future growth',
                        'strict selection proves absence of excluded fast fronts'],
        'theorist_inputs': ['crossings.csv.gz', 'declines_and_hold.csv.gz', 'hold_sensitivity.csv', 'interval_envelopes.csv', 'growth_distribution.csv',
                           'growth_extrema.csv.gz', 'coverage.csv.gz', 'quiet_episodes.csv.gz', 'count_index.csv.gz'],
        'missing_transfer': {
            'spectral_response': 'energy/angular time series transfer from data32/proton/10mmAl to full38/background+SEP/3 and 2.5g/cm2',
            'continuous_growth': 'bound on all within-bin pairs, not selected interpolation; include future coverage/exceptions',
            'ERR_E': 'read/conditional-repair E calendar and phase, full38 grouping, pending corrections, detection/delivery law and reset/hold history',
            'early_LOW': 'counts in actual 40/60s windows and program/delivery delay; 60/300s means do not identify them'},
        'unchanged': ['D*', 'epsilon=1e-3', 'peak<=80% in any 1ms', 'program_delay<=3us', 'timing_margin=10%'],
        'physical_qualification': False, 'Q_T_certified_by_this_analysis': False,
    }
