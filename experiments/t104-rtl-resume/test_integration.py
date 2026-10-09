import unittest
import zlib

from contract_check import check_contract
from integration_check import command, core_error_vectors, fixtures


class IntegratedContractTests(unittest.TestCase):
    def test_whole_bus_and_physical_VALID(self):
        result = check_contract()
        self.assertLess(result["whole_bus_peak_upper_float"], .8)
        self.assertLess(result["response_ns_float"], 2281.971692)

    def test_independent_standard_crc_known_vector(self):
        self.assertEqual(zlib.crc32(b"123456789"), 0xcbf43926)
        packet = command(1, 4, 20, 24, 40).to_bytes(52, "little")
        self.assertEqual(zlib.crc32(packet[:48]), int.from_bytes(packet[48:], "little"))
        self.assertEqual(int.from_bytes(packet[8:16], "little"), 1)
        self.assertEqual(int.from_bytes(packet[40:48], "little"), 40)
        self.assertEqual(packet[:4], (104).to_bytes(4, "little"))

    def test_corrupt_crc_and_replay_are_separate(self):
        good = command(1, 4, 20, 24, 40)
        bad = command(1, 4, 20, 24, 40, True)
        self.assertEqual(good ^ bad, 1<<384)
        rows = core_error_vectors().splitlines()
        self.assertEqual(len(rows), 7)
        self.assertEqual(sum(int(row.split()[2]) for row in rows), 5)

    def test_normal_traffic_not_independent_per_source_envelopes(self):
        for case in (0, 1):
            rows = fixtures(case)[0].splitlines()
            times = [int(row.split()[0]) for row in rows]
            # Joint, not separate CPU and X spacings. Source clock alignment
            # can change this by<=10ns, still far from the5555.56ns boundary.
            self.assertGreaterEqual(min(b-a for a, b in zip(times, times[1:]))-10, 5556)


if __name__ == "__main__":
    unittest.main()
