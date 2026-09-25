import json
import math
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations
import unittest

import numpy as np
from scipy.linalg import expm

from audit import ROOT, calculations, reduced_generator
from independent_check import enumerate_survival


class InputChecks(unittest.TestCase):
    def test_literal_rows(self):
        raw = json.loads((ROOT/'source_rows.json').read_text(encoding='utf-8'))
        self.assertEqual(len(raw['ISSI_32Mbit']),20)
        self.assertEqual(len(raw['Renesas_8Mbit']),23)
        selected = [r for r in raw['Renesas_8Mbit'] if r[0]=='RADEF' and r[1]==13.3]
        self.assertEqual(selected,[['RADEF',13.3,7000000,1199,0,2e-11]])

    def test_normalization_not_silently_repaired(self):
        rows=calculations()['normalization']
        self.assertTrue(all(1.85 < r['nominal_to_full_capacity_ratio'] < 2.15 for r in rows['ISSI_32Mbit']))
        self.assertTrue(all(.9 < r['nominal_to_full_capacity_ratio'] < 1.1 for r in rows['Renesas_8Mbit'] if r['SBU']))

    def test_full_word_rate_independent_rational(self):
        a=calculations()['candidate']
        expected=Fraction(1199,7000000)*Fraction(39,16)*1000
        self.assertAlmostEqual(a['nominal_protected_SBU_exposure_rate_s_minus1'], float(expected),14)
        self.assertEqual(a['physical_bits']-a['protected_bits'],9*524288)
        self.assertNotAlmostEqual(float(expected*Fraction(32,39)),float(expected),8)  # data-only mutant

    def test_zero_is_not_zero_upper_independent_decimal(self):
        a=calculations()['optimistic_complete_detection_diagnostic']
        with localcontext() as ctx:
            ctx.prec=50
            upper=-(Decimal(1)/20).ln()/Decimal(7000000)
            hazard=upper*3*1000*3600
            probability=1-(-hazard).exp()
        self.assertAlmostEqual(a['per_device_group_cross_section_upper_cm2'],float(upper),18)
        self.assertAlmostEqual(a['Poisson_at_least_one_upper'],float(probability),14)
        self.assertGreater(float(probability),.1)
        self.assertGreater(float(upper),0)  # zero-MBU => zero-probability mutant rejected
        self.assertFalse(a['is_validated_physical_bound'])

    def test_word_marginals_identical_but_joint_different(self):
        W=4
        for size in (1,2):
            marks=list(combinations(range(W),size))
            rates=[Fraction(sum(w in m for m in marks),len(marks)*size) for w in range(W)]
            self.assertEqual(rates,[Fraction(1,W)]*W)
        a=calculations()['joint_mark_nonidentification_witness']
        self.assertEqual(a['1']['per_word_arrival_mean'],a['2']['per_word_arrival_mean'])
        self.assertNotAlmostEqual(a['1']['F_first_cap'],a['2']['F_first_cap'],8)

    def test_generators_against_independent_bit_oracle(self):
        for W,n in [(2,2),(3,2),(3,3)]:
            for g in (1,2):
                for t in (0, .2, 1, 3):
                    q=reduced_generator(W,n,2,g)
                    self.assertTrue(np.allclose(q.sum(axis=1),0,atol=1e-14))
                    actual=1-expm(q*t)[0,-1]
                    expected,tail=enumerate_survival(W,n,2,t,g)
                    self.assertLess(abs(actual-expected),tail+2e-13)

    def test_marginal_only_mutant_rejected(self):
        # Wrongly feed group-size=1 to the production reduced solver while
        # preserving every per-word rate of the two-word physical generator.
        wrong=1-expm(reduced_generator(3,3,2,1))[0,-1]
        oracle,_=enumerate_survival(3,3,2,1,2)
        self.assertGreater(abs(wrong-oracle),.001)

    def test_limits(self):
        for g in (1,2):
            self.assertEqual(expm(reduced_generator(4,39,0,g))[0,-1],0)
            self.assertEqual(expm(reduced_generator(4,39,2,g)*0)[0,-1],0)
        with self.assertRaises(ValueError):
            reduced_generator(1,39,2,2)


if __name__=='__main__':
    unittest.main(verbosity=2)
