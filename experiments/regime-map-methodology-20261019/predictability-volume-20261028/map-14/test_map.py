"""Tests of the new parameter adapter and map bookkeeping, not accepted reruns."""
from fractions import Fraction as F
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import run as m


class MapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=m.load()
        cls.records=m.accepted.numeric(json.loads((m.HERE/'result.json').read_text('utf-8')))['cells']

    def test_fourteen_registered_unique_inputs_and_accepted_not_rerun(self):
        self.assertEqual(len(self.cfg['cells']),14)
        c00=self.cfg['cells'][0]
        with patch.object(m.accepted.Point,'__init__',side_effect=AssertionError('Accepted rerun forbidden')):
            r=m.reuse_accepted(c00)
        self.assertEqual(r['provenance']['kind'],'accepted_reuse_no_rerun')
        self.assertEqual(len(r['executions']),1)
        self.assertEqual(len(r['price_bounds']),1)
        self.assertEqual(r['methods']['Nplus_refined']['alias'],'M')

    def test_parameter_normalization_and_resource_identity(self):
        for cell in self.cfg['cells'][1:]:
            if cell['id'] not in self.records:
                continue
            p=m.GridPoint(cell)
            b,fs,a0=p.b,p.Fs,2*p.Fs/(58440*600)
            a=(1-F(cell['alpha']))*a0
            expected=b*b*315576000+2*b*(1-F(cell['alpha']))*fs+58440*600*a*a/3
            self.assertEqual(p.Ip,expected)
            self.assertEqual(p.K*2*p.D**2,cell['words']*39*38)
            self.assertEqual(p.a,p.a0*(1-F(cell['alpha'])))
            self.assertEqual(p.R+p.a+p.b,p.B)
            self.assertEqual(p.Fr+(1-p.alpha)*p.Fs,p.Fs)
            self.assertEqual(p.resource['words'],p.W)
            self.assertEqual(p.P(1)*10**9,p.resource['calendar']['cycle_upper_ns'])
            self.assertEqual(p.Nmax,p.resource['calendar']['necessary_class_maximum_reads_upper'])
            if p.alpha==0:
                self.assertEqual(len(p.witnesses()),1)
                self.assertEqual(p.Fr,0)

    def test_new_cells_binary_boundaries_and_real_N0_status(self):
        for cell in self.cfg['cells'][1:]:
            if cell['id'] not in self.records:
                continue
            p=m.GridPoint(cell);r=self.records[cell['id']]
            for s in r['menu_generation']:
                k,ratio,f=s['largest_kH'],s['ratio'],s['formula']
                if k is None:
                    self.assertGreater(p.risk(1,ratio,f)['upper'],p.eps)
                else:
                    self.assertLessEqual(p.risk(k,k*ratio,f)['upper'],p.eps)
                    if k<2**32//ratio:
                        self.assertGreater(p.risk(k+1,(k+1)*ratio,f)['upper'],p.eps)
            for name,v in r['methods'].items():
                if 'alias' in v or v.get('pair') is None:
                    continue
                self.assertLessEqual(v['Q_lower'],v['Q_upper'])
                self.assertEqual(v['Q_upper'],p.risk(*v['pair'],v['Q_basis'])['upper'])
                if name!='N0':
                    self.assertLessEqual(v['Q_upper'],p.eps)
                if v['Q_status']=='unresolved':
                    self.assertLessEqual(v['Q_lower'],p.eps)
                    self.assertGreater(v['Q_upper'],p.eps)
                if v['Q_status']=='violates':
                    self.assertGreater(v['Q_lower'],p.eps)

    def test_unavailable_necessary_bound_is_not_zero_optimum(self):
        x=m.lower_for_account({'excluded_from':None})
        self.assertEqual(x['cost']['serial']['lower_s'],0)
        self.assertIn('trivial',x['basis'])
        self.assertFalse(x['class_excluded_by_resource'])
        self.assertIsNone(x['P0_s'])

    def test_deduplication_full_price_and_guard_resource(self):
        for r in self.records.values():
            for v in r['methods'].values():
                if v.get('pair') is None or 'alias' in v:
                    continue
                e=r['executions'][v['execution']]
                p=r['price_bounds'][v['price']]['price']
                self.assertEqual(e['reads_upper'],p['reads_upper'])
                self.assertEqual(e['read_terms_upper'],p['read_terms_upper'])
                self.assertTrue(e['hold_count_fits_prior_34_bits'])
                if e['guarded']:
                    self.assertGreaterEqual(e['H_lower_margin_s'],0)
                if e['constant']:
                    self.assertTrue(e['channel_disabled'])
                    self.assertEqual(e['hold']['ticks'],0)
                for x in ('bus','serial'):
                    c=p['coordinates'][x]
                    self.assertEqual(c['all_known_upper_s'],c['checks_upper_s']+c['repairs_upper_s']+c['app_s']['upper']+c['init_s']['upper'])
                    self.assertGreater(c['app_s']['lower'],0)
                    self.assertGreater(c['init_s']['lower'],0)
                self.assertFalse(p['control_included'])
            res=r['resource']
            self.assertLess(res['resource']['peak_including_full_reserved_management_slot'],res['resource']['serial_cap'])
            self.assertLess(res['application']['inherited_response_envelope_ns'],res['application']['response_deadline_ns'])
            self.assertEqual(res['resource']['available_serial_upper_for_necessary_exclusion'],res['resource']['serial_cap']-res['application']['serial_mission_lower'])

    def test_best_existing_constant_is_not_schedule_advantage(self):
        for r in self.records.values():
            fixed=r['methods']['F_menu'];maxfixed=r['methods']['F_max'];method=r['methods']['M']
            if fixed.get('pair') is None:
                continue
            cf=r['price_bounds'][fixed['price']]['price']['coordinates']['serial']['protection_upper_s']
            cm=r['price_bounds'][maxfixed['price']]['price']['coordinates']['serial']['protection_upper_s']
            self.assertLessEqual(cf,cm)
            if r['executions'][method['execution']]['constant']:
                self.assertEqual(method['execution'],fixed['execution'])
                self.assertEqual(method['price'],fixed['price'])
                gains=r['price_bounds'][method['price']]['comparisons']
                self.assertEqual(gains['serial']['ratio_of_sufficient_uppers'],1)


if __name__=='__main__':
    unittest.main()
