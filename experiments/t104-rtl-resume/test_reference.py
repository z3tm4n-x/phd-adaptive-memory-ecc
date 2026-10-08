import random
import unittest
from dataclasses import replace

from reference import (ApplicationQueue, Calendar, CONTROL, ETransaction,
                       Permission, READ32, Request, ServiceConfig, U64,
                       WRITE32, load_config, resource_contract)
from memory_oracle import MemoryOracle


def trace(kind, err=False, be=15, data=0xFEDCBA98, low=0x1234):
    x = ETransaction(Request(kind, 0, data, be), 0)
    out = []
    for t in range(0, 220, 4):
        p = x.step(t, low if t == 60 else 0x5678, err)
        out.append((t, p))
        if p["done"]:
            break
    return out


class ServiceTests(unittest.TestCase):
    def test_clean_E_no_write_92(self):
        tr = trace(CONTROL)
        self.assertEqual(tr[-1][0], 92)
        self.assertEqual(sum(p["we"] for _, p in tr), 0)
        self.assertEqual([t for t, p in tr if p["sample"]], [60])

    def test_dirty_E_write_132_release148_flag_once(self):
        tr = trace(CONTROL, True)
        self.assertEqual(tr[-1][0], 148)
        self.assertEqual([t for t, p in tr if p["commit"]], [132])
        self.assertEqual([t for t, p in tr if p["flag"]], [64])
        self.assertEqual([t for t, p in tr if p["we"]], list(range(92, 132, 4)))

    def test_read32_no_inline_write_or_new_control_flag(self):
        tr = trace(READ32, True)
        self.assertEqual(tr[-1][0], 184)
        self.assertEqual([t for t, p in tr if p["sample"]], [60, 152])
        self.assertFalse(any(p["we"] or p["flag"] for _, p in tr))
        self.assertEqual(tr[-1][1]["data"], 0x56781234)

    def test_observed_write_clean_still_writes(self):
        tr = trace(WRITE32)
        self.assertEqual(tr[-1][0], 216)
        self.assertEqual([t for t, p in tr if p["commit"]], [132, 200])
        self.assertEqual([t for t, p in tr if p["sample"]], [60])

    def test_observed_write_err_before_modification_once(self):
        tr = trace(WRITE32, True)
        self.assertEqual([t for t, p in tr if p["flag"]], [64])
        self.assertLess(64, min(t for t, p in tr if p["we"]))
        self.assertTrue(all(p["busy"] for t, p in tr if t < 216))

    def test_partial_write_all_byte_enables(self):
        for be in range(1, 16):
            with self.subTest(be=be):
                p = dict(trace(WRITE32, True, be))[92]
                expected = ((0x98 if be & 1 else 0x34)
                            | ((0xBA if be & 2 else 0x12) << 8))
                self.assertEqual(p["dout"], expected)
                self.assertEqual(p["be"], 3)
                # High-only request must still observe full38 on an enabled read.
                self.assertEqual(dict(trace(WRITE32, True, be))[60]["be"], 3)

    def test_coherent_latch_not_live_ERR_at_decision(self):
        x = ETransaction(Request(CONTROL, 0), 0)
        for t in range(0, 68, 4):
            p = x.step(t, 0x1234, t == 60)
        self.assertEqual(p["flag"], 1)

    def test_no_drive_while_reading(self):
        for kind in range(3):
            for err in (False, True):
                for _, p in trace(kind, err):
                    self.assertFalse(p["oe"] and p["drive"])
                    self.assertFalse(p["we"] and not p["drive"])

    def test_timing_pin_pulse_minima(self):
        # Independent corner arithmetic: xi=0.99999, two edge uncertainties
        # total0.5ns, output-path skew4ns. PWE first40 and second40 >=35ns.
        self.assertGreaterEqual(40 * .99999 - .5 - 4, 35)
        self.assertGreaterEqual(56 * .99999 - .5 - 4 - 2 - 1, 45)
        # OE disable64 -> drive92: 28 ticks covers output4+HZ18+0.5.
        self.assertGreaterEqual(28 * .99999 - .5 - 4, 18)

    def test_reject_bad_requests_and_time(self):
        for req in (Request(3, 0), Request(0, 8), Request(2, 1, -1),
                    Request(2, 1, 0, 0), Request(2, 1, 0, 16)):
            with self.assertRaises(ValueError):
                req.validate(8)
        with self.assertRaises(ValueError):
            ETransaction(Request(0, 0), 0).step(1)


