import bisect
from pathlib import Path
import unittest
from burst_boundary import build
from burst_run_inputs import build as original_build


class BurstBoundaryTests(unittest.TestCase):
    def test_main_inputs_identical(self):
        self.assertEqual(build(), original_build())
        self.assertEqual(build(pilot_events=20), original_build(pilot_events=20))

    def test_closed_boundary_and_wrong_selector_sentinel(self):
        for now in (80070, 202379545401330):
            epochs = [now - 4, now, now + 4_793_439_060]
            self.assertEqual(epochs[bisect.bisect_left(epochs, now)], now)
            self.assertGreater(epochs[bisect.bisect_right(epochs, now)], now)
            for t in (now - 2, now + 2):
                self.assertEqual(bisect.bisect_left(epochs, t), bisect.bisect_right(epochs, t))

    def test_new_runner_uses_closed_boundary(self):
        source = (Path(__file__).parent/'run_burst_v2.py').read_text()
        self.assertIn('bisect.bisect_left(external,now-t0)', source)
        self.assertNotIn('bisect.bisect_right(external,now-t0)', source)

    def test_large_timestamp_range_and_known_loss(self):
        t = 202376233820426
        self.assertEqual((1000*t)//1000, t)
        self.assertEqual(202376233820425984//1000, t-1)
        self.assertLess(1000*(363900_000_000_000+1000), 2**64)
        source = (Path(__file__).parent/'tb_burst_v2.sv').read_text()
        self.assertNotIn('%0t', source)


if __name__ == '__main__':
    unittest.main()
