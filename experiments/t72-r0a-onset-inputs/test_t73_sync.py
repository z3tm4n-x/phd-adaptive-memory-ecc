"""New-SHA checks supplement, not replace, the 27 historical regressions."""
import copy
from fractions import Fraction as F
import itertools
import unittest

from confirm_t73_sync import (SETS, compare_inputs, evaluate, expand, full_paired_checks,
                              merge, paired_edge, read_new, source_check, text_claims)
from t73_calendar import Calendar, MAX_TIME
from verify_t73 import calculate, t58


class SyncChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = read_new()
        cls.expanded = expand(cls.doc)
        cls.exact, cls.rows, cls.summaries = evaluate(cls.doc, cls.expanded)

    def test_new_source_bytes_and_four_independent_inputs(self):
        self.assertEqual(len(source_check()), 3)
        compared = compare_inputs(self.doc, self.expanded)
        self.assertEqual(sum(r['status'] != 'same' for r in compared), 2)
        root = {'x': {'a': 1, 'b': 2}, 'list': [1, 2]}
        self.assertEqual(merge(root, {'x': {'a': 3}, 'list': [4]}),
                         {'x': {'a': 3, 'b': 2}, 'list': [4]})
        self.assertEqual(root, {'x': {'a': 1, 'b': 2}, 'list': [1, 2]})
        doc = copy.deepcopy(self.doc)
        doc['variant_definitions'][0]['overrides']['monitor'] = {'k': -999}
        expanded = expand(doc)
        self.assertEqual(expanded[0]['input']['monitor']['k'], -999)
        self.assertEqual(expanded[1]['input']['monitor']['k'], 18500)

    def test_new_JSON_eight_rows_and_text_directions(self):
        self.assertEqual(len(self.summaries), 8)
        self.assertGreater(len(text_claims(self.exact)), 100)
        # Negative controls: reject a silent quota reduction or reversed bound.
        doc = copy.deepcopy(self.doc)
        doc['variant_definitions'][1]['overrides']['whole_mission_quotas']['rho0'] = '0'
        with self.assertRaises(AssertionError):
            compare_inputs(doc, expand(doc))
        doc = copy.deepcopy(self.doc)
        doc['verified_results'][0]['directed_formula_bounds']['fixed_cost_lower']['lower'] = '1'
        with self.assertRaises(AssertionError):
            evaluate(doc, self.expanded)

    def test_paired_edge_full_W_and_small_direct_windows(self):
        self.assertEqual(len(full_paired_checks(self.expanded, self.exact)), 8)
        cases = windows = 0
        for N, c in itertools.product([1, 2, 3, 4, 8], [1, 2]):
            for M in range(2*c*N, 2*c*N+2*N+1):
                paired_edge(N, c, M)
                # Independent integration of actual occupied intervals, not
                # the residue/prefix formula. All breakpoint pairs over two
                # periods; linearity covers intermediate real endpoints.
                blocks = [(period*M+i*M//N, period*M+i*M//N+2*c)
                          for period in range(2) for i in range(N)]
                points = sorted({0, 2*M} | {t for block in blocks for t in block})
                for a, b in itertools.combinations(points, 2):
                    occupied = sum(max(0, min(b, y)-max(a, x)) for x, y in blocks)
                    difference_numerator = M*occupied-N*2*c*(b-a)
                    self.assertLessEqual(abs(difference_numerator), 2*c*M)
                    windows += 1
                cases += 1
        self.assertEqual(cases, 82)
        print(f'New paired edge: {cases} small calendars, {windows} direct windows; '
              '8 full-W calendars, 4194304 start/end extrema.')
        with self.assertRaises(AssertionError):
            paired_edge(4, 2, 15)  # overlap is outside the proved class

    def test_arbitrary_phase_edge_and_necessary_bound(self):
        cases = 0
        for tau in range(2, 15):
            for c in range(1, tau+1):
                for phase in range(tau):
                    for horizon in range(2*tau+1):
                        work = sum(max(0, min(horizon, start+c)-max(0, start))
                                   for start in [phase-tau, phase, phase+tau])
                        self.assertGreaterEqual(F(work), F(c*horizon, tau)-2*c)
                        cases += 1
        print(f'New arbitrary-phase edge: {cases} one-word finite windows; sum over W is valid.')
        bound = self.doc['fixed_class_necessary_bound']
        self.assertEqual(bound['arbitrary_phase_cost_edge'], '2*W*c_plus/T')
        self.assertEqual(bound['J0'], 24540)
        for variant in self.expanded:
            name, cfg = variant['set'], variant['input']
            sc, s = cfg['scenario'], cfg['service']
            cp = s['c_ticks']*F(s['tick_nominal_s'])*F(s['constant_clock_scale_max'])
            cm = s['c_ticks']*F(s['tick_nominal_s'])*F(s['constant_clock_scale_min'])
            tau_min = sc['W']*cm/(F(bound['tax_limit'])+2*sc['W']*cp/F(sc['T_s']))
            J = t58.floor(F(bound['witness_peak_length_s'])/tau_min)+2
            self.assertEqual(J, 24268 if s['c_ticks'] == 91 else 24538)
            self.assertLessEqual(J, bound['J0'])
            for shield in ['2.5', '3']:
                v = self.exact[name, shield]
                self.assertEqual(v['E3_arbitrary_phase_tau_min_s'], tau_min)
                self.assertEqual(v['E3_cells'], bound['cells'])
                self.assertGreater(v['E3_risk_lower'], F('.001'))
                # Distinguish the historical stronger/special-phase formula.
                self.assertLess(tau_min, v['E3_tau_min_s'])

    def test_strong_constant_M_next_resources_and_price(self):
        for variant in self.expanded:
            name, cfg = variant['set'], variant['input']
            s, sc, q = cfg['service'], cfg['scenario'], cfg['whole_mission_quotas']
            for shield in ['2.5', '3']:
                v = self.exact[name, shield]
                eps = F(sc['epsilon'])
                intercept = sum(F(q[x]) for x in ['rho0', 'delta_exec', 'delta_svc']) + v['risk_direct']
                slope = F(sc['n']-1, 2*sc['n']*sc['W'])*v['S2_formula_exact']+q['K0']*v['B']/sc['W']
                quantum = F(s['tick_nominal_s'])*F(s['constant_clock_scale_max'])
                closed_M = t58.floor((eps-intercept)/(slope*quantum))
                self.assertEqual(closed_M, v['fixed_strong_M'])
                self.assertLessEqual(v['fixed_risk_upper'], eps)
                self.assertGreater(v['fixed_risk_next_quantum'], eps)
                self.assertLessEqual(v['S2_formula_exact'], v['S2_declared_upper'])
                self.assertGreaterEqual(closed_M, v['fixed_E1_M'])
                self.assertTrue(v['fixed_resource_ok'])
                duty = F(sc['W']*s['c_ticks'], closed_M)
                edge = 2*s['c_ticks']*quantum/F(sc['T_s'])
                self.assertEqual(v['fixed_cost_lower'], duty-edge)
                self.assertEqual(v['fixed_cost_upper'], duty+edge)
                self.assertLess(v['quiet_returns_upper'], v['fixed_cost_lower'])
            # The 279/560 candidates are historical only; not the optimizer.
            self.assertEqual([e['fixed_candidate_frame_ticks'] for e in cfg['environments']], [279, 560])

    def test_LOW_all_counts_new_phi_delivery_boundary_and_WCET(self):
        for index in [0, 2]:  # both distinct monitor/service configurations
            cfg = self.expanded[index]['input']
            s, m, v = cfg['service'], cfg['monitor'], self.exact[SETS[index], '2.5']
            self.assertLessEqual(F(m['phi_rational_lower']), 1-t58.exp_neg(F(m['z']))[1])
            self.assertGreater(v['LOW_margin'], 0)
            cal = Calendar(cfg['scenario']['W'], s['long_multiplier'], s['c_ticks'], s['g_ticks'],
                           s['fence_ticks'], s['decision_lead_ticks'], int(s['hold_ticks']), MAX_TIME)
            for count in range(m['k']+1):
                self.assertTrue(cal.message(count, at=0, lease_end=1, count=count,
                                            k=m['k'], qualified=v['LOW_margin'] >= 0))
            self.assertFalse(cal.message(m['k']+1, at=0, lease_end=1, count=m['k']+1,
                                         k=m['k'], qualified=True))
            # Largest safe integer deadline and its immediately unsafe neighbor.
            q = F(s['tick_nominal_s'])*F(s['constant_clock_scale_max'])
            limit = t58.floor(v['d_safe_lower_s']/q)
            changed = copy.deepcopy(cfg)
            changed['monitor']['delivery_computation_deadline_after_window_ticks'] = str(limit)
            self.assertGreaterEqual(calculate(changed, changed['environments'][0])['time_margin_s'], 0)
            changed['monitor']['delivery_computation_deadline_after_window_ticks'] = str(limit+1)
            self.assertLess(calculate(changed, changed['environments'][0])['time_margin_s'], 0)
        for name in SETS[2:]:
            cfg = self.expanded[SETS.index(name)]['input']
            m = cfg['monitor']
            self.assertEqual(F(m['a_M']), 10**11)
            self.assertEqual(F(m['A_M'])/F(m['a_M']), F('1.001'))
            self.assertEqual(F(m['required_delivery_computation_physical_max_s']), F('.009'))
            self.assertEqual(self.exact[name, '2.5']['required_joint_U_WCET_physical_s'], F('0.0000000899991'))
            self.assertEqual(self.exact[name, '2.5']['nominal_90ns_U_clock_margin_s'], F('-0.0000000000009'))

    def test_preserved_failures_and_return_price_repair(self):
        self.assertGreater(self.exact[SETS[1], '2.5']['known_T72_subtotal_if_two_missing_quotas_excluded'], F('.001'))
        for shield in ['2.5', '3']:
            first, second = [self.exact[name, shield] for name in SETS[2:]]
            self.assertGreater(first['quiet_returns_upper'], F('.01'))
            self.assertLess(second['quiet_returns_upper'], F('.01'))
            self.assertTrue(second['passes_also_24h_and_returns'])
            self.assertEqual(first['risk_upper'], second['risk_upper'])
            self.assertGreater(second['strip_margin_s'], 0)
        # Descriptive correction agrees with the unchanged executable rule.
        for variant in self.expanded[2:]:
            s = variant['input']['service']
            self.assertEqual(s['long_multiplier'], 85)
            self.assertEqual(s['mandatory_slots'], 'j divisible by 85')


if __name__ == '__main__':
    unittest.main()
