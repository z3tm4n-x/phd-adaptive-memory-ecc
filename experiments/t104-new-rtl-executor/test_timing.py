"""Directed exact checks of the first timing gate; not RTL formal proof."""
from fractions import Fraction as F
import sys
import unittest

from timing import (ROOT, NS, calculate, ceil, fixed_phase_cycle, load_inputs,
                    queue_capacity, staged_choice)

sys.path.insert(0, str(ROOT / "experiments/t96-hybrid-rule-implementation"))
import reference as A  # Accepted oracle; never modified by this package.


class Timing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.h, cls.a = load_inputs()
        cls.r = calculate()
        cls.tm, cls.tp = F(99999, 10**14), F(100001, 10**14)

    def test_original_joint_and_application_limits(self):
        self.assertEqual(F(self.r["limits"]["joint_U_s"]), F(99999, 1100000000000))
        self.assertEqual(F(self.r["limits"]["application_s"]), 45*NS)
        self.assertEqual(F(self.r["limits"]["margin"]), F(11, 10))
        self.assertEqual(self.r["fixed_phase_candidates"][0]
                         ["minimum_4tick_slot_for_optimistic_U_with_margin"], 108)

    def test_fast_corner_rounding_then_slow_corner_check(self):
        expected = (("4", 12, "48.00048"), ("2", 23, "46.00046"),
                    ("1", 46, "46.00046"), ("1/2", 91, "45.500455"),
                    ("1/4", 181, "45.2504525"))
        for q, n, worst_ns in expected:
            with self.subTest(q=q):
                r = fixed_phase_cycle(q, 45*NS, self.tm, self.tp)
                self.assertEqual(r["phase_count"], n)
                self.assertEqual(r["slowest_interval_s"], F(worst_ns)*NS)
                self.assertGreaterEqual(n*F(q)*self.tm, 45*NS)
                self.assertLess((n-1)*F(q)*self.tm, 45*NS)

    def test_45_integer_ticks_do_not_meet_read_cycle_minimum(self):
        self.assertEqual(45*self.tm, F("44.99955")*NS)
        self.assertLess(45*self.tm, 45*NS)

    def test_fine_phases_do_not_fix_application_limit(self):
        row = self.r["fixed_phase_candidates"][-1]
        self.assertTrue(row["U_arithmetic_fits_before_unknown_extras"])
        self.assertFalse(row["application_arithmetic_fits_before_unknown_extras"])
        self.assertFalse(row["physical_timing_qualified"])
        self.assertEqual(F(row["U_residual_s"]), F(896009, 2200000)*NS)

    def test_continuous_limit_excludes_every_fixed_phase_count(self):
        necessary = 45*NS*self.tp/self.tm
        self.assertEqual(F(self.r["fixed_phase_necessary_application_s"]), necessary)
        self.assertGreater(necessary, 45*NS)
        # Analytic condition: x*tm >=45 ns implies x*tp >=45*tp/tm.
        for q in (F(1, 4), F(1, 1000), F(1, 10**9)):
            r = fixed_phase_cycle(q, 45*NS, self.tm, self.tp)
            self.assertGreaterEqual(r["slowest_interval_s"], necessary)

    def test_positive_path_counterexample_is_not_a_measurement(self):
        r = self.r["positive_path_counterexample"]
        self.assertEqual(F(r["completion_s"]), F("45.25")*NS)
        self.assertGreater(F(r["completion_s"]), 45*NS)
        self.assertIn("hypothetical", r["status"])

    def test_unknowns_are_not_zero_and_no_physical_pass(self):
        self.assertTrue(all(x is None for x in self.r["physical_upper_bounds_s"].values()))
        self.assertTrue(all(not x["physical_timing_qualified"]
                            for x in self.r["fixed_phase_candidates"]))
        self.assertFalse(self.r["decision"]["continue_main_RTL"])
        self.assertFalse(self.r["decision"]["all_possible_architectures_excluded"])

    def test_pin_write_turnaround_is_separate_from_cycle_number(self):
        r = self.r["write_turnaround_constraints"]
        self.assertEqual(F(r["OE_high_to_drive_pin_min_s"]), 18*NS)
        self.assertEqual(F(r["write_end_after_DQ_stable_min_s"]), 25*NS)
        self.assertEqual(F(r["OE_low_WE_pulse_min_s"]), 43*NS)
        self.assertFalse(r["full_pin_timing_closed"])

    def test_early_cutoff_preserves_original_deadline_and_lease(self):
        r = self.r["command_projection"]
        self.assertEqual(r["original_activation_ticks"], 2100011001)
        self.assertEqual(r["last_early_edge_ticks"], 2100011000)
        self.assertEqual(r["first_eligible_edge_ticks"], 2100011004)
        self.assertEqual(r["original_lease_ticks"], 2940811639)
        self.assertEqual(F(r["zero_jitter_early_total_path_s"]), F(9999999999, 10**10))
        self.assertLess(F(r["diagnostic_early_total_path_s"]),
                        F(r["zero_jitter_early_total_path_s"]))

    def test_all_original_windows_keep_residue_without_enumerating_mission(self):
        p = A.Parameters.accepted()
        self.assertEqual(p.stride % 4, 0)
        self.assertEqual(p.deadline(0) % 4, 1)
        for i in (0, 1, 2, p.J-1):
            a = p.deadline(i)
            self.assertEqual(a % 4, 1)
            self.assertEqual(a // 4 * 4, a-1)
            self.assertEqual(ceil(F(a, 4))*4, a+3)

    def test_early_shadow_never_enables_a_previous_decision(self):
        p = self.r["command_projection"]
        a, cutoff = p["original_activation_ticks"], p["last_early_edge_ticks"]
        old, new = object(), object()
        # Old and new LOW may overlap: a separate not_before is still needed.
        for d in range(cutoff-8, cutoff+13, 4):
            self.assertIs(staged_choice(old, new, a, d, cutoff, cutoff),
                          old if d < a else new)

    def test_staged_command_loss_or_lateness_cannot_restore_LOW(self):
        p = self.r["command_projection"]
        a, cutoff = p["original_activation_ticks"], p["last_early_edge_ticks"]
        self.assertIsNone(staged_choice("old", "new", a, a+3, cutoff, cutoff, revoked=True))
        self.assertIsNone(staged_choice("old", "new", a, a+3, cutoff+1, cutoff))

    def test_reference_still_buffers_early_and_rejects_late_window(self):
        p = A.Parameters.accepted()
        for now, result in ((p.deadline(0)-1, "buffer_until_deadline"),
                            (p.deadline(0), "LOW"), (p.deadline(0)+3, "alarm")):
            r = A.Rule(p)
            r.epoch_begin(1, 0, p.config_id)
            packet = A.Message(0, 1, 0, p.config_id, 0, p.window,
                count=0, loss_upper=0, live_ticks=p.window, complete=True,
                calibration_ok=True, clock_ok=True, integrity_ok=True, loss_contract_ok=True)
            self.assertEqual(r.message(packet, now), result)

    def test_finite_queue_needs_count_contract_as_well_as_work(self):
        # Arbitrarily many tiny jobs fit a finite work burst. No depth follows.
        total_work = F(145)*NS
        count = 100000
        self.assertEqual(count*(total_work/count), total_work)
        self.assertGreater(count, self.cfg["queue_candidate"]["total_outstanding_capacity"])
        r = self.r["queue"]
        self.assertEqual(r["required_entries_conservative"], 12)
        self.assertEqual(queue_capacity(8, 2000000, F(r["delay_bound_used_s"])), 12)
        self.assertTrue(r["fits_under_both_count_and_original_work_contracts"])
        self.assertFalse(r["actual_workload_confirmed"])

    def test_existing_skip_write_regressions_remain_in_accepted_report(self):
        names = self.a["tests"]
        self.assertEqual(self.a["test_count"], 49)
        for suffix in ("test_committed_skip_allows_crossing_application_write_W8",
                       "test_committed_skip_crossing_write_survives_ERR_and_loss",
                       "test_committed_skip_crossing_write_at_working_W_local_state",
                       "test_skip_calendar_guards_and_executed_U_write_lock"):
            self.assertIn("test_reference.Fixed."+suffix, names)


if __name__ == "__main__":
    unittest.main()
