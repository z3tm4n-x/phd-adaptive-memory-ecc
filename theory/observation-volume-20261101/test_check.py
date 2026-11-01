"""Local checks of the new transfer; no policy/environment search."""
import unittest
from fractions import Fraction as F
import check as c


def pulse_integral(t):
    """Independent primitive: unit triangle on [0,600], repeated every 5400."""
    q, r = divmod(F(t), F(5400))
    if r <= 300:
        part = r*r/600
    elif r <= 600:
        part = 300-(600-r)**2/600
    else:
        part = F(300)
    return q*300+part


class TransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = c.calculate()  # Includes exact replay against the accepted small-bank rows.

    def test_periodic_window_mass_and_old_one_pulse_limit(self):
        for length in map(F, (0, 1, 300, 600, 3701, 5400, 5401, 10800, 29600)):
            bound = c.triangular_mass(length)
            rem = length % 5400
            start = 300-min(rem, F(600))/2
            self.assertEqual(pulse_integral(start+length)-pulse_integral(start),bound)
            for shift in map(F, (-601, -1, 0, 299, 300, 601, 5100, 5400)):
                self.assertLessEqual(pulse_integral(shift+length)-pulse_integral(shift),bound)
        self.assertEqual(c.triangular_mass(F(3701)),300)
        self.assertGreater(c.triangular_mass(F(29600)),300)

    def test_volume_scaling_and_history_control(self):
        a,b=c.Bank(c.W0),c.Bank(8*c.W0)
        for key in ('b','ap','R','g','Fr','B','mass'):
            self.assertEqual(getattr(b,key),8*getattr(a,key))
        self.assertEqual(b.ip,64*a.ip)
        self.assertEqual(b.weak/a.weak,8*b.p/a.p)
        self.assertLess(abs(b.lhi-a.lhi),6*b.bhi)
        self.assertEqual(a.gate_budget,b.gate_budget)
        self.assertEqual(b.gate_budget,F('.0000012708848'))
        self.assertGreater(b.B*b.scan_span_lower*b.mass/b.w,F('.01'))

    def test_no_illegal_one_block_tail_and_price_after_failure(self):
        for bank in self.result['banks']:
            w=bank['geometry']['words']; b=c.Bank(w)
            for row in bank['rows']:
                a=row['adaptive']
                if 'costs' not in a:
                    continue
                self.assertGreater(a['log_score_lower'],a['log_threshold_upper'])
                self.assertLessEqual(a['Q_upper'],row['epsilon'])
                self.assertGreater(a['k_rare'],a['k_base'])
                for k in (a['k_base'],a['k_rare']):
                    end=2; lengths=[2]
                    while end<b.kcell:
                        step=min(k,b.kcell-end); lengths.append(step); end+=step
                    self.assertEqual(end,b.kcell)
                    self.assertGreaterEqual(min(lengths),2)
                    self.assertEqual(len(lengths),b.passes(k))
                self.assertLessEqual(a['main_repairs_upper'],a['main_reads_maximum'])
                self.assertGreater(a['main_reads_maximum'],w*b.n)
                for x,v in a['costs'].items():
                    self.assertIsNone(v['actual_extra_processing'])
                    self.assertEqual(v['V_at_deltaC_design'],v['U0']+v['C_b']*c.DELTAC)
                    self.assertLessEqual(v['strict_full_cost_budget']['schedule'],
                                         v['strict_protection_cost_budget']['schedule'])

    def test_failed_upper_and_independent_lower_resource_exclusion(self):
        large=self.result['banks'][1]
        for row in large['rows'][1:]:
            a=row['adaptive']
            self.assertEqual(a['status'],'E5_UNRESOLVED')
            self.assertNotIn('Q_upper',a)
            self.assertNotIn('costs',a)
            self.assertGreater(a['residual_upper'],row['epsilon'])
        for bank in self.result['banks']:
            for row in bank['rows']:
                member=row['rivals']['constant_member']
                if member is not None:
                    self.assertLessEqual(member['Q_upper'],row['epsilon'])
        last=large['rows'][-1]['rivals']
        self.assertTrue(all(last['excluded_with_inherited_all_slot_contract'].values()))
        self.assertGreater(last['expected_reads_lower']['schedule'],last['all_slot_reads_upper'])
        self.assertFalse(any(large['rows'][1]['rivals']['excluded_with_inherited_all_slot_contract'].values()))


if __name__=='__main__':
    unittest.main()
