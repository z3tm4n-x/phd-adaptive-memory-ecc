import importlib.util
import math
import unittest
from fractions import Fraction as F
from pathlib import Path
from advance_budget import calculate

class AdvanceTests(unittest.TestCase):
    def test_reference_history(self):
        path=Path(__file__).resolve().parent.parent/'t104-rtl-resume/integrated/bounds.py'
        spec=importlib.util.spec_from_file_location('accepted_history',path)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        self.assertEqual(calculate()['history_ns'],mod.calculate()['history']['processed_history_ns'])

    def test_independent_rational_endpoints(self):
        r=calculate();b=r['joint_B_limit_ns']
        # Independent arithmetic, NOT float tolerance at a safety boundary.
        h=(4500045002-1)*F(199998,10000)-F(1,2)
        fixed=F('80.5008')+F('36.50036')+F('531869457677237/102498975000')+F('20.5002')+F('600.506')
        self.assertEqual(2*b+fixed,h)
        self.assertGreater(2*(b+F(1,1000))+fixed,h)
        self.assertLess(b+F('531869457677237/102498975000')+2*F('20.5002'),
                        F(22500225010)*F('3.99996')-F('.5'))
        self.assertLess(math.ceil((b+F('.5'))/F('19.9998'))+2,2**32-1)

    def test_different_deadlines_not_renaming(self):
        r=calculate();diagnostic_B=10**6
        self.assertGreater(diagnostic_B,r['old_literal_fresh_history_B_limit_ns'])
        self.assertLess(diagnostic_B,r['joint_B_limit_ns'])
        self.assertFalse(r['literal_processed_G_10us_implied'])
        self.assertIsNone(r['new_physical_ARM_upper_ns'])

    def test_tail_and_margin(self):
        r=calculate()
        self.assertLess(r['derived_link_with_refresh_ns'],r['certificate_allocation_ns'])
        self.assertLess(r['certificate_10pct_ns'],1000)
        self.assertLess(r['non_hold_tail_including_history_ns'],10000)
        self.assertEqual(r['non_hold_tail_including_history_ns']+r['remaining_to_10us_ns'],10000)
        self.assertFalse(r['Q_recalculated'])
        self.assertEqual(r['historical_published_B_limit_ns']-r['old_literal_fresh_history_B_limit_ns'],
                         F('36.50036')/2)

    def test_selected_millisecond_round(self):
        r=calculate()
        self.assertEqual(r['selected_service_allocation_ns'],1000000)
        self.assertEqual(r['selected_max_nominal_slow_ticks'],49999)
        self.assertEqual(r['selected_collector_count_upper'],50003)
        self.assertGreater(r['selected_preparation_margin_ns'],F('89.99')*10**9)
        self.assertLess(49999*20*F('1.00001')+F('.5'),1000000)
        self.assertGreater(50000*20*F('1.00001')+F('.5'),1000000)
        self.assertFalse(r['selected_service_is_WCET'])

if __name__=='__main__':unittest.main()
