from __future__ import annotations
import hashlib, json, os, sys, unittest
from pathlib import Path
import numpy as np, pandas as pd
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from theta_model import candidate_mean_multiplicity, partition_parent_density, partition_from_bridge_endpoints
from boundary_solver import bisect_monotone, monotonicity_violations


def load_json(p):
    with open(p,encoding='utf-8') as f: return json.load(f)

def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

class TestDirectDecisionBoundary(unittest.TestCase):
    def test_01_previous_bridge_full_hashes_when_available(self):
        d=os.getenv('PREVIOUS_BRIDGE_FULL_OUTPUT_DIR')
        if not d: self.skipTest('set PREVIOUS_BRIDGE_FULL_OUTPUT_DIR for integration hash check')
        expected=load_json(HERE/'input_manifest.json')['previous_bridge_full_output_hashes']
        for name,h in expected.items(): self.assertEqual(sha256(Path(d)/name),h)

    def test_02_candidate_mean_identity(self):
        p=np.array([0.0,.1,.4]); km=np.array([1.0,1.25,2.2])
        K=candidate_mean_multiplicity(km,p)
        m=p>0
        self.assertTrue(np.allclose(km[m],(1-p[m])+p[m]*K[m],rtol=0,atol=1e-15))
        self.assertTrue(np.isnan(K[0]))

    def test_03_parent_partition_conservation(self):
        rb=np.array([1e-6,2e-4,.2]);kb=np.array([1.1,1.4,2.0]);p=np.array([.05,.2,.5])
        for th in [0,.03,.37,1]:
            rd,rc,removed=partition_parent_density(rb,kb,p,th)
            self.assertTrue(np.allclose(rb,rc+removed,rtol=1e-14,atol=1e-16))
            self.assertTrue(np.all(rd>=0));self.assertTrue(np.all(rc>=0))

    def test_04_endpoint_reproduction_and_no_double_count(self):
        a0=np.array([1.,2.,3.]);dk=np.array([.1,.2,.3]);ak=np.array([.8,1.7,2.4]);dl=np.array([.15,.3,.5]);al=np.array([.7,1.5,2.0])
        d,a,r=partition_from_bridge_endpoints(a0,dk,ak,dl,al,0,0);self.assertTrue(np.array_equal(d,np.zeros(3)));self.assertTrue(np.array_equal(a,a0))
        d,a,r=partition_from_bridge_endpoints(a0,dk,ak,dl,al,0,1);self.assertTrue(np.allclose(d,dk));self.assertTrue(np.allclose(a,ak))
        d,a,r=partition_from_bridge_endpoints(a0,dk,ak,dl,al,1,1);self.assertTrue(np.allclose(d,dl));self.assertTrue(np.allclose(a,al));self.assertTrue(np.allclose(a+r,a0))

    def test_05_theta_partition_monotone(self):
        a0=np.array([1.,2.]);dk=np.array([.1,.2]);ak=np.array([.8,1.7]);dl=np.array([.2,.4]);al=np.array([.6,1.4])
        ds=[];acs=[]
        for th in np.linspace(0,1,21):
            d,a,_=partition_from_bridge_endpoints(a0,dk,ak,dl,al,th,th);ds.append(d.sum());acs.append(a.sum())
        self.assertEqual(len(monotonicity_violations(ds,1e-15)),0)
        self.assertEqual(len(monotonicity_violations(-np.asarray(acs),1e-15)),0)

    def test_06_synthetic_bisection(self):
        target=.37
        res=bisect_monotone(lambda x:x*x,target*target,tol=1e-6)
        self.assertEqual(res.status,'FINITE');self.assertLess(abs(res.theta-target),1e-6)

    def test_07_exact_scalar_root_validation(self):
        d=pd.read_csv(HERE/'exact_root_validation.csv')
        self.assertLessEqual(float(d.equiv_delta_theta.abs().max()),1e-4)

    def test_08_tolerance_tightening(self):
        d=pd.read_csv(HERE/'tolerance_study.csv')
        # Stable non-near-boundary cases must change by less than the production tolerance.
        stable=d[d.case_label.isin(['median','p90','highest','shield_10'])]
        piv=stable.pivot_table(index='case_label',columns='theta_tolerance',values='theta_root',aggfunc='first')
        for _,r in piv.iterrows(): self.assertLess(abs(r[1e-4]-r[1e-5]),1e-4)

    def test_09_action_transition_exact_ordering(self):
        d=pd.read_csv(HERE/'action_transition_exact_validation.csv')
        self.assertTrue(((d.F_exact_tau_from>=d.epsilon_analysis-1e-10)&(d.F_exact_tau_to<=d.epsilon_analysis+1e-10)).all())

    def test_10_action_transition_order_monotone_full_when_available(self):
        dpath=os.getenv('BOUNDARY_FULL_OUTPUT_DIR')
        if not dpath: self.skipTest('set BOUNDARY_FULL_OUTPUT_DIR for full transition ordering')
        d=pd.read_csv(Path(dpath)/'action_transition_boundaries.csv')
        keys=['shield_mm','window_duration','window_statistic','epsilon_analysis','sigma_model','risk_semantics','low_energy_model']
        for _,g in d.groupby(keys):
            x=g.theta_transition.to_numpy(float)
            self.assertTrue(np.all(np.diff(x)>=-1e-12))

    def test_11_tau_monotonicity_representative(self):
        d=pd.read_csv(HERE/'representative_boundary_curves.csv')
        keys=['shield_mm','window_duration','window_statistic','epsilon_analysis','sigma_model','risk_semantics','low_energy_model','theta']
        for _,g in d.groupby(keys):
            g=g.sort_values('tau_scrub_s'); self.assertTrue(np.all(np.diff(g.F_interpolated.to_numpy(float))>=-1e-10))

    def test_12_invariant_regression(self):
        d=pd.read_csv(HERE/'invariant_regression.csv');self.assertTrue(d['pass'].all())
        keys=['shield_mm','window_duration','window_statistic','epsilon_analysis','sigma_model']
        u=d[keys+['regression_type']].drop_duplicates()
        self.assertGreaterEqual((u.regression_type=='feasible').sum(),10);self.assertGreaterEqual((u.regression_type=='all_infeasible').sum(),10)

    def test_13_both_sigma_and_low_energy_branches_present(self):
        s=load_json(HERE/'boundary_summary.json')
        self.assertEqual(s['K1_only_boundary_summary']['finite_count'],1550)
        self.assertEqual(s['low_energy_conservative_boundary_summary']['finite_count'],1566)
        self.assertGreater(s['sigma_model_boundary_shift_summary']['finite_pairs'],0)

    def test_14_row_order_independence(self):
        rng=np.random.default_rng(7);n=100
        a0=rng.random(n)+1;dk=rng.random(n)*.1;ak=a0-rng.random(n)*.2;dl=dk+rng.random(n)*.05;al=ak-rng.random(n)*.1
        p=rng.permutation(n); inv=np.argsort(p)
        ref=partition_from_bridge_endpoints(a0,dk,ak,dl,al,.3,.7)
        got=partition_from_bridge_endpoints(a0[p],dk[p],ak[p],dl[p],al[p],.3,.7)
        for a,b in zip(ref,got):self.assertTrue(np.allclose(a,b[inv],rtol=0,atol=0))

    def test_15_no_address_refit_and_parity_outside(self):
        i=load_json(HERE/'input_manifest.json');c=load_json(HERE/'boundary_contract.json')
        self.assertFalse(i['address_mapping']['refitted']);self.assertIn('OUTSIDE',c['parity'])

    def test_16_full_output_hash_contract_when_available(self):
        d=os.getenv('BOUNDARY_FULL_OUTPUT_DIR')
        if not d: self.skipTest('set BOUNDARY_FULL_OUTPUT_DIR for full result hash check')
        m=load_json(HERE/'full_output_manifest.json')
        for name,meta in m.items():
            p=Path(d)/name
            if p.exists(): self.assertEqual(sha256(p),meta['sha256'],name)

if __name__=='__main__': unittest.main(verbosity=2)
