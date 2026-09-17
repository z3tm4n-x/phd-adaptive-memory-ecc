import csv, json, math, sys, unittest
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.integrate import quad
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'src'))
from contracts import *
from prepare_inputs import ion_sigma,ion_iso60,proton_sigma,proton_anchors,proton_tag

class CodeTests(unittest.TestCase):
    def test_all_single_bits(self):
        for payload in [0,1,0x55555555,0xAAAAAAAA,0xFFFFFFFF,0x12345678]:
            original=encode(payload)
            self.assertEqual(decode(original),('clean',original))
            for b in range(39):self.assertEqual(decode(original^(1<<b)),('corrected',original))
    def test_all_double_bits(self):
        for payload in [0,0x12345678,0xFFFFFFFF]:
            original=encode(payload)
            for a in range(39):
                for b in range(a):self.assertEqual(decode(original^(1<<a)^(1<<b))[0],'uncorrectable')
    def test_mapping_is_bijection(self):
        with (R/'inputs/logical_mapping.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual({int(r['hamming_position_1based']) for r in rows},set(range(1,40)))
        self.assertEqual(len({(r['chip'],r['DQ']) for r in rows}),39)
        self.assertEqual(sum(r['role']!='data' for r in rows),7)
    def test_dimensions(self):
        m=json.loads((R/'config/memory.json').read_text())
        self.assertEqual(m['active_bits'],m['words']*39)
        self.assertEqual(m['active_bits']+m['padding_bits'],m['physical_addressable_bits'])
        self.assertEqual(m['useful_bytes'],4194304)
        self.assertAlmostEqual(m['pass_seconds'],.3145728)
    def test_wrong_bit_multiplier_sentinel(self):
        with self.assertRaises(ValueError):per_bit_to_active(1e-12,bits=32*2**20)
        with self.assertRaises(ValueError):per_bit_to_active(1e-12,bits=48*2**20)
    def test_double_normalization_sentinel(self):
        with self.assertRaises(ValueError):per_bit_to_active(1,normalization='array')
        self.assertAlmostEqual(per_bit_to_active(1e-12),.000040894464)

class ResponseTests(unittest.TestCase):
    def test_let_jacobian(self):
        x=np.array([100,200,400,800.]);y=np.array([4,3,2,1.])
        X,Y=convert_let_density(x,y)
        self.assertEqual(np.trapezoid(y,x),np.trapezoid(Y,X))
        wrong=np.trapezoid(y,X)
        self.assertAlmostEqual(wrong/np.trapezoid(Y,X),.001)
    def test_flux_factors(self):
        self.assertAlmostEqual(differential_to_omni([1],per_keV=True,per_sr=True)[0],4000*math.pi)
        self.assertEqual(differential_to_omni([1],per_keV=False,per_sr=False)[0],1)
    def test_invalid_not_zero(self):
        for x in [-999.9,float('nan')]:
            with self.assertRaises(ValueError):differential_to_omni([x],per_keV=False,per_sr=True)
    def test_proton_nonmonotonic(self):
        self.assertGreater(float(proton_sigma(1)),10000*float(proton_sigma(186)))
        self.assertLess(float(proton_sigma(.6)),float(proton_sigma(1)))
        self.assertLess(float(proton_sigma(5)),float(proton_sigma(1)))
    def test_anchor_values_preserved(self):
        for e,s in proton_anchors():self.assertAlmostEqual(float(proton_sigma(e))/s,1,places=12)
    def test_missing_29_not_zero(self):
        self.assertGreater(float(proton_sigma(29)),0)
        self.assertIn('unmeasured',proton_tag(29))
        with (R/'inputs/proton_repository_points.csv').open() as f:r=[x for x in csv.DictReader(f) if float(x['energy_MeV'])==29][0]
        self.assertEqual(r['sigma_cm2_per_bit'],'')
    def test_184_not_relabelled(self):
        self.assertNotIn(184,proton_anchors()[:,0])
        self.assertIn(186,proton_anchors()[:,0])
    def test_continuations_are_named(self):
        self.assertIn('ASSUMPTION',proton_tag(.2));self.assertIn('ASSUMPTION',proton_tag(1000))
        self.assertEqual(float(proton_sigma(0)),0)
    def test_ion_threshold_and_sat(self):
        self.assertEqual(float(ion_sigma(.15)),0)
        self.assertGreater(float(ion_sigma(.151)),0)
        self.assertLess(float(ion_sigma(80)),2.6e-7)
        self.assertAlmostEqual(float(ion_sigma(1e5))/2.6e-7,1)
    def test_ion_angle_independent_scalar(self):
        for l in [.01,.075,.1,.15,1,10,70,200,1000]:
            cut=l/.15
            q,_=quad(lambda theta:float(ion_sigma(l/math.cos(theta)))*math.cos(theta)*math.sin(theta),0,math.pi/3,epsabs=1e-19,points=[math.acos(cut)] if .5<cut<1 else None)
            self.assertLess(abs(q-ion_iso60(l)[0]),3e-15)
    def test_ion_angular_constant_plateau(self):
        self.assertAlmostEqual(float(ion_iso60(1e5)[0])/2.6e-7,.375,places=12)
    def test_registered_counts(self):
        with (R/'inputs/registered_multiplicity.csv').open() as f:rs=list(csv.DictReader(f))
        grouped={}
        for r in rs:grouped.setdefault(r['energy_MeV'],[]).append(r)
        for group in grouped.values():
            self.assertEqual(sum(int(r['registered_count']) for r in group),int(group[0]['registered_total']))
            self.assertEqual(sum(int(r['K'])*int(r['registered_count']) for r in group),int(group[0]['recorded_bit_total']))
            self.assertAlmostEqual(sum(float(r['conditional_probability']) for r in group),1,places=13)
        self.assertEqual(sum(int(g[0]['registered_total']) for g in grouped.values()),140111)
        self.assertEqual(sum(int(g[0]['recorded_bit_total']) for g in grouped.values()),162910)
    def test_original_archive_audit(self):
        p=R/'provenance/cosrad_old_archive.json'
        self.assertTrue(p.exists(),'generate manifest with --archive first')
        m=json.loads(p.read_text());self.assertEqual(m['member_count'],38)
        self.assertNotIn(.27,m['shielding_g_cm2']);self.assertFalse(m['is_new_1mm_input'])

class ExecutorTests(unittest.TestCase):
    def runx(self,events=(),H=1200,tau=600):
        return run_fixed(words=2,horizon_ns=H,period_ns=tau,upsets=events)
    def test_parity_in_own_count(self):
        for bit in [0,1,3,7,15,31,38]:
            r=self.runx([Upset(10,((0,bit),))]);self.assertEqual(r.completed_counts[0],(600,1))
    def test_clean_latch_does_not_erase_late_upset(self):
        r=self.runx([Upset(150,((0,2),))],H=600)
        self.assertEqual(r.completed_counts,[(600,0)]);self.assertNotEqual(r.final_words[0],0)
    def test_dirty_latch_then_second_hit_is_latched_failure(self):
        r=self.runx([Upset(10,((0,2),)),Upset(150,((0,4),))],H=600)
        self.assertEqual(r.first_ecap_ns,150);self.assertEqual(r.final_words[0],0)
    def test_same_bit_toggle_is_not_failure(self):
        r=self.runx([Upset(10,((0,2),)),Upset(50,((0,2),))]);self.assertIsNone(r.first_ecap_ns)
        self.assertEqual(sum(c for _,c in r.completed_counts),0)
    def test_group_is_atomic(self):
        r=self.runx([Upset(50,((0,2),(0,4)))]);self.assertEqual(r.first_ecap_ns,50)
    def test_late_word_residual_persists(self):
        r=self.runx([Upset(350,((0,2),))])
        self.assertEqual(r.completed_counts,[(600,0),(1200,1)])
    def test_terminal_no_false_zero_sentinel(self):
        r=self.runx([Upset(10,((0,2),))],H=450)
        self.assertEqual(r.completed_counts,[]);self.assertEqual(r.writes,1)
        self.assertNotEqual(r.completed_counts,[(450,0)])
    def test_terminal_after_latch_before_commit(self):
        r=self.runx([Upset(10,((0,2),))],H=200)
        self.assertEqual(r.writes,0);self.assertEqual(r.reads,1);self.assertNotEqual(r.final_words[0],0)
    def test_commit_upset_latch_tie(self):
        r=self.runx([Upset(10,((0,2),)),Upset(300,((0,4),))],H=600)
        self.assertIsNone(r.first_ecap_ns);self.assertEqual(r.final_words[0],1<<4)
    def test_own_count_not_shared_sentinel(self):
        stream=(Upset(350,((0,2),)),Upset(800,((0,2),)))
        a=self.runx(stream,H=1200,tau=600);b=self.runx(stream,H=1200,tau=900)
        self.assertNotEqual(a.completed_counts,b.completed_counts)
        self.assertEqual(stream,(Upset(350,((0,2),)),Upset(800,((0,2),))))
    def test_ecap_not_cleared_by_later_toggle(self):
        r=self.runx([Upset(10,((0,2),(0,4))),Upset(20,((0,4),))]);self.assertEqual(r.first_ecap_ns,10)
    def test_horizon_contract(self):
        r=self.runx([Upset(600,((0,2),(0,4)))],H=600)
        self.assertIsNone(r.first_ecap_ns);self.assertEqual(r.completed_counts,[(600,0)])
    def test_invalid_period(self):
        with self.assertRaises(ValueError):self.runx(tau=599)
    def test_pair_bound_independent_fraction_oracle(self):
        W,n,H,tau,P=4,39,23,5,2
        S=Fraction(0)
        for j in range(W):
            d=Fraction(P*(W-1-j),W);checks=[Fraction(0)]
            k=1
            while k*tau-d <= H:checks.append(k*tau-d);k+=1
            checks.append(Fraction(H));S+=sum((b-a)**2 for a,b in zip(checks,checks[1:]))
        rate=Fraction(1,10);q=Fraction(n-1,2*n)*(rate/W)**2*S
        self.assertAlmostEqual(pair_bound_constant(float(rate),H,tau,W,n,P),float(q),places=15)
    def test_no_scan_pair_bound(self):
        # No first check occurs before H. Complete horizon exposure must be retained.
        self.assertAlmostEqual(pair_bound_constant(.1,1,10,4,39,2),(38/78)*(.1**2)/4)

if __name__=='__main__':unittest.main(verbosity=2)
