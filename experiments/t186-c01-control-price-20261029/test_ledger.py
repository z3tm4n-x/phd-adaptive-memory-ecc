"""Targeted accounting/unit/unknown tests; no accepted simulation campaign."""
from fractions import Fraction as F
from decimal import Decimal, localcontext
import json
import unittest

import reproduce as m


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = m.calculate()
        cls.rows = cls.r['ledger']
        cls.by_id = {r['id']: r for r in cls.rows}

    def test_no_unknown_becomes_zero(self):
        for x in ('bus', 'serial'):
            c = self.r['coordinates'][x]
            self.assertEqual(c['verdict']['status'], 'not_established')
            self.assertIsNone(c['actual_control_upper_s'])
            self.assertIsNone(c['verdict']['upper_us_per_s'])
            for row in self.rows:
                self.assertIsNone(row['coefficient_'+x])
        self.assertIsNone(self.r['ERR_scope']['actual_export_disabled'])
        for key in ('actual_CPU_upper','actual_energy_upper','actual_M_WCET','actual_M_state_bytes'):
            self.assertIsNone(self.r['resource_conditions'][key])

    def test_accepted_common_data_price_not_charged_again(self):
        self.assertEqual(set(self.by_id), {'check','command','timer','extra_bundle',
            'slot','dispatch','ERR','state_rate','state_edges'})
        for x, c in self.r['coordinates'].items():
            paid = self.r['already_paid'][x]
            self.assertEqual(paid['all_known_upper_s'], paid['checks_upper_s']+
                paid['repairs_upper_s']+paid['app_s']['upper']+paid['init_s']['upper'])
            self.assertEqual(c['accepted_margin_s'],
                c['fixed_class_known_lower_s']-c['accepted_M_known_upper_s'])
            self.assertLess(c['conservative_strict_budget_s'], c['accepted_margin_s'])
        self.assertTrue(self.r['costs_uniform_after_first_failure'])
        self.assertFalse(self.r['accepted_calculations_rerun'])

    def test_full_slot_count_edges_and_ERR_cap(self):
        cfg = m.numeric(json.loads((m.MAP/'inputs.json').read_text('utf-8')))
        T,W=self.r['mission_s'],self.r['words']
        svc=cfg['service']
        pminus=196*W*svc['xi_minus']/10**9-svc['J_ns']/10**9
        self.assertEqual(self.r['counts']['slot'], W*(T/pminus+2))
        self.assertGreater(self.r['counts']['slot'], 100*self.r['reads_upper'])
        self.assertEqual(self.r['counts']['ERR'], self.r['reads_upper'])
        self.assertGreaterEqual(self.r['counts']['ERR'], self.r['repairs_upper'])
        self.assertEqual(self.r['counts']['dispatch'],self.r['reads_upper']+315569688607+W)
        P=self.r['counts']['check']; R=self.r['calendar_recoveries_upper']
        self.assertEqual(self.r['counts']['command'],P+R+1)
        self.assertEqual(self.r['counts']['timer'],P+2*R+2)
        self.assertTrue(self.r['ERR_scope']['expected_count_not_burst'])

    def test_units_and_ceilings_with_independent_decimal(self):
        def d(x):
            x=F(x)
            return Decimal(x.numerator)/Decimal(x.denominator)
        with localcontext() as ctx:
            ctx.prec=70
            for x,c in self.r['coordinates'].items():
                B=d(c['conservative_strict_budget_us_per_s'])
                for row in self.rows:
                    direct=d(row['count_upper'])*d(row['coefficient_seconds_scale'])*1000000/d(self.r['mission_s'])
                    self.assertLess(abs(d(row['mean_multiplier'])-direct),Decimal('1e-60'))
                    limit=c['sole_term_coefficient_ceilings'][row['id']]
                    self.assertLess(abs(d(limit)*direct-B),Decimal('1e-60'))
                    self.assertLessEqual(F(m.display(limit,12)),limit)
                    self.assertGreaterEqual(F(m.display(row['mean_multiplier'],12,True)),row['mean_multiplier'])

    def test_joint_strict_boundary_not_four_independent_budgets(self):
        # Synthetic unit-cost fixture only; never assigned to the actual M.
        for x,c in self.r['coordinates'].items():
            B=c['conservative_strict_budget_us_per_s']
            vals={r['id']:F(0) for r in self.rows}
            vals['slot']=c['sole_term_coefficient_ceilings']['slot']
            self.assertEqual(m.evaluate(self.rows,vals,B)['status'],'not_met_by_this_upper')
            vals['slot']-=F(1,10**12)
            self.assertEqual(m.evaluate(self.rows,vals,B)['status'],'condition_met')
            vals['state_rate']=F(1,1000)
            self.assertEqual(m.evaluate(self.rows,vals,B)['status'],'not_met_by_this_upper')
            vals['ERR']=None
            self.assertEqual(m.evaluate(self.rows,vals,B)['status'],'not_established')


if __name__=='__main__':
    unittest.main()