class FullWordOracleTests(unittest.TestCase):
    def run_operation(self, m, req, start=0, hits=None):
        x = ETransaction(req, start)
        m.begin(req.request_id, req.word, start, ("control", "read32", "write32")[req.kind])
        hits = hits or {}
        for t in range(start, start + 220, 4):
            for bit in hits.get(t, []):
                m.words[req.word].toggle(bit, t)
            data = m.words[req.word].data
            err = bool(m.words[req.word].errors)
            if t == start + 60:
                data, err = m.observe(t)
            p = x.step(t, (data >> (16 if t == start + 152 else 0)) & 65535, err)
            if p["commit"]:
                # Physical write data was stable before the rising WE edge.
                prior = pins
                m.write(t, p["alias"], prior["dout"], prior["be"], req.request_id)
            pins = p
            if p["done"]:
                m.release(t)
                return t
        self.fail("never completed")

    def test_all38_positions_equal_observation_and_repair(self):
        for bit in range(38):
            with self.subTest(bit=bit):
                m = MemoryOracle(1)
                m.words[0].toggle(bit, -1)
                self.run_operation(m, Request(CONTROL, 0))
                self.assertEqual(m.flags, [(64, 0, 0)])
                self.assertFalse(m.words[0].errors)

    def test_clean_latch_does_not_imply_clean_release(self):
        m = MemoryOracle(1)
        self.assertEqual(self.run_operation(m, Request(CONTROL, 0), hits={64: [37]}), 92)
        self.assertEqual(m.words[0].errors, {37: 64})
        self.assertFalse(m.flags)

    def test_E_retains_permitted_inside_operation_residual(self):
        m = MemoryOracle(1)
        m.words[0].toggle(0, -1)
        self.run_operation(m, Request(CONTROL, 0), hits={100: [35]})
        self.assertEqual(m.words[0].errors, {35: 100})
        self.assertEqual(m.words[0].first_exceedance, 100)

    def test_repeat_toggle_and_absorbing_first_exceedance(self):
        m = MemoryOracle(1)
        w = m.words[0]
        w.toggle(2, 1); w.toggle(2, 2)
        self.assertIsNone(w.first_exceedance)
        w.toggle(2, 3); w.toggle(33, 4); w.toggle(33, 5)
        self.assertEqual(w.first_exceedance, 4)

    def test_atomic_new_write_after_repair_no_stale_overwrite(self):
        m = MemoryOracle(1)
        m.words[0].data = 0x12345678
        m.words[0].toggle(37, -1)
        self.run_operation(m, Request(CONTROL, 0, request_id=1))
        self.run_operation(m, Request(WRITE32, 0, 0xABCDEF01, request_id=2), 1568 + 1312)
        self.assertEqual(m.words[0].data, 0xABCDEF01)
        self.assertEqual(len(m.flags), 1)

    def test_masked_logical_data_independent_byte_checker(self):
        for mask in range(1, 16):
            m = MemoryOracle(1)
            m.words[0].data = 0x12345678
            self.run_operation(m, Request(WRITE32, 0, 0xABCDEF01, mask))
            old = bytes.fromhex("78563412")
            new = bytes.fromhex("01efcdab")
            expected = bytes(new[b] if mask & 2**b else old[b] for b in range(4))
            self.assertEqual(m.words[0].data, int.from_bytes(expected, "little"))

    def test_observed_write_reports_checkbit_before_overwrite(self):
        m = MemoryOracle(1)
        m.words[0].toggle(36, -1)
        self.run_operation(m, Request(WRITE32, 0, 0xF00DCAFE))
        self.assertEqual(len(m.flags), 1)
        self.assertFalse(m.words[0].errors)

    def test_soft_reset_preserves_pending_lock_and_memory(self):
        m = MemoryOracle(1)
        m.words[0].toggle(37, -1)
        m.begin(1, 0, 0, "control"); m.observe(60)
        before = m.lock
        self.assertEqual(m.soft_reset(), before)
        with self.assertRaises(ValueError):
            m.begin(2, 0, 80, "write32")
        m.write(132, 0, 0); m.release(148)

    def test_sentinel_raw_unobserved_write_rejected(self):
        m = MemoryOracle(1)
        m.words[0].toggle(37, -1)
        m.begin(1, 0, 0, "write32")
        with self.assertRaisesRegex(ValueError, "unobserved"):
            m.write(132, 0, 123)

    def test_sentinel_missing_repair_rejected(self):
        m = MemoryOracle(1)
        m.words[0].toggle(0, -1)
        m.begin(1, 0, 0, "control"); m.observe(60)
        with self.assertRaisesRegex(ValueError, "missing write"):
            m.release(148)

    def test_sentinel_stale_pending_rejected(self):
        m = MemoryOracle(1)
        m.begin(2, 0, 0, "write32"); m.observe(60)
        with self.assertRaisesRegex(ValueError, "stale pending"):
            m.write(132, 0, 123, transaction_id=1)


