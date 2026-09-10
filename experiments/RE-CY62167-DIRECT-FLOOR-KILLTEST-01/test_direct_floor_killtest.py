#!/usr/bin/env python3
import tempfile, unittest
from pathlib import Path
import numpy as np

from direct_floor_killtest import (
    LOW_SCENARIOS, MULTIPLICITY_VARIANTS, load_multiplicity_points,
    low_conservative_probability, multiplicity_on_grid, nhpp_floor,
    max_contiguous_hazard,
)

MULT = '''energy_mev,source_file,N_events,N_bitflips,max_K,multiplicity_counts,P_K,scope
0.9,a,1000,1010,2,"{""1"":990,""2"":10}","{}",x
1.0,b,1000,1005,2,"{""1"":995,""2"":5}","{}",x
3.0,c,1000,1020,2,"{""1"":980,""2"":20}","{}",x
5.0,d,1000,1030,2,"{""1"":970,""2"":30}","{}",x
186.0,e,1000,1300,3,"{""1"":800,""2"":100,""3"":100}","{}",x
'''
FALSE = '''energy_mev,segment_id,N1,N2_observed,N_bitflips,false_N2_MD3_pooled,false_N2_IND3_pooled,false_N2_MD3_temporal,false_N2_IND3_temporal,false_N3_MD3_lo,false_N3_MD3_hi,false_N3_IND3_lo,false_N3_IND3_hi,temporal_status
0.9,1,990,10,1010,0,0,1,2,0,0,0,0,x
1.0,1,995,5,1005,0,0,1,1,0,0,0,0,x
3.0,1,980,20,1020,0,0,1,4,0,0,0,0,x
5.0,1,970,30,1030,0,0,1,3,0,0,0,0,x
186.0,1,800,100,1300,0,0,1,10,0,0,0,0,x
'''

class KillTestUnitTests(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); root=Path(self.td.name)
        self.m=root/'m.csv'; self.f=root/'f.csv'; self.m.write_text(MULT); self.f.write_text(FALSE)
        self.points=load_multiplicity_points(self.m,self.f)
    def tearDown(self): self.td.cleanup()

    def test_measured_kbar_and_pmulti(self):
        p=self.points[0]
        self.assertAlmostEqual(p.raw_p_multi,0.01)
        self.assertAlmostEqual(p.raw_kbar,1.01)

    def test_false_pair_correction_splits_cluster_into_two_parents(self):
        p=self.points[0]
        self.assertAlmostEqual(p.false_pair_temporal_ind3,2.0)
        self.assertAlmostEqual(p.corrected_p_multi,8/1002)
        self.assertAlmostEqual(p.corrected_kbar,1010/1002)
        self.assertLess(p.corrected_p_multi,p.raw_p_multi)

    def test_low_conservative_uses_max_0p9_to_3(self):
        self.assertAlmostEqual(low_conservative_probability(self.points),0.02)

    def test_low_scenarios_and_high_hold(self):
        E=np.array([0.5,0.9,2.0,186.0,500.0])
        p0,k0=multiplicity_on_grid(E,self.points,'nominal_logE_linear','K1_only')
        pc,kc=multiplicity_on_grid(E,self.points,'nominal_logE_linear','low_energy_conservative')
        self.assertEqual(p0[0],0); self.assertEqual(k0[0],1)
        self.assertAlmostEqual(pc[0],0.02); self.assertAlmostEqual(kc[0],1.02)
        self.assertAlmostEqual(p0[-1],self.points[-1].raw_p_multi)
        self.assertAlmostEqual(k0[-1],self.points[-1].raw_kbar)

    def test_all_variants_obey_kbar_bound(self):
        E=np.geomspace(0.2,800,100)
        for mv in MULTIPLICITY_VARIANTS:
            for low in LOW_SCENARIOS:
                p,k=multiplicity_on_grid(E,self.points,mv,low)
                self.assertTrue(np.all((p>=0)&(p<=1)))
                self.assertTrue(np.all(k>=1+p-1e-12))

    def test_nhpp_and_window(self):
        self.assertAlmostEqual(nhpp_floor(1.0),1-np.exp(-1))
        x=np.array([1.,1.,np.nan,5.,5.,5.])
        h,i=max_contiguous_hazard(x,2,dt_s=1)
        self.assertEqual(i,3); self.assertAlmostEqual(h,10.)
        h3,i3=max_contiguous_hazard(x,3,dt_s=1)
        self.assertEqual(i3,3); self.assertAlmostEqual(h3,15.)

if __name__=='__main__': unittest.main()
