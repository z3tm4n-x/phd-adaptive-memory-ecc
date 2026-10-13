import ctypes,unittest
from batch_budget import calculate
from verify_batch import Batch,BatchState,Decision

class TransportContractTests(unittest.TestCase):
    def test_abi(self):
        self.assertEqual((ctypes.sizeof(Batch),ctypes.sizeof(BatchState),ctypes.sizeof(Decision)),(96,72,32))
        self.assertEqual(Batch.end_generation.offset,16)
        self.assertEqual(Batch.flags.offset,88)
        self.assertEqual(Decision.crc.offset,28)
    def test_full_round_phase_not_free(self):
        d=calculate()
        self.assertAlmostEqual(d['fixed_sum_ns']+2*d['round_max_allowed_ns'],10000)
        self.assertGreater(d['unchanged_history_ns'],5000)
        self.assertLess(d['round_max_allowed_ns'],1700)
    def test_unknown_not_zero(self):
        d=calculate()
        for k in ('CPU_round_upper_ns','PS_AXI_upper_ns','B_established_upper_ns','reaction_established_upper_ns','CPU_load'):
            self.assertIsNone(d[k])
        self.assertFalse(d['whole_system_price_claim'])
    def test_candidate_allocation_and_crc(self):
        d=calculate()
        self.assertLess(d['derived_digital_certificate_ns'],d['certificate_allocation_ns'])
        self.assertLess(d['certificate_with_10pct_ns'],1000)
        self.assertEqual(d['CRC_words'],7)
        self.assertAlmostEqual(d['CRC_processing_ns'],140.5014)
if __name__=='__main__':unittest.main()