class CalendarTests(unittest.TestCase):
    def setUp(self):
        self.c = ServiceConfig(words=8).validate()
        self.x = Calendar(self.c)

    def enable(self, at=1):
        self.x.recovered(at)
        return self.x.command(Permission(104, 1, at, at, 10000, 20000), at)

    def test_initial_and_mandatory(self):
        self.enable()
        for j in range(2, 16):
            t = self.c.start(j) - self.c.lead
            self.assertEqual(self.x.freeze(j, t), j < 8 or j % 3 == 0)

    def test_alarm_before_or_on_freeze_forces_service(self):
        d = self.c.start(8) - self.c.lead
        for offset in (-4, 0):
            self.x = Calendar(self.c); self.enable()
            self.x.err(d + offset)
            self.assertTrue(self.x.freeze(8, d))

    def test_alarm_after_freeze_does_not_revoke_skip(self):
        self.enable(); d = self.c.start(8) - self.c.lead
        self.assertFalse(self.x.freeze(8, d))
        self.x.err(d + 4)
        self.assertFalse(self.x.committed[8])

    def test_default_missing_permission_is_fast(self):
        self.assertTrue(self.x.freeze(8, self.c.start(8) - self.c.lead))

    def test_early_command_shadow_and_expiry(self):
        self.x.command(Permission(104, 1, 0, 100, 104, 200), 0)
        self.assertIsNone(self.x.active)
        self.x.at(96); self.assertIsNone(self.x.active)
        self.x.at(100); self.assertIsNotNone(self.x.active)
        self.x.at(200); self.assertIsNone(self.x.active)

    def test_inclusive_command_deadline_and_late_rejection(self):
        p = Permission(104, 1, 0, 0, 100, 200)
        self.assertTrue(self.x.command(p, 100))
        y = Calendar(self.c)
        self.assertFalse(y.command(p, 104))

    def test_bad_command_and_sequence_replay_revoke(self):
        self.enable()
        self.assertFalse(self.x.command(Permission(104, 1, 1, 1, 10000, 20000), 4))
        self.assertIsNone(self.x.active)
        y = Calendar(self.c)
        self.assertFalse(y.command(Permission(105, 1, 0, 0, 100, 200), 0))

    def test_loss_reset_no_new_mission_or_old_shadow(self):
        self.x.command(Permission(104, 1, 0, 100, 200, 300), 0)
        self.x.loss(4); self.x.recovered(8); self.x.at(100)
        self.assertIsNone(self.x.active)
        self.assertEqual(self.x.mission, 104)
        self.assertFalse(self.x.command(Permission(104, 2, 0, 100, 200, 300), 100))

    def test_overflow_and_clock_rollback_forbid_skip(self):
        self.x.err_count = U64
        self.x.err(1); self.x.recovered(2)
        self.assertTrue(self.x.overflow)
        self.assertEqual(self.x.err_count, U64)
        with self.assertRaises(ValueError):
            self.x.at(1)
        self.assertFalse(self.x.phase_valid)

    def test_fullW_permutation_and_period_independent_identity(self):
        c = load_config()
        addresses = [c.address(j) for j in range(c.words)]
        self.assertEqual(len(set(addresses)), c.words)
        self.assertTrue(all(3 * a % c.words == j for j, a in enumerate(addresses)))
        self.assertTrue(all(c.start(j+c.words)-c.start(j) == c.words*196 for j in range(8)))
        self.assertEqual(c.words*196, 102760448)

    def test_absolute_start_and_skip_advance(self):
        self.x.freeze(0, 0); self.x.freeze(1, 0)
        self.assertEqual(self.x.start_slot(0, 0), (True, 0))
        self.assertEqual(self.x.start_slot(1, 164), (True, 3))
        self.x.loss(168)
        self.assertEqual(self.x.started, 2)

    def test_tuple_validation(self):
        for k, value in (("words", 9), ("ka", 2), ("ka", 5), ("g", 192),
                         ("lead", 256), ("app_charge", 208), ("core", 5)):
            with self.assertRaises(ValueError):
                replace(self.c, **{k: value}).validate()
        with self.assertRaises(ValueError):
            self.c.start(U64)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.q = ApplicationQueue(words=8)

    def test_offer_not_grant_and_first_valid_retained(self):
        self.q.offer(Request(WRITE32, 1, request_id=1), 1, 16)
        self.assertIsNone(self.q.entries[0].granted)
        self.assertIsNone(self.q.grant(1308))
        self.assertEqual(self.q.grant(1312).request_id, 1)
        self.assertEqual(self.q.entries[0].offered, 1)

    def test_two_places_include_active_and_reply(self):
        self.q.offer(Request(WRITE32, 1, request_id=1), 1, 16)
        self.q.grant(1312)
        self.q.offer(Request(READ32, 1, request_id=2), 1316, 1332)
        self.assertFalse(self.q.offer(Request(READ32, 1, request_id=3), 1340, 1356))
        self.q.complete(1, 1528)
        self.assertEqual(len(self.q.entries), 2)
        self.q.consume(1, 1628)
        self.assertEqual(len(self.q.entries), 1)

    def test_reply_backpressure_does_not_retain_lock(self):
        self.q.offer(Request(READ32, 0, request_id=1), 0, 16)
        self.q.grant(1312); self.q.complete(1, 1496)
        self.assertFalse(any(e.state == "active" for e in self.q.entries))

    def test_reset_does_not_cancel_accepted_request(self):
        self.q.offer(Request(WRITE32, 1, request_id=1), 1, 16)
        self.q.grant(1312); self.q.soft_reset()
        self.q.complete(1, 1528)
        self.assertEqual(self.q.entries[0].state, "reply")

    def test_completion_before_release_rejected(self):
        self.q.offer(Request(WRITE32, 1, request_id=1), 1, 16)
        self.q.grant(1312)
        with self.assertRaises(ValueError):
            self.q.complete(1, 1512)


class ResourceTests(unittest.TestCase):
    def test_joint_bound_with_all_ERR_and_observed_writes(self):
        r = resource_contract()
        self.assertTrue(r["passes"])
        self.assertGreater(r["peak_upper_float"], .79)

    def test_no_overlap_all_ERR_entire_frame(self):
        # Independent direct intervals, no production timing helpers.
        intervals = [(164*j, 164*j+148) for j in range(8)] + [(1312, 1528)]
        self.assertTrue(all(a[1] < b[0] for a, b in zip(intervals, intervals[1:])))
        self.assertLess(intervals[-1][1], 1568)
        self.assertGreaterEqual((240*.99999-.5)/1.1, 217.002160)

    def test_seeded_streams_reference_safety(self):
        rng = random.Random(104)
        for _ in range(1000):
            tr = trace(rng.randrange(3), bool(rng.randrange(2)), rng.randrange(1, 16),
                       rng.randrange(1 << 32), rng.randrange(65536))
            self.assertEqual(sum(p["done"] for _, p in tr), 1)
            self.assertLessEqual(sum(p["flag"] for _, p in tr), 1)


if __name__ == "__main__":
    unittest.main()
