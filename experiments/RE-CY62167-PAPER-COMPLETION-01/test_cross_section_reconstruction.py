import csv, math, unittest
from pathlib import Path
from cross_section_model import point_cross_sections
HERE=Path(__file__).resolve().parent
class TestCrossSection(unittest.TestCase):
    def test_baseline_42_57(self):
        with (HERE/'heavy_ion_cross_sections.csv').open(newline='',encoding='utf-8') as f:
            rows={(r['mapping_id'],float(r['LET_MeV_cm2_mg'])):r for r in csv.DictReader(f)}
        a=rows[('W_00_01',42.0)]; b=rows[('W_00_01',57.0)]
        self.assertEqual((int(a['N_direct']),int(a['S_direct_event_cells']),int(a['S_accumulation'])),(1,43,16969))
        self.assertEqual((int(b['N_direct']),int(b['S_direct_event_cells']),int(b['S_accumulation'])),(3,127,21058))
        self.assertAlmostEqual(float(a['sigma_accumulation_point']),1.8139804054,places=9)
        self.assertAlmostEqual(float(b['sigma_accumulation_point']),2.3463996153,places=9)
        self.assertAlmostEqual(float(b['sigma_direct_point']),3.342767046e-4,places=13)
    def test_equivalent_forms(self):
        d=point_cross_sections(N_events=1060,S_cells_used=21185,N_direct=3,S_accumulation=21058,let_value=57)
        self.assertAlmostEqual(d['sigma_direct_point_cm2'],d['p_D_reg']*d['sigma_event_cm2'],places=15)
        self.assertAlmostEqual(d['sigma_accumulation_point_cm2'],d['mbar_C']*d['sigma_event_cm2'],places=14)
    def test_effective_fluence_not_named_measured(self):
        text=(HERE/'REPORT.md').read_text(encoding='utf-8')
        self.assertIn('ARTICLE-NORMALIZED EFFECTIVE FLUENCE',text)
        self.assertIn('not measured fluence',text)
if __name__=='__main__': unittest.main()
