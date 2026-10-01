"""Focused scientific invariants and counterexamples for the T68 input package."""
import json
import csv
import math
import unittest
import numpy as np
import run


class PhysicsAndUnits(unittest.TestCase):
    def test_duration_seconds_and_zero_components(self):
        f=np.array([[1.,86400.,0.],[2.,172800.,0.]])
        p=np.array([[1.,1.,0.],[2.,2.,0.]])
        self.assertEqual(run.effective_duration(f,p)["max_days"],1.)

    def test_positive_fluence_zero_peak_is_not_ignored(self):
        f=np.array([[1.,1.],[2.,0.]])
        p=np.array([[1.,0.],[2.,1.]])
        with self.assertRaises(ValueError):run.effective_duration(f,p)

    def test_peak_fluence_bound_with_mixed_pairs(self):
        g,s,T,h=.02,3.,100.,2.
        exact=h*(g+s)**2+(T-h)*g**2
        terms=run.terms(g,s,T,h)
        self.assertAlmostEqual(sum(terms),exact)
        self.assertLess(sum(terms[:2]),exact)

    def test_full38_multiplier_includes_word_length(self):
        W=2**19
        direct=(37/(2*38*W))*(38/32)**2/(31/(2*32*W))
        self.assertAlmostEqual(direct,38*37/(32*31))
        self.assertNotAlmostEqual(direct,38/32)

    def test_point_period_does_not_certify_upper_smu(self):
        self.assertGreater(run.period(3.1e-5,.000155,.245),0)
        self.assertEqual(run.period(.012,.000155,.245),0)

    def test_xor_direct_mark_can_cancel(self):
        before={0}
        mark={0,1}
        self.assertEqual(before.symmetric_difference(mark),{1})
        self.assertEqual(len(mark),2)


class GeometryAndService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merge=staticmethod(run.function_namespace(run.HERE/".cache/legacy/merged.py")["merge_events"])

    @staticmethod
    def event(x,y,a=0):
        return {"xs":np.array([x]),"ys":np.array([y]),"a":np.array([a])}

    def test_merge_uses_l1_not_chebyshev(self):
        # Distance L_inf=4 but L1=8: not merged.
        self.assertEqual(len(self.merge([self.event(1,1),self.event(5,5,1)])),2)

    def test_merge_transitivity_is_not_parent_identification(self):
        events=[self.event(1,1),self.event(1,6,1),self.event(1,11,2)]
        merged=self.merge(events)
        self.assertEqual(len(merged),1)
        self.assertEqual(merged[0]["parts"],3)
        self.assertEqual(int(np.ptp(merged[0]["ys"])),10)

    def test_conditional_write_does_not_implement_U_fence(self):
        err_at_latch=False
        dirty_after_latch=True
        dirty_at_fence=dirty_after_latch if not err_at_latch else False
        self.assertTrue(dirty_at_fence)

    def test_byte_pair_hypotheses_are_distinct(self):
        A=123456
        self.assertEqual(A>>1,(A^1)>>1)
        self.assertNotEqual(A & ((1<<20)-1),(A^1) & ((1<<20)-1))
        self.assertEqual(A & ((1<<20)-1),(A^(1<<20)) & ((1<<20)-1))

    def test_err_read_only_is_lower_bound(self):
        W=2**19
        self.assertAlmostEqual(run.service_bounds(W,0),.02359296)
        self.assertAlmostEqual(run.service_bounds(W,1),.04718592)
        self.assertLess(run.service_bounds(W,0),run.service_bounds(W,.1))

    def test_calendar_span_differs_from_occupancy(self):
        W,a,c=100,1.,.001
        calendar=(W-1)*a/W+c
        busy=W*c
        self.assertGreater(calendar,9*busy)

    def test_peak_bound_small_and_large_window(self):
        self.assertEqual(run.peak_envelope(1e-9,90e-9,1e-6),1.)
        self.assertGreaterEqual(run.peak_envelope(.01,90e-9,1e-6),.09)


class ReproducedInputs(unittest.TestCase):
    def test_six_smu_are_merged_objects(self):
        rows=json.loads((run.OUT/"summary.json").read_text())["clusters"]
        self.assertEqual(rows["HI_grouping_distribution"],{"0":45,"6":10})
        self.assertLess(rows["HI_merged_objects"],rows["HI_registered_clusters"])
        with (run.OUT/"clusters.csv").open() as f:
            counts={r["run"]:int(r["SMU_objects_A0_A1"]) for r in csv.DictReader(f)}
        self.assertEqual({k:v for k,v in counts.items() if v},{"XeLET42":2,"XeLET57":4})

    def test_both_v21_tables_match_printed_precision(self):
        for filename,n in [("v21_comparison.csv",42),("v21_table1_comparison.csv",84)]:
            with (run.OUT/filename).open() as f:rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),n)
            self.assertTrue(all(r["within_printed_rounding"]=="True" for r in rows))

    def test_numerical_reproduction_not_physical_qualification(self):
        summary=json.loads((run.OUT/"summary.json").read_text())
        self.assertLess(summary["numeric"]["v18_frozen_max_relative_difference"],1e-10)
        self.assertFalse(summary["qualification"]["full38_ready"])
        self.assertFalse(summary["qualification"]["full39_ready"])


if __name__=="__main__":unittest.main()
