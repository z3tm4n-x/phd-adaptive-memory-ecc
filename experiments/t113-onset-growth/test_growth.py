"""Boundary cases that matter to the interpretation of T113."""
import math
import json
import itertools
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

from onset_growth import (class_contract, classify, extremum, first_efold,
                          h_transform, hold_interval, pair_metrics,
                          quiet_episodes, segments)


class GrowthTests(unittest.TestCase):
    def test_H_below_and_above_level(self):
        np.testing.assert_allclose(h_transform([0, .5, 1, math.e], 1), [0, .5, 1, 2])

    def test_H_rejects_unknown_and_negative(self):
        for values in ([1, np.nan], [1, np.inf], [-1, 1]):
            with self.assertRaises(ValueError):
                h_transform(values, 1)

    def test_equivalent_time_is_not_sample_interval(self):
        h, log = pair_metrics([1, math.exp(3)], 1, 60)
        self.assertAlmostEqual(1 / log[0], 20)
        self.assertAlmostEqual(h[0], .05)
        self.assertEqual(first_efold([1, math.exp(3)], 60), (60, 0, 1))
        self.assertGreater(log[0], 1 / 60)

    def test_below_threshold_not_a_log_slope(self):
        h, log = pair_metrics([.00001, .001], .001, 60)
        self.assertTrue(np.isnan(log[0]))
        self.assertAlmostEqual(h[0], .99 / 60)

    def test_efold_allows_intermediate_decline(self):
        self.assertEqual(first_efold([2, 1, 1.5, 3], 60), (120, 1, 3))

    def test_efold_no_crossing_is_missing_not_zero(self):
        self.assertIsNone(first_efold([2, 2, 2.1, 1.9], 60))

    def test_efold_frontier_against_exhaustive_oracle(self):
        rng = np.random.default_rng(113)
        for n in [1, 2, 8, 30, 100]:
            for _ in range(30):
                x = np.exp(rng.uniform(0, 5, n))
                candidates = [(60 * (j-i), i, j) for i in range(n) for j in range(i+1, n)
                              if x[i] <= x[j] / math.e]
                self.assertEqual(first_efold(x, 60), min(candidates) if candidates else None)

    def test_gap_is_not_interpolated(self):
        t = np.array([0, 60, 180, 240])
        self.assertEqual(segments(t, np.ones(4), np.ones(4, bool), np.zeros(4), 60), [(0, 2), (2, 4)])

    def test_quality_and_signature_split(self):
        t = np.arange(6) * 60
        self.assertEqual(segments(t, np.ones(6), [1, 1, 0, 1, 1, 1], [0, 0, 0, 0, 1, 1], 60),
                         [(0, 2), (3, 4), (4, 6)])

    def test_strict_removal_cannot_validate_fast_front(self):
        t, x = np.arange(3)*60, np.array([1., math.exp(3), 1.])
        broad = segments(t, x, [1, 1, 1], [0, 0, 0], 60)
        strict = segments(t, x, [1, 0, 1], [0, 0, 0], 60)
        self.assertEqual(broad, [(0, 3)])
        self.assertEqual(strict, [(0, 1), (2, 3)])
        self.assertTrue(all(b-a == 1 for a, b in strict))

    def test_confirmed_entry_does_not_depend_on_future_peak(self):
        for phase in ['pre_peak', 'post_peak', 'unknown_peak']:
            self.assertEqual(classify(True, True, phase), 'confirmed_entry')

    def test_repeat_and_censored_are_separate(self):
        self.assertEqual(classify(False, True, 'post_peak'), 'repeat_post_peak')
        self.assertEqual(classify(False, False, 'post_peak'), 'censored_repeat')

    def test_hold_long_decline_still_unknown_state(self):
        r = hold_interval(0, 600, 60, 60, 120)
        self.assertEqual(r['label_duration_lower_s'], 540)
        self.assertTrue(r['longer_than_w_plus_h_by_labels'])
        self.assertTrue(r['actual_ERR_state'].startswith('unknown'))

    def test_hold_boundary_one_bin_allowance(self):
        self.assertFalse(hold_interval(0, 180, 60, 60, 120)['longer_than_w_plus_h_by_labels'])
        self.assertTrue(hold_interval(0, 240, 60, 60, 120)['longer_than_w_plus_h_by_labels'])
        marginal = hold_interval(0, 120, 60, 40, 90)
        self.assertFalse(marginal['longer_than_h_by_labels'])
        self.assertTrue(marginal['h_not_excluded_by_label_bracket'])
        self.assertTrue(marginal['w_plus_h_not_excluded_by_label_bracket'])

    def test_hold_missing_start_not_zero(self):
        self.assertIsNone(hold_interval(None, 600, 60, 40, 90)['duration_bin_starts_s'])

    def test_quiet_end_is_last_bin_end(self):
        t = np.arange(6)*60
        r = quiet_episodes(t, np.array([0, 0, 1, 0, 0, 0]), np.ones(6, bool), np.zeros(6), 60, .1, 120)
        self.assertEqual(len(r), 1)
        self.assertTrue(r[0]['confirmed_start'])
        self.assertEqual(r[0]['end_time'], 300)
        self.assertFalse(r[0]['right_censored'])

    def test_quiet_gap_does_not_end_episode(self):
        r = quiet_episodes(np.arange(6)*60, np.array([0, 0, 1, 0, 0, 0]),
                           np.array([1, 1, 1, 1, 0, 1], bool), np.zeros(6), 60, .1, 120)
        self.assertTrue(r[0]['right_censored'])
        self.assertIsNone(r[0]['end_time'])

    def test_repeated_quiet_episode_gets_new_causal_start(self):
        r = quiet_episodes(np.arange(8)*60, np.array([0, 0, 1, 0, 0, 1, 0, 0]),
                           np.ones(8, bool), np.zeros(8), 60, .1, 120)
        self.assertEqual(len(r), 2)
        self.assertTrue(all(v['confirmed_start'] for v in r))

    def test_empty_or_all_missing_not_synthetic_zero(self):
        self.assertEqual(segments([], [], [], [], 60), [])
        self.assertEqual(segments([0, 60], [np.nan, np.nan], [0, 0], [0, 0], 60), [])
        self.assertIsNone(extremum(np.array([0., -1., np.nan])))

    def test_conditional_class_does_not_qualify_response(self):
        c = class_contract(1/180, .048)
        self.assertFalse(c['physical_qualification'])
        self.assertIn('ERR_law_under_E', c['unknown'])
        self.assertIn('possible causal exit', c['entry_scope'])

    def test_whole_pipeline_background_repeat_and_overlap_union(self):
        # Two overlapping windows, each with a first *recorded* T72 crossing;
        # both already exceeded L in their background. The reference history
        # proves a repeat, and the same native pair is counted only once.
        import pipeline as p
        cfg = json.loads((p.HERE / 'config.json').read_text())
        cfg['quiet_history_s'] = 120
        events = [dict(id=name, kind='NOAA_catalogue', analysis_start=p.iso(360),
                       analysis_end_exclusive=p.iso(540), background_start=p.iso(0),
                       onset_utc=p.iso(360), peak_utc=p.iso(300)) for name in ['A', 'B']]
        source = dict(name='synthetic.nc', sha256='synthetic-only', version='test',
                      satellite=16, cadence_s=60, date='19700101')
        accepted, avail = [], []
        x = np.array([0, 0, .0002, .0011, .004, .0005, .0012, .005, .0005])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'outputs').mkdir()
            for sat, cad in itertools.product([16, 18, 19], [60, 300]):
                use = sat == 16 and cad == 60
                n = len(x) if use else 0
                arrays = dict(time=np.arange(n)*60, signature=np.zeros(n, int), file_index=np.zeros(n, int))
                arrays.update({k: np.repeat(x[:, None], 2, axis=1) if use else np.empty((0, 2))
                               for k in ['main_loglog', 'core_only']})
                arrays.update({k: np.ones((n, 2), bool) for k in ['screened', 'strict', 'core_strict']})
                np.savez(root / f'g{sat}_{cad}.npz', **arrays)
                for e, model, mask, direction in itertools.product(events, cfg['responses'], cfg['masks'], ['E', 'W']):
                    base = dict(event_id=e['id'], satellite=sat, cadence_s=cad, response=model, mask=mask, direction=direction)
                    for L in cfg['levels_s_inv']:
                        avail.append({**base, 'target_level_s_inv': L, 'retained_bins': 3 if use else 0,
                                      'crossing_rows': 1 if use and L == .001 else 0})
                    if not use:
                        continue
                    accepted.append({**base, 'record_id': len(accepted)+1, 'target_level_s_inv': .001,
                        'target_bin_start_utc': p.iso(360), 'target_bin_response_s_inv': .0012,
                        'target_source_name': source['name'], 'target_source_sha256': source['sha256'],
                        'processing_version': source['version'], 'signature_id': 0,
                        'target_screened': True, 'target_strict': True, 'target_core_strict': True,
                        'quiet_exit_bin_start_utc': p.iso(120), 'repeat_rise_start_utc': p.iso(300),
                        'first_target_in_quiet_episode': True, 'segment_type': 'post_peak_growth',
                        'quiet_to_target_expected_inversions': sum(x[2:6])*60, 'time_from_quiet_s': 240})
            (root / 'outputs/onsets.csv.gz').write_bytes(p.serialize('onsets.csv.gz', accepted))
            (root / 'outputs/availability.csv').write_bytes(p.serialize('availability.csv', avail))
            (root / 'outputs/available_counts.csv.gz').write_bytes(p.serialize('counts.csv.gz', []))
            with patch.object(p, 'T72', root), patch('builtins.print'):
                result = p.analyze(cfg, {'events': events, 'files': [source]}, root)
        rows = result['crossings.csv.gz']
        self.assertEqual(len(rows), 24)
        self.assertTrue(all(r['stratum'] == 'repeat_post_peak' for r in rows))
        self.assertTrue(all(r['T72_first_label_differs_from_continuous_history'] for r in rows))
        self.assertTrue(all(r['H_exceeds_1_over_60'] for r in rows))
        self.assertTrue(all(not r['right_censored'] for r in rows))
        self.assertTrue(all(r['count_status'] == 'no_T72_count_for_this_record' for r in rows))
        dist = next(r for r in result['growth_distribution.csv'] if r['response'] == 'main_loglog'
                    and r['mask'] == 'screened' and r['cadence_s'] == 60 and r['target_level_s_inv'] == .001
                    and r['stratum'] == 'repeat_post_peak' and r['zone'] == 'above_level' and r['metric'] == 'log')
        self.assertEqual(dist['unique_adjacent_pairs'], 2)  # one pair per direction, not per window
        self.assertEqual(dist['pairs_exceed_1_over_60'], 2)
        self.assertEqual(len(result['event_levels.csv']), 6)
        self.assertEqual(len(result['declines_and_hold.csv.gz']), 48)


if __name__ == '__main__':
    unittest.main()
