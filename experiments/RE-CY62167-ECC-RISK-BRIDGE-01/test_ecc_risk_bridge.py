from __future__ import annotations
import csv,json,math,sys,unittest
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from ecc_word_model import transient_generator,transient_expm,clean_failure,pair_failure,log_clean_survival
from scrub_model import cyclic_phase_aggregate_multi,aggregate_domain
from risk_bridge import address_xy,dreg_grid,rolling_hazard,run_mc
class T(unittest.TestCase):
 def test_01_generator(self): self.assertTrue(np.allclose(transient_generator(32),[[-32,32],[1,-32]]))
 def test_02_pair(self):
  for mu in (1e-8,1e-7,1e-6): self.assertLess(abs(clean_failure(mu)/pair_failure(mu)-1),3e-5)
 def test_03_expm(self):
  for mu in (1e-5,1e-3,.03): self.assertAlmostEqual(float((np.array([1.,0.])@transient_expm(mu)).sum()),math.exp(log_clean_survival(mu)),places=12)
 def test_04_mapping(self): self.assertEqual(address_xy(0,0),787324)
 def test_05_dreg(self):
  rows=[{'energy_mev':.9,'p_registered_direct_W32seq':0.,'mean_accumulation_bits_per_registered_event':1.1},{'energy_mev':186.,'p_registered_direct_W32seq':0.,'mean_accumulation_bits_per_registered_event':1.4}];p,m=dreg_grid(np.array([.5,.9,10.,186.,300.]),rows);self.assertTrue(np.all(p==0));self.assertTrue(np.all(m>=1))
 def test_06_hazard(self): self.assertTrue(np.allclose(rolling_hazard(np.array([1.,2.,3.]),2),[900.,1500.]))
 def test_07_bounds(self):
  ml,mf,mx,_=cyclic_phase_aggregate_multi(np.full(24,1e-8),[12],60,16)[12];_,prod,upper,lower=aggregate_domain(ml,mf,mx,128);self.assertLessEqual(np.nanmax(prod-upper),1e-12);self.assertLessEqual(np.nanmax(lower-prod),1e-12)
 def test_08_monotonic(self):
  vals=[]
  for tau in (10,30,60,120,300,600):
   ml,mf,mx,_=cyclic_phase_aggregate_multi(np.full(24,2e-7),[12],tau,16)[12];_,prod,_,_=aggregate_domain(ml,mf,mx,512);vals.append(float(prod[0]))
  self.assertTrue(all(b+1e-12>=a for a,b in zip(vals,vals[1:])))
 def test_09_mc(self): self.assertTrue(run_mc(seed=7,trials=3000,Nw=64,T=300,tau=30,lam=.03,p_direct=.02)['below_union_upper'])
 def test_10_registered(self):
  with (HERE/'registered_direct_by_energy.csv').open(newline='',encoding='utf-8-sig') as f:r=list(csv.DictReader(f));self.assertEqual(len(r),14);self.assertEqual(sum(int(x['N_direct_W32seq']) for x in r),0);self.assertEqual(sum(int(x['address_mapping_failures']) for x in r),0)
 def test_11_decision(self):
  v=json.loads((HERE/'validation.json').read_text());self.assertEqual(v['decision_counts']['C_FEASIBILITY_FLIP'],798);self.assertEqual(v['decision_counts']['A_ACTION_INVARIANT_FEASIBLE'],140)
 def test_12_contract(self):
  m=json.loads((HERE/'model_contract.json').read_text());self.assertEqual(m['N_data_bits'],2**24);self.assertEqual(m['N_analysis_words'],2**19);self.assertEqual(m['data_bits_per_word'],32);self.assertEqual(m['correction_capability'],1);self.assertIn('CYCLIC-SEQUENTIAL',m['scrub_semantics'])
if __name__=='__main__':unittest.main(verbosity=2)
