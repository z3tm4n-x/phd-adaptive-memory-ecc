"""New-scope regressions and counterexamples, not a repeat of accepted Q tests."""
from fractions import Fraction as F
import json
import unittest
import calculate as c


class ScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.accepted,_=c.load()

    def test_fixed_budget_is_not_halved_silently(self):
        full=c.fixed(self.cfg,39,1)
        half=c.fixed(self.cfg,39,1,2)
        self.assertGreater(full['k'],half['k'])
        self.assertLessEqual(full['risk']['upper'],F(self.cfg['epsilon']))
        self.assertGreater(full['next_upper'],F(self.cfg['epsilon']))

    def test_old_k27_protection_account_preserved(self):
        cert=self.accepted['informational']
        U=max(cert['risk']['upper'],self.accepted['accepted_risk_upper_retained_in_price'])
        value=c.price(self.cfg,39,27,U,cert['calendar'])
        self.assertEqual(value['core_upper'],self.accepted['ERR_price']['added_control_core_upper'])
        for key in ('false','startup_and_recovery','loss','weak_E_repeat','bad'):
            self.assertGreater(value['read_count_terms'][key],0)
        self.assertGreater(value['extra_veto_core_slope'],0)
        self.assertIsNone(value['CPU_value'])
        self.assertIsNone(value['energy_value'])

    def test_geometry_all_phases_and_long_tail(self):
        length=F(53); d=F(1); P0=F(7)
        M=length/P0+2
        bound=(length-M*d)**2/(M+1)
        for P in (F(7),F(8),F(14),F(100),F(10000)):
            for phase in (F(0),F(1,2),P/2,P-F(1,2)):
                windows=[]
                for j in range(-1,int(length/P)+2):
                    a=max(F(0),phase+j*P); b=min(length,phase+j*P+d)
                    if b>a:
                        windows.append((a,b))
                pos=F(0); gaps=[]
                for a,b in sorted(windows):
                    if a>pos:gaps.append(a-pos)
                    pos=max(pos,b)
                if pos<length:gaps.append(length-pos)
                self.assertLessEqual(len(windows),M)
                self.assertGreaterEqual(sum(x*x for x in gaps),bound)

    def test_witness_is_in_declared_class(self):
        row=c.fixed_class_lower(self.cfg,F(1))
        e=self.cfg['environment']
        self.assertEqual(row['plateau_s']*(F(e['reference_peak_per_s'])-F(e['reference_background_per_s'])),F(e['reference_solar_mass']))
        self.assertLess(row['plateau_s'],F(self.cfg['mission_s']))
        self.assertGreater(row['free_length_lower'],0)
        self.assertLess(row['Q_lower'],row['Q_upper_numeric_enclosure'])

    def test_threshold_strictly_excludes_whole_tail(self):
        row=c.class_threshold(self.cfg)
        low,high=row['last_not_excluded'],row['excluded_from']
        self.assertEqual(high['P0']-low['P0'],F(1,10**6))
        self.assertLessEqual(low['Q_lower'],F(self.cfg['epsilon']))
        self.assertGreater(high['Q_lower'],F(self.cfg['epsilon']))
        for P in (high['P0']*2,F(100),F(self.cfg['mission_s'])):
            self.assertGreaterEqual(c.fixed_class_lower(self.cfg,P)['Q_lower'],high['Q_lower'])

    def test_useful_writes_are_not_needed_for_upper_Q_formula(self):
        from copy import deepcopy
        cfg=deepcopy(self.cfg)
        # This regression confirms the previously stated mandatory-only scope.
        cfg['application']['epoch_ns']*=10**9
        before=c.fixed(self.cfg,39,1)
        after=c.fixed(cfg,39,1)
        self.assertEqual(before['risk'],after['risk'])

    def test_new_certificates_cover_whole_intensity_interval(self):
        for k in (53,107):
            cert=c.numeric(json.loads((c.OUT/f'certificate-k{k}.json').read_text('utf-8')))
            ma,p=cert['majorant'],cert['environment']
            cells=ma['cells'];last=p['b']
            for cell in cells:
                self.assertEqual(cell['lo'],last)
                self.assertGreater(cell['hi'],cell['lo'])
                for point,key in ((cell['lo'],'left_slack'),(cell['hi'],'right_slack')):
                    slack=ma['u']+ma['v']*(point-p['b'])-cell['K_upper']*point*point
                    self.assertEqual(slack,cell[key])
                    self.assertGreaterEqual(slack,0)
                last=cell['hi']
            self.assertEqual(last,p['B'])
            self.assertEqual(sum(cert['risk']['terms'].values()),cert['risk']['upper'])
            self.assertEqual(cert['selected_target'],F(self.cfg['epsilon'])/2)
            # The retained legacy half-budget flag is not the new decision.
            self.assertEqual(cert['risk']['upper']<=F(self.cfg['epsilon']),k==53)


if __name__=='__main__':
    unittest.main()
