import csv
import unittest
from pathlib import Path
from collections import Counter
from event_partition import Cell, event_local_dedup
HERE=Path(__file__).resolve().parent
class TestEventPartition(unittest.TestCase):
    def test_45_9_1(self):
        with (HERE/'mapping_sweep_summary.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
        self.assertEqual(Counter(int(r['N_direct_all_series']) for r in rows),Counter({0:45,4:9,5:1}))
    def test_proton_fifth_event(self):
        with (HERE/'registered_direct_events.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
        p=[r for r in rows if r['radiation_type']=='proton']
        self.assertEqual(len(p),1)
        self.assertEqual((p[0]['source_file'],p[0]['segment_id'],p[0]['cluster_id'],p[0]['mapping_id'],p[0]['K']),('clust_p164MeV.txt','1','5480','W_00_11','29'))
    def test_conservation_audit_subset(self):
        with (HERE/'heavy_ion_cross_sections_audit_subset.csv').open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
        self.assertGreater(len(rows),0)
        for r in rows: self.assertEqual(int(r['S_direct_event_cells'])+int(r['S_accumulation']),int(r['S_cells_used']))
    def test_event_local_duplicate_removed(self):
        base=dict(source_file='x',segment_id=1,cluster_id=1,line_start=1,timestamp=None,field_arity=2,field0_raw=None,x=10,y=20,classification='PHYSICAL_NO_ADDRESS',raw_fields=(10,20))
        c1=Cell(cell_index=0,**base); c2=Cell(cell_index=1,**base)
        out,removed=event_local_dedup([c1,c2])
        self.assertEqual(len(out),1); self.assertEqual(removed,1)
if __name__=='__main__': unittest.main()
