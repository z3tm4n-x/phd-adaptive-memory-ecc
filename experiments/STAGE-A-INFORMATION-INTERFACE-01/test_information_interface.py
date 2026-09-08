#!/usr/bin/env python3
import csv, json, os, tempfile, unittest
from fractions import Fraction as R
from pathlib import Path
import information_interface as ii

HERE=Path(__file__).resolve().parent
STAGE=Path(os.environ.get("STAGE_A_DIR",HERE.parent/"STAGE-A-IMPLEMENTATION-01"))

class InformationInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.out=Path(cls.tmp.name)
        cls.summary=ii.run(STAGE,cls.out)
        with (cls.out/"resource_summary.csv").open(newline="",encoding="utf-8") as h:
            cls.rows=list(csv.DictReader(h))
        with (cls.out/"policy_region_map.csv").open(newline="",encoding="utf-8") as h:
            cls.detail=list(csv.DictReader(h))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_01_six_timing_classes_are_exhaustive(self):
        self.assertEqual([x[0] for x in ii.TIMING_CLASSES],
                         ["T000","T001","T010","T011","T110","T111"])
        self.assertEqual(len({x[1:] for x in ii.TIMING_CLASSES}),6)
        self.assertTrue(all(not a0 or a1 for _,a0,a1,a2 in ii.TIMING_CLASSES))

    def test_02_aligned_latency_boundaries(self):
        self.assertEqual(ii.availability(0,300,0,True,True),"T111")
        self.assertEqual(ii.availability(0,300,R(1,10**9),True,True),"T010")
        self.assertEqual(ii.availability(0,300,300,True,True),"T010")
        self.assertEqual(ii.availability(0,300,R(300)+R(1,10**9),True,True),"T000")

    def test_03_timestamp_equality_and_missing_update_boundaries(self):
        # First report delivered exactly at t=300 is available before decision.
        self.assertEqual(ii.availability(100,400,200,True,False),"T010")
        self.assertEqual(ii.availability(1,300,0,True,True),"T011")
        self.assertEqual(ii.availability(0,400,0,True,False),"T110")
        self.assertEqual(ii.availability(100,300,0,False,True),"T001")

    def test_04_eta_half_is_ambiguous_boundary(self):
        self.assertEqual(ii.eta_class(0),"E_EXACT")
        self.assertEqual(ii.eta_class(R(1,2)-R(1,10**9)),"E_EXACT")
        self.assertEqual(ii.eta_class(R(1,2)),"E_AMBIG")
        self.assertEqual(ii.eta_class(2),"E_AMBIG")
        self.assertEqual(ii.allowed_report_sets("L",True),("L","A"))

    def test_05_exact_ideal_endpoint_recovery(self):
        z=[r for r in self.rows if r["region_id"]=="T111_E_EXACT"]
        self.assertTrue(z)
        self.assertTrue(all(r["ideal_action_implementable"]=="1" for r in z))
        self.assertTrue(all(r["selection_matches_ideal"]=="1" for r in z))
        self.assertTrue(all(r["retention"] in ("1","NA") for r in z))

    def test_06_no_information_endpoint_recovery(self):
        z=[r for r in self.rows if r["region_id"]=="T000_E_EXACT"]
        self.assertTrue(z)
        self.assertTrue(all(r["policy_equals_precomputed_all_reports"]=="1" for r in z))
        self.assertTrue(all(r["guaranteed_cost_equals_precomputed"]=="1" for r in z))

    def test_07_eta_ambiguous_guaranteed_collapse(self):
        z=[r for r in self.rows if r["eta_class"]=="E_AMBIG"]
        self.assertTrue(z)
        self.assertTrue(all(r["guaranteed_cost_equals_precomputed"]=="1" for r in z))

    def test_08_class_inclusion_cost_order(self):
        for r in self.rows:
            p=int(r["precomputed_passes"]); i=int(r["ideal_passes"])
            d=int(r["imperfect_worst_report_passes"])
            self.assertLessEqual(i,d)
            self.assertLessEqual(d,p)

    def test_09_selected_rows_are_certified_with_whole_window_Q(self):
        # Q values come from the reused Stage-A production certificate.
        for r in self.detail:
            self.assertGreaterEqual(float(r["certificate_margin"]),-1e-18)

    def test_10_resource_identities(self):
        P=R("0.18874368")
        for r in self.detail:
            p=int(r["passes"])
            self.assertEqual(int(r["reads"]),p*2**21)
            self.assertEqual(int(r["writes"]),p*2**21)
            self.assertAlmostEqual(float(r["occupied_s"]),float(P*p),places=11)
            self.assertAlmostEqual(float(r["occupied_fraction"]),float(P*p/R(600)),places=12)

if __name__=="__main__":
    unittest.main(verbosity=2)
