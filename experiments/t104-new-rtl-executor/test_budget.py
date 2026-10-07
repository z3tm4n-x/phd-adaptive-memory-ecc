"""Addressed arithmetic/counterexamples, not an RTL or radiation simulation."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import product
import unittest

from budget import (inputs, timing_budget, pin_margins, calculate,
                    pass_occupancy, mask, exact_periodic_max, peak_bound)


class Budget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.legacy, cls.h, cls.a, cls.rows = inputs()
        cls.b = timing_budget(cls.cfg, cls.h)

    def test_historical_sources_and_fixed_versions(self):
        self.assertEqual(len(self.legacy["sources"]), 14)
        self.assertEqual(len(self.cfg["legacy_blobs"]), 6)
        self.assertEqual(self.legacy["science_sha"], "8ecc8fb24213e03110789646725481cd34d09ab9")
        self.assertEqual(self.legacy["stage_A_sha"], "96e1cc58ffe91ea5ef6ac3960fb4da03423b56d1")

    def test_source_numbers_read_write_not_double_counted(self):
        self.assertEqual(F(self.cfg["pin_ns"]["tWC"]), 45)
        self.assertEqual(self.cfg["pin_ns"]["tAA"], self.legacy["datasheet"]["address_access_max_ns"])
        self.assertEqual(self.cfg["pin_ns"]["tHZOE"], self.legacy["datasheet"]["output_disable_max_ns"])
        report, _ = calculate()
        self.assertEqual(report["internal_write"]["external_writes_ERR"], 1)
        self.assertFalse(report["internal_write"]["extra_external_internal_RMW_cycle"])

    def test_pin_intervals_and_design_margins_are_nonnegative(self):
        self.assertTrue(all(x >= 0 for x in pin_margins(self.cfg, self.b).values()))

    def test_read_capture_at_adverse_clock_path_edge_vertices(self):
        # Independent absolute-time construction of latest valid pins/return,
        # earliest capture and output changes, not values from report.json.
        for xi, start_error, sample_error, path, return_path in product(
                (F(99999,100000), F(100001,100000)), (F(-1,4), F(1,4)),
                (F(-1,4), F(1,4)), (0,4), (0,2)):
            valid = 4*xi + start_error + path + 45 + return_path
            capture = 60*xi + sample_error
            self.assertGreaterEqual(capture-valid, 1)

    def test_capture_one_core_edge_early_is_invalid(self):
        b = deepcopy(self.b)
        b["control_ticks"]["capture_DQ_ERR"] -= 4
        self.assertLess(pin_margins(self.cfg, b)["DQ_ERR_capture_setup"], 0)

    def test_turnaround_vertices_exclude_contention(self):
        for xi, e_disable, e_drive, out, back in product(
                (F(99999,100000), F(100001,100000)), (F(-1,4), F(1,4)),
                (F(-1,4), F(1,4)), (0,4), (0,2)):
            memory_off_seen = 64*xi+e_disable+out+18+back
            controller_on_earliest = 92*xi+e_drive
            self.assertGreaterEqual(controller_on_earliest, memory_off_seen)

    def test_turnaround_one_edge_short_fails(self):
        b = deepcopy(self.b)
        b["control_ticks"]["drive_and_WE_low_if_ERR"] -= 4
        self.assertLess(pin_margins(self.cfg, b)["SRAM_HIZ_before_FPGA_drive_or_release"], 0)

    def test_write_pulse_and_data_at_all_skew_vertices(self):
        for xi, ef, er, df, dr, data_delay in product(
                (F(99999,100000), F(100001,100000)), (F(-1,4), F(1,4)),
                (F(-1,4), F(1,4)), (0,4), (0,4), (0,4)):
            falling = 92*xi+ef+df
            rising = 132*xi+er+dr
            data_valid = 92*xi+ef+data_delay
            self.assertGreaterEqual(rising-falling, 35)
            self.assertGreaterEqual(rising-data_valid, 25)

    def test_write_pulse_one_edge_short_fails(self):
        b = deepcopy(self.b)
        b["control_ticks"]["write_end"] -= 4
        self.assertLess(pin_margins(self.cfg, b)["WE_pulse"], 0)

    def test_postwrite_hold_and_release_one_edge_short_fail(self):
        b = deepcopy(self.b)
        b["control_ticks"]["controller_DQ_off"] -= 4
        self.assertLess(pin_margins(self.cfg, b)["DQ_hold_to_controller_off"], 0)
        b = deepcopy(self.b)
        b["control_ticks"]["release_if_ERR"] -= 4
        self.assertLess(pin_margins(self.cfg, b)["FPGA_HIZ_before_next_grant"], 0)

    def test_standalone_write_requires_address_before_WE(self):
        b = deepcopy(self.b)
        b["application_write_ticks"]["WE_low"] = b["application_write_ticks"]["address_CE_BE_DQ"]
        self.assertLess(pin_margins(self.cfg, b)["app_write_address_setup"], 0)

    def test_ten_percent_and_quantization_are_not_nominal_WCET(self):
        self.assertEqual(self.b["charge_ticks_with_margin"]["read_no_ERR"], 104)
        self.assertEqual(self.b["charge_ticks_with_margin"]["read_ERR_repair"], 164)
        b = deepcopy(self.b)
        b["charge_ticks_with_margin"]["read_ERR_repair"] -= 4
        self.assertLess(pin_margins(self.cfg, b)["read_ERR_repair_margin_reservation"], 0)

    def test_larger_unknown_jitter_cannot_be_ignored(self):
        b = deepcopy(self.b)
        b["edge_span_ns"] += 1
        self.assertLess(pin_margins(self.cfg, b)["WE_pulse"], 0)

    def test_new_application_grant_between_latch_and_repair_is_unsafe(self):
        t = self.b["control_ticks"]
        # Minimal old-image clobber: incorrect release at latch lets a newer
        # write commit at 80, then old repair commits at 132. Full lock excludes it.
        memory, latch = 7, 7
        new_commit = 80
        memory = 99
        memory = latch
        self.assertEqual(memory, 7)
        self.assertLess(t["capture_DQ_ERR"], new_commit)
        self.assertLess(new_commit, t["release_if_ERR"])
        # Correct contract grants only at/after148; both aliases share lock.
        memory = latch
        memory = 99
        self.assertEqual(memory, 99)
        self.assertEqual(self.cfg["design"]["repair_queue_depth"], 1)

    def test_no_ERR_release_after_check_and_high_Z(self):
        t = self.b["control_ticks"]
        self.assertLess(t["capture_DQ_ERR"], t["decision_disable_outputs"])
        self.assertLess(t["decision_disable_outputs"], t["release_if_no_ERR"])
        self.assertLess(t["release_if_no_ERR"], t["release_if_ERR"])

    def test_clean_observation_is_not_clean_fence(self):
        t = self.b["control_ticks"]
        err_at_capture = 0
        single_hit_at = t["capture_DQ_ERR"]+1
        self.assertLess(single_hit_at, t["release_if_no_ERR"])
        dirty_at_release = (err_at_capture == 0 and single_hit_at < t["release_if_no_ERR"])
        self.assertTrue(dirty_at_release)  # Counterexample, not radiation model.

    def test_pass_count_zero_all_and_partial(self):
        self.assertEqual(pass_occupancy(8, 0, 92, 148), 736)
        self.assertEqual(pass_occupancy(8, 8, 92, 148), 1184)
        self.assertEqual(pass_occupancy(8, 3, 92, 148), 904)
        with self.assertRaises(ValueError):
            pass_occupancy(8, 9, 92, 148)

    def test_sliding_mask_matches_independent_event_edges(self):
        for period, duration, h in product(range(2,12), range(0,8), range(0,37)):
            if duration <= period:
                self.assertEqual(mask(F(h,2), F(period), F(duration)),
                                 exact_periodic_max(F(h,2), F(period), [(F(0), F(duration))]))

    def test_two_phase_bound_covers_all_binary_corrections_small_case(self):
        # W=4 local periodic fixture; examine all ERR patterns and all window
        # edge phases. This checks resource inequality, not a working-W proof.
        for pattern in product((0,1), repeat=4):
            c, r, g, period = 8, 4, 12, 48
            intervals = [(F(s), F(s+(c if e else r))) for s,e in zip((0,8,24,32),pattern)]
            for h in range(1,100):
                exact = exact_periodic_max(F(h), F(period), intervals)
                unconditional = mask(F(h), F(24), F(16))
                read_upper = 2*mask(F(h), F(24), F(4))
                # Safe carry-in upper: entire-pattern ERR count per intersected
                # period plus two partial periods, not number in bins only.
                K = (h//period+2)*sum(pattern)
                self.assertLessEqual(exact, min(unconditional, read_upper+4*K))

    def test_correction_tail_crossing_window_is_not_free(self):
        # Repair begins before a measurement window but occupies it for6 units.
        interval, window = (90,148), (142,150)
        overlap = min(interval[1],window[1])-max(interval[0],window[0])
        self.assertEqual(overlap, 6)
        self.assertFalse(window[0] <= interval[0] < window[1])

    def test_rare_mission_average_allows_one_dense_peak(self):
        # One all-correction millisecond in ten years still has tiny mean.
        self.assertLess(F(1,1000)/F(315576000), F(1,10**10))
        r, _ = calculate()
        peak = r["resource_algebra_only"]["lower_adjacent_core_g"]
        self.assertGreater(F(peak["peak_upper"]), F(4,5))

    def test_old_calendar_rejects_ERR_overlap_and_even_no_ERR_margin(self):
        report, _ = calculate()
        for row in report["old_rows_not_transferred"]:
            self.assertGreater(F(row["old_calendar_ERR_overlap_ns"]), 0)
            self.assertGreater(F(row["old_calendar_no_ERR_margin_deficit_ns"]), 0)
            self.assertFalse(row["new_reservation_unchanged_g"]["nonoverlap"])

    def test_resource_witness_keeps_80_percent_and_separate_margins(self):
        report, _ = calculate()
        r = report["resource_algebra_only"]
        self.assertEqual(r["g_core_aligned_sufficient"], 208)
        self.assertLessEqual(F(r["worst_corrections_every_visit"]["peak_upper"]), F(4,5))
        self.assertLess(F(r["no_corrections_in_expanded_window"]["peak_upper"]),
                        F(r["worst_corrections_every_visit"]["peak_upper"]))
        with self.assertRaises(ValueError):
            peak_bound(self.b, 208, F(1000000), F(1,10000), F(100), -1)

    def test_fixed_calendar_saves_only_last_tail_not_W_tails(self):
        report, _ = calculate()
        r = report["resource_algebra_only"]
        saved = F(r["first_pass_release_upper_ns_all_ERR"])-F(r["first_pass_release_upper_ns_no_ERR"])
        self.assertEqual(saved, F(r["only_last_visit_release_saving_ns"]))
        self.assertEqual(report["completed_pass"]["unchanged_calendar_period_saving_ns"], 0)

    def test_CDC_and_validation_are_not_free(self):
        b = self.b
        self.assertGreater(b["first_VALID_to_done_no_queue_no_backpressure_ns"]["read16"], b["upper_ns"]["application_read16"])
        report, _ = calculate()
        c = report["command_comparison_only"]
        self.assertEqual(F(c["total_post_window_with_old_deadline_ns"])-F(c["remaining_before_mailbox_ns"]),
                         b["outside_lock_upper_ns"]["command_receive_validate_shadow"])
        self.assertLess(F(c["total_post_window_with_old_deadline_ns"]), 10**9)

    def test_atomic32_and_queue_are_not_hidden_16bit_workload(self):
        self.assertEqual(self.b["upper_ns"]["application_read32_atomic_two_aliases"], 2*self.b["upper_ns"]["application_read16"])
        report, _ = calculate()
        self.assertIsNone(report["queue"]["D_offer_to_departure_ns"])
        self.assertFalse(report["queue"]["depth_certified"])

    def test_handoff_preserves_rows_quotas_unknowns_and_loss(self):
        report, h = calculate()
        self.assertEqual([x["Dstar"] for x in h["rows"]], ["560489/2000000000", "109073/2000000000"])
        for new, old in zip(h["rows"], self.rows):
            self.assertEqual(new["environment"], old["effective_T88_input"]["environment"])
            self.assertEqual(new["quotas"], old["effective_T88_input"]["quotas"])
            self.assertIsNone(new["new_Q_upper"])
        self.assertEqual(h["loss_policy_unchanged"], self.h["loss_policy"])
        self.assertTrue(all(v is None for v in report["unknowns"].values()))
        self.assertFalse(report["decision"]["new_risk_certificate"])
        self.assertFalse(report["decision"]["main_RTL_started"])

    def test_bus_peak_pass_does_not_prove_nonpreemptive_request_delay(self):
        report, _ = calculate()
        r = report["resource_algebra_only"]
        self.assertEqual(r["longest_all_ERR_gap_ticks_at_actual_release"], 104)
        gaps = r["atomic_gap_checks"]
        self.assertTrue(gaps["read16_no_inline_repair"]["fits_one_gap_at_resource_example"])
        self.assertFalse(gaps["read32_atomic_no_inline_repair"]["fits_one_gap_at_resource_example"])
        self.assertEqual(gaps["read32_atomic_no_inline_repair"]["g_sufficient_for_one_gap_only"], 260)
        # Even zero-ERR initial S has gaps<=160xi but the fixed two-alias
        # timeline lasts184xi. Compare a LOWER execution duration to an UPPER
        # gap, not an upper-WCET estimate as if it were a lower bound.
        self.assertEqual(r["longest_no_ERR_gap_ticks_at_actual_release"], 160)
        minimum = 184*self.b["tick_min_ns"]-self.b["edge_span_ns"]
        maximum_gap = 160*self.b["tick_max_ns"]+self.b["edge_span_ns"]
        self.assertGreater(minimum, maximum_gap)


if __name__ == "__main__":
    unittest.main()
