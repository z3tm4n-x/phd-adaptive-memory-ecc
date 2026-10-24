"""Checks for the new volume transfer and certificate-price gate only."""
from fractions import Fraction as F
import unittest
import run as v
import table


class VolumeTests(unittest.TestCase):
    def test_only_volume_fields_change_in_calculation_input(self):
        original, _, _ = v.base.load()
        for kib in [256,128,64]:
            cfg=v.cfg_for(kib)
            self.assertEqual(set(k for k in cfg if cfg[k]!=original[k]),
                             {'words','useful_bytes'})
            self.assertEqual(v.base.cmp.per_bit_moment_caps(cfg),
                             v.base.cmp.per_bit_moment_caps(original))
            self.assertEqual(cfg['words']*4,kib*1024)

    def test_address_and_mandatory_support_are_complete(self):
        result=v.read(v.OUT/'result.json')
        for row in result['rows']:
            W=row['words']
            for trial in row['adaptive_rows']:
                k=trial['k']; inverse=pow(k,-1,W)
                self.assertEqual(len({inverse*j%W for j in range(W)}),W)
                self.assertEqual([(inverse*k*j)%W for j in range(W)],list(range(W)))
                c=v.base.info.calendar(v.cfg_for(row['kib']),k)
                self.assertGreaterEqual(c['zero_union_slack'],0)
                self.assertGreater(c['w'],c['tau'])
                self.assertGreaterEqual(c['recovery']['lower'],c['h_upper']+c['tau'])

    def test_plateau_and_single_word_law_preserved(self):
        reference=v.cfg_for(512); e=reference['environment']
        lam=F(39)*F(e['reference_peak_per_s'])/(e['reference_words']*e['reference_bits'])
        L=F(e['reference_solar_mass'])/(F(e['reference_peak_per_s'])-F(e['reference_background_per_s']))
        for kib in [256,128,64]:
            cfg=v.cfg_for(kib); ee=cfg['environment']
            self.assertEqual(F(39)*F(ee['reference_peak_per_s'])/(ee['reference_words']*ee['reference_bits']),lam)
            bounds=v.base.class_threshold(cfg)
            low,high=bounds['last_not_excluded'],bounds['excluded_from']
            self.assertEqual(high['plateau_s'],L)
            self.assertGreater(high['free_length_lower'],0)
            self.assertGreater(high['Q_lower'],F(cfg['epsilon']))
            self.assertLessEqual(low['Q_lower'],F(cfg['epsilon']))
            self.assertEqual(high['P0']-low['P0'],F(1,10**6))

    def test_floor_bounds_both_price_branches_even_at_minimum_U(self):
        for kib in [512,256,128,64]:
            cfg=v.cfg_for(kib); gate=v.price_gate(cfg)
            kf=v.base.fixed(cfg,39,1)['k']
            for k in {1,v.odd_at_least(kf),2*kf+1,4*kf+1}:
                cal=v.base.info.calendar(cfg,k)
                U=F(cfg['lifetime_other_budget'])
                # Test at the algebraic minimum U, not a claimed risk certificate.
                price=v.base.price(cfg,39,k,U,cal)
                self.assertLessEqual(gate['certificate_bus_floor'],price['pure_bus_upper'])
                old=v.base.cmp.cost_result(cfg,39,1,k,U,True,cal)
                Nfloor=sum(gate['terms'].values(),F(0))
                self.assertLessEqual(Nfloor,old['read_count_upper'])
                self.assertLessEqual(Nfloor,sum(price['read_count_terms'].values(),F(0)))
            self.assertTrue(gate['NOT_a_lower_bound_on_real_cost'])

    def test_new_phase_certificates_and_array_scale(self):
        files=list(v.OUT.glob('certificate-*KiB-*.json'))
        self.assertGreaterEqual(len(files),1)
        for file in files:
            cert=v.read(file); p=cert['environment']; W=p['W']
            cfg=v.cfg_for(W*4//1024); e=cfg['environment']
            factor=F(39*W,e['reference_words']*e['reference_bits'])
            for key,source in [('b','reference_background_per_s'),('B','reference_peak_per_s'),
                               ('FS','reference_solar_mass'),('ell','reference_growth_threshold_per_s')]:
                self.assertEqual(p[key],factor*F(e[source]))
            ma=cert['majorant']; last=p['b']
            for cell in ma['cells']:
                self.assertEqual(last,cell['lo'])
                self.assertGreater(cell['hi'],cell['lo'])
                for x in [cell['lo'],cell['hi']]:
                    self.assertGreaterEqual(ma['u']+ma['v']*(x-p['b'])-cell['K_upper']*x*x,0)
                last=cell['hi']
            self.assertEqual(last,p['B'])
            self.assertEqual(sum(cert['risk']['terms'].values()),cert['risk']['upper'])
            self.assertEqual(cert['risk']['coupling_beta'],F(1,2*W))

    def test_partial_bank_budget_is_not_a_whole_memory_claim(self):
        result=v.read(v.OUT/'result.json')
        for row in result['rows']:
            self.assertEqual(row['epsilon'],F(1,1000))
            self.assertEqual(row['delta_common'],F(6,10**6))
            self.assertIsNone(row['whole_reference_memory_Q'])
            self.assertEqual(row['application_write_rate'],0)
            self.assertGreater(row['application_read_rate'],0)
            selected=next(r for r in row['adaptive_rows'] if r['k']==row['selected_k'])
            self.assertLessEqual(selected['Q_upper'],row['epsilon'])
            self.assertTrue(selected['price']['after_A_paid'])
            self.assertTrue(selected['price']['tail_paid'])
            self.assertIsNone(row['comparison']['fixed_extra_control_upper'])
            self.assertEqual(row['price_gate']['activated'],row['kib'] in (64,128))
        self.assertIsNone(result['interpolated_boundary'])

    def test_displayed_bounds_are_directed_including_negative_gaps(self):
        result=v.read(v.OUT/'result.json')
        for row in result['rows']:
            c=row['comparison']
            for key,upper in [('adaptive_bus_upper',True),('fixed_witness_bus_upper',True),
                              ('fixed_class_bus_lower',False),('control_bus_sufficient_strict_below',False)]:
                value=100*c[key]
                printed=F(table.directed(value,6,upper))
                error=printed-value if upper else value-printed
                self.assertGreaterEqual(error,0)
                self.assertLess(error,F(1,10**6))


if __name__=='__main__':
    unittest.main()
