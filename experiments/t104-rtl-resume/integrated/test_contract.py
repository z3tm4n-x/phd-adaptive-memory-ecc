"""Independent arithmetic spot checks, scope and source-regression checks."""
import hashlib,importlib.util,json,unittest
from pathlib import Path
from fractions import Fraction as F
HERE=Path(__file__).resolve().parent
def load(name):
    s=importlib.util.spec_from_file_location('integrated_'+name,HERE/(name+'.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
bounds=load('bounds');physical=load('physical_audit')

class ContractTests(unittest.TestCase):
    def test_operations_and_application(self):
        b=bounds.calculate();o=b['operations_ns'];a=b['application']
        self.assertEqual(o['R'],F('92.500920'));self.assertEqual(o['E'],F('148.501480'))
        self.assertEqual(o['read32'],2*o['R'])
        self.assertEqual(a['response_with_10pct_ns'],F('2778.069624'))
        self.assertLess(a['bus_any_1ms_upper'],F('.8'))
    def test_network_bound_covers_dense_grid(self):
        b=bounds.calculate()['history'];lat=float(b['prefix_latency_ns']);s=20.0002
        observed=max(min(2002,3+t/19.9998)+1+(t+.5)/163.99836-max(0,(t-lat)/s)
                     for t in range(0,100001))
        self.assertLessEqual(observed,float(b['backlog_upper'])+1e-9)
        self.assertEqual(b['full_flag_occupancy_upper'],275)
        self.assertLess(b['last_history_to_fresh_applicable_including_loss_CDC_ns'],10000)
    def test_no_runtime_generation_wrap(self):
        b=bounds.calculate()['generation']
        self.assertLess(b['mission_fast_edges_upper'],2**57)
        self.assertGreater(b['mission_fast_edges_upper'],10*365*86400*250000000)
        self.assertFalse(b['runtime_reset'])
    def test_local_tag_flight_not_generation(self):
        b=bounds.calculate()['candidates']
        self.assertEqual(b['tag_bits'],4)
        self.assertGreater(b['tag_wrap_min_ns'],25000)
        self.assertLess(b['with_10pct_ns'],1000)
    def test_physical_unknowns_not_zero(self):
        p=physical.calculate();self.assertEqual(len(p['pin_plan']),42)
        self.assertEqual(p['tie_plan']['VCC'],[12,37,47])
        self.assertIsNone(p['unknown']['ECC_two_alias_function'])
        self.assertIsNone(p['unknown']['actual_load_pF'])
        self.assertEqual(p['source_parameters']['AC_test_load_pF'],30)
        self.assertAlmostEqual(p['conditional_margins_ns']['WE_pulse_over_35ns'],.49776)
    def test_source_defaults(self):
        source=(HERE/'executor.sv').read_text()
        for token in ('WORD_BITS=19','NW=34\'d4500045002','NH=34\'d9000090002',
                      'NR=34\'d9015504896','PAIR_WINDOW=64\'d22500225010','credits<2'):
            self.assertIn(token,source)
    def test_historical_backend_unchanged(self):
        # Pinned after git diff against eab470d returned empty. A plain
        # source archive can run this test without Windows-worktree Git.
        sources={
          'registered/e_backend_registered.sv':'b824217b11b8b9d912a76038b5a3ede04eafca79c8b1296cfbb55f863be3d9ad',
          'registered/handshake_channel.sv':'c3017a5d6bc988b0fab7998fc95a7cfc8d28f6302775a9676356b768f6a90fbd',
          'split/async_queue.sv':'7f50da920cd5f4e03c5ee394d73c6aff22e6f7172bc0f54f73669fea3fb8d69e',
          'split/slow_queue.sv':'181f7da9596594c99681b6050886ea9f55a61de97d9d9e3bc2d108be655c60e0',
          'reference.py':'3fe43213c76b52a725e802bd6ae5be3cb68e5b9078dde08b9139788174e37a19'}
        for path,before in sources.items():
            after=(HERE.parent/path).read_bytes()
            self.assertEqual(before,hashlib.sha256(after).hexdigest(),path)

if __name__=='__main__':unittest.main()
