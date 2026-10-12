import unittest
from fractions import Fraction as F
from bounds import calculate
from check_pins import plan

class ContractTests(unittest.TestCase):
    def test_input_cutpoint_is_eligible_not_waiting(self):
        a=calculate()['application']
        self.assertEqual(a['inbound_to_eligible_ns'],F('177.001760'))
        self.assertGreater(a['inbound_to_eligible_ns'],a['inbound_to_app_waiting_ns'])
    def test_single_envelope_includes_tail(self):
        a=calculate()['application'];tail=a['post_response_recycling']
        self.assertLess(a['response_with_10pct_ns']+tail['allocated_tail_ns'],tail['next_envelope_arrival_min_ns'])
        self.assertLess(a['bus_any_1ms_upper'],F('.8'))
    def test_generation_is_not_16_bit(self):
        g=calculate()['generation']
        self.assertEqual(g['bits'],64)
        self.assertGreater(g['mission_fast_edges_upper'],2**56)
        self.assertLess(g['mission_fast_edges_upper'],2**64-1)
        self.assertFalse(g['runtime_reset'])
    def test_whole_package_and_signal_assignment(self):
        r=plan()
        for key in ['port','FPGA_pin','FMC_contact','SRAM_TSOP48_pin']:
            self.assertEqual(len({x[key] for x in r}),42)
        self.assertEqual({x['SRAM_TSOP48_pin'] for x in r}|{10,12,27,37,46,47},set(range(1,49)))

if __name__=='__main__':unittest.main()
