from fractions import Fraction as F
import json
import unittest

import engine as e


class T88(unittest.TestCase):
    def test_active_quotas(self):
        p=e.context('3','combined')
        for mode,n in [('combined',6),('monitor-only',5),('ERR-only',4)]:
            self.assertEqual(e.old.errors(p['q'],mode),n*F('1e-6'))
        self.assertEqual(e.fixed(p,e.DMIN)['quota_upper'],F('3e-6'))

    def test_inputs_unchanged_and_fullword(self):
        for s in ('3','2.5'):
            p=e.context(s,'combined')
            self.assertEqual((p['W'],p['n'],p['c'],p['g']),(524288,38,100,131))
            self.assertEqual(p['margin'],F('.1'))
            self.assertEqual(p['Dstar'],e.DMIN)
            self.assertEqual(p['FS'],115776*(p['B']-p['b']))

    def test_resource_and_short_cap(self):
        for s in ('3','2.5'):
            for mode in e.CFG['modes']:
                p=e.context(s,mode);cap,slope=e.g_cap(p)
                self.assertTrue(e.calendar(p,131)['resource_pass'])
                self.assertFalse(e.calendar(p,130)['resource_pass'])
                self.assertLessEqual(e.DMIN+e.old.errors(p['q'],mode)+cap*slope,p['eps'])
                self.assertGreater(e.DMIN+e.old.errors(p['q'],mode)+(cap+1)*slope,p['eps'])

    def test_baseline_monitor_rows(self):
        pilot=json.loads((e.HERE/'outputs/pilot.json').read_text())
        for record in pilot['rows']:
            if record['mode']=='ERR-only':continue
            p=e.calendar(e.context(record['shield'],record['mode']),131)
            b=record['result'];r=e.evaluate(p,b)
            for key in ('risk_upper','quiet_upper','returns_upper','objective'):
                self.assertEqual(r[key],F(b[key]))

    def test_ERR_formula_9_and_affine_prices(self):
        pilot=json.loads((e.HERE/'outputs/pilot.json').read_text())
        for record in pilot['rows']:
            if record['mode']!='ERR-only':continue
            p=e.calendar(e.context(record['shield'],'ERR-only'),131)
            spec=record['result'];r=e.evaluate(p,spec)
            self.assertEqual(r['risk_upper'],F(spec['risk_upper']))
            w=e.pack(p,r)
            for d in (e.DMIN,(e.DMIN+w['D_cert'])/2,w['D_cert']):
                new=e.evaluate(p,spec,d)
                self.assertEqual(e.cost_at(w,d),(new['quiet_upper'],new['returns_upper'],new['objective']))
                self.assertEqual(new['risk_upper']-r['risk_upper'],d-e.DMIN)

    def test_monitor_affine_D_and_price_limit(self):
        for mode in ('combined','monitor-only'):
            p=e.calendar(e.context('3',mode),150)
            m=e.window(p)
            r=e.j.best_direct(p,m);w=e.pack(p,r)
            for d in (e.DMIN,(e.DMIN+w['D_cert'])/2,w['D_cert']):
                new=e.evaluate(p,w['spec'],d)
                self.assertEqual(e.cost_at(w,d),(new['quiet_upper'],new['returns_upper'],new['objective']))
                self.assertEqual(new['risk_upper']-r['risk_upper'],d-e.DMIN)
            if w['D_cost']>=e.DMIN:self.assertLessEqual(e.cost_at(w,w['D_cost'])[2],e.LIMIT)

    def test_fixed_M_next_and_no_monitor_cost(self):
        from run_t80 import fixed_row
        for s in ('3','2.5'):
            p=e.context(s,'combined');old=fixed_row(p);r=e.fixed(p,e.DMIN)
            self.assertEqual(r['M'],old['fixed_strong_M'])
            self.assertEqual(r['risk_upper'],old['fixed_risk_upper'])
            self.assertEqual(r['cost_lower'],old['fixed_cost_lower'])
            for d in (e.DMIN,F('.0002'),F('.0005'),F('.000996'),F('.000997')):
                r=e.fixed(p,d)
                self.assertEqual(r['monitor_cost'],0)
                if r['M']:
                    self.assertLessEqual(r['risk_upper'],p['eps'])
                    self.assertGreater(r['next_risk_upper'],p['eps'])

    def test_safe_bracket_and_empty_not_zero(self):
        self.assertIsNone(e.bracket(e.DMIN-e.TOL))
        br=e.bracket(e.DMIN+e.TOL/F(3))
        self.assertLessEqual(br['lower'],br['exact_family_bound'])
        self.assertGreaterEqual(br['upper'],br['exact_family_bound'])
        self.assertLessEqual(br['width'],e.TOL)

    def test_same_class_necessary_boundary_separate(self):
        for s in ('3','2.5'):
            r=e.necessary_constant(e.context(s,'combined'))
            self.assertGreater(r['risk_lower'],F('.001'))
            self.assertIsNone(r['physical_occupied_lower_s'])

    def test_pareto_pruning_preserves_two_prices_and_D_limits(self):
        from collections import Counter
        p=e.calendar(e.context('2.5','monitor-only'),131)
        candidates=[e.pack(p,r) for r in e.monitor_family(p,Counter()) if r['ka']>1]
        front=[]
        for w in candidates:e.frontier_add(front,w)
        for d in (e.DMIN,F('.00006'),F('.00008'),F('.0001')):
            raw=e.best_at(candidates,d);pruned=e.best_at(front,d)
            self.assertEqual(raw is None,pruned is None)
            if raw:self.assertEqual(e.cost_at(raw,d),e.cost_at(pruned,d))
        self.assertEqual(max(w['D_cert'] for w in candidates),max(w['D_cert'] for w in front))
        self.assertEqual(max(w['D_cost'] for w in candidates),max(w['D_cost'] for w in front))

    def test_feasible_set_shrinks_no_D_optimization(self):
        p=e.calendar(e.context('3','monitor-only'),160)
        w=e.pack(p,e.j.best_direct(p,e.window(p)))
        for d in (e.DMIN,w['D_cert']):
            self.assertIsNotNone(e.best_at([w],d))
            r=e.evaluate(p,w['spec'],d)
            self.assertEqual(r['Dstar'],d)
            self.assertEqual(r['risk_upper'],d+w['risk_intercept'])
        self.assertIsNone(e.best_at([w],w['D_cert']+e.TOL))

    def test_margins_covariates_and_odd_word_map(self):
        for g in (131,180,279):
            p=e.calendar(e.context('3','combined'),g);m=e.window(p)
            self.assertGreaterEqual(m['hF_min'],(1+p['margin'])*m['hF_required'])
            self.assertGreaterEqual(m['dmin'],(1+p['margin'])*F(1))
            self.assertEqual(m['J'],631158312)
            self.assertEqual(m['H'],35)
            for ka in (1,3,129,4095):self.assertEqual((pow(ka,-1,p['W'])*ka)%p['W'],1)


if __name__=='__main__':unittest.main()
