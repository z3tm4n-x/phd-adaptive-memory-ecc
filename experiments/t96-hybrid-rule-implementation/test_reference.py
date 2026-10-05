"""Directed Stage-A checks. No rare-event Monte Carlo or production RTL proof."""
from dataclasses import replace
from fractions import Fraction as F
import itertools
import unittest

from reference import (U64, Calendar, Executor, Gate, Message, Parameters,
                       Permission, Rule, can_grant, fifo_grants, load_inputs,
                       mapping_report, mask_max, resource_bounds)


def packet(p, index=0, count=0, epoch=1, **changes):
    """Declared synthetic full-quality/raw-count profile; not physical data."""
    start = index * p.stride
    m = Message(index, epoch, index, p.config_id, start, start + p.window,
                count=count, loss_upper=0, live_ticks=p.window, complete=True,
                calibration_ok=True, clock_ok=True, integrity_ok=True,
                loss_contract_ok=True)
    return replace(m, **changes)


class Fixed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = Parameters.accepted()
        cls.cfg, cls.h, cls.row = load_inputs()

    def fresh(self, last=4):
        r = Rule(self.p)
        self.assertTrue(r.epoch_begin(1, 0, self.p.config_id))
        for i in range(last + 1):
            self.assertEqual(r.message(packet(self.p, i), self.p.deadline(i)), "LOW")
        return r

    def optional_at(self, tick, p=None):
        p = p or self.p
        c = Calendar(p)
        j = max(p.W, tick // p.g)
        while c.slot(j).decision < tick or j % p.ka == 0:
            j += 1
        return c.slot(j)

    def permissive(self, slot, **kw):
        p = self.p
        return replace(Permission(p.mission_id, p.config_id, 1, 0,
                       max(0, slot.decision), p.end, 0, p.end,
                       0, 0, 0, False), **kw).sealed()

    def small_committed_skip(self):
        """Review #1: exact W=8 prefix and synthetic all-covering LOW."""
        p = replace(self.p, W=8, ka=3)
        c, g = Calendar(p), Gate(p)
        e = Executor(p, g, functional_writes=True)
        a = Permission(p.mission_id, p.config_id, 1, 0, 0, p.end,
                       0, p.end, 0, 0, 0, False).sealed()
        self.assertTrue(g.receive(a, 0))
        for j in range(8):
            s = c.slot(j)
            e.start(g.freeze(s, max(0, s.decision)), s.start)
            e.latch(s.start + 48, 0)
            e.finish(s.fence)
        s = c.slot(8)
        d = g.freeze(s, s.decision)
        self.assertFalse(d.execute)
        return p, c, g, e, s, d

    def test_sources_and_exact_anchor(self):
        self.assertEqual((self.p.W, self.p.ka, self.p.g, self.p.c), (524288, 367, 140, 100))
        self.assertEqual(self.p.Ps, 73400320)
        self.assertEqual(self.p.delivery, 1100011001)
        self.assertEqual(self.p.lease, 2940811639)
        self.assertEqual(self.p.hold, 1000010001)

    def test_full_W_permutation_no_duplicate_and_inverse(self):
        c = Calendar(self.p)
        seen = {c.inverse * j % self.p.W for j in range(self.p.W)}
        self.assertEqual(len(seen), self.p.W)
        self.assertEqual(c.inverse * self.p.ka % self.p.W, 1)

    def test_period_and_phase_full_W_all_words(self):
        c, p = Calendar(self.p), self.p
        # Complete residue set, not a small-W inference.
        for j in range(p.W):
            s, t = c.slot(j), c.slot(j + p.W)
            self.assertEqual((t.word, t.start - s.start), (s.word, p.Ps))
            self.assertEqual(c.slot(j + p.ka * p.W).start - s.start, p.ka * p.Ps)

    def test_paired_edges_no_compressed_Wc_period(self):
        c = Calendar(self.p)
        self.assertEqual([c.slot(j).start for j in range(6)], [0, 100, 280, 380, 560, 660])
        self.assertNotEqual(self.p.Ps, self.p.W * self.p.c)

    def test_initial_and_mandatory_cannot_skip(self):
        c = Calendar(self.p)
        for j in (0, 1, self.p.W - 1, 367 * 2000):
            s = c.slot(j)
            g = Gate(self.p)
            g.receive(self.permissive(s), 0)
            self.assertTrue(g.freeze(s, max(0, s.decision)).execute)

    def test_two_sided_LOW_equal_and_one_tick_fail(self):
        s = self.optional_at(self.p.W * self.p.g + self.p.Ps)
        for dl, dr, execute in ((0, 0, False), (1, 0, True), (0, -1, True)):
            g = Gate(self.p)
            a = self.permissive(s, low_left=s.fence-self.p.Ps+dl,
                                low_right=s.fence+self.p.Ps+dr)
            self.assertTrue(g.receive(a, 0))
            self.assertEqual(g.freeze(s, s.decision).execute, execute)

    def test_end_radius_is_clipped_conservatively(self):
        p = replace(self.p, end=10000, W=8, ka=3)
        s = Calendar(p).slot(70)
        a = replace(self.permissive(s), valid_until=p.end,
                    low_left=0, low_right=p.end).sealed()
        g = Gate(p)
        g.receive(a, 0)
        self.assertLess(s.fence, p.end)
        self.assertFalse(g.freeze(s, s.decision).execute)

    def test_ERR_before_at_after_decision_and_immutability(self):
        s = self.optional_at(3_000_000_000)
        for offset in (-1, 0, 1):
            g = Gate(self.p)
            g.receive(self.permissive(s), 0)
            if offset <= 0:
                g.err(s.decision + offset)
            d = g.freeze(s, s.decision)
            if offset > 0:
                g.err(s.decision + offset)
            g.loss(s.decision+2)
            self.assertEqual(d.execute, offset <= 0)
            self.assertIs(g.freeze(s, s.start), d)

    def test_late_command_and_crc_failure_default_S(self):
        s = self.optional_at(3_000_000_000)
        for a, now in ((self.permissive(s), s.decision+1),
                       (replace(self.permissive(s), low_right=1), 0)):
            g = Gate(self.p)
            self.assertFalse(g.receive(a, now))
            self.assertTrue(g.freeze(s, s.decision).execute)

    def test_command_atomicity_replay_and_wrong_mission(self):
        s = self.optional_at(3_000_000_000)
        g, a = Gate(self.p), self.permissive(s)
        self.assertTrue(g.receive(a, 0))
        self.assertIs(g.active, a)
        self.assertFalse(g.receive(a, 1))
        self.assertIsNone(g.active)
        self.assertFalse(g.receive(replace(a, sequence=2, mission_id="other").sealed(), 1))

    def test_no_permission_or_expired_permission_is_S(self):
        s = self.optional_at(3_000_000_000)
        for active in (False, True):
            g = Gate(self.p)
            if active:
                g.receive(self.permissive(s, valid_until=s.decision), 0)
            self.assertTrue(g.freeze(s, s.decision).execute)

    def test_queued_pre_loss_permission_cannot_resurrect_LOW(self):
        s = self.optional_at(4_000_000_000)
        g = Gate(self.p)
        queued = self.permissive(s, issued_at=10, apply_by=s.decision)
        g.loss(11)
        self.assertFalse(g.receive(queued, 12))
        self.assertIsNone(g.active)
        self.assertTrue(g.freeze(s, s.decision).execute)
        same_edge = self.permissive(s, sequence=2, issued_at=11)
        self.assertFalse(g.receive(same_edge, 12))

    def test_applied_not_issued_time_controls_first_eligible_decision(self):
        s = self.optional_at(4_000_000_000)
        g = Gate(self.p)
        cmd = self.permissive(s, issued_at=0, apply_by=s.decision+10)
        self.assertTrue(g.receive(cmd, s.decision+1))
        # A late-arriving lease may affect later slots, never a past decision.
        self.assertTrue(g.freeze(s, s.decision).execute)

    def test_protected_new_command_cannot_reduce_hardware_loss_hold(self):
        s = self.optional_at(4_000_000_000)
        g = Gate(self.p)
        g.loss(s.decision-10)
        fresh = self.permissive(s, issued_at=s.decision-9, holdM=0)
        self.assertTrue(g.receive(fresh, s.decision-8))
        self.assertTrue(g.freeze(s, s.decision).execute)

    def test_ERR_overflow_never_wraps_and_cannot_be_cleared_by_lease(self):
        s = self.optional_at(3_000_000_000)
        g = Gate(self.p)
        g.err_count = U64
        g.err(1)
        self.assertEqual(g.err_count, U64)
        self.assertTrue(g.err_overflow)
        g.receive(self.permissive(s), 2)
        self.assertTrue(g.freeze(s, s.decision).execute)

    def test_good_window_overlap_three_records(self):
        r = self.fresh(5)
        self.assertEqual(r.low, (self.p.deadline(0), 5*self.p.stride+self.p.lease))
        self.assertEqual([x[0] for x in r.snapshots], [3, 4, 5])

    def test_threshold_223_224_and_loss_correction(self):
        for count, loss, result in ((223, 0, "LOW"), (224, 0, "alarm"),
                                     (223, 1, "alarm"), (222, 1, "LOW")):
            r = Rule(self.p)
            r.epoch_begin(1, 0, self.p.config_id)
            self.assertEqual(r.message(packet(self.p, count=count, loss_upper=loss),
                                       self.p.deadline(0)), result)

    def test_unknown_quality_overflow_saturation_and_bad_times(self):
        bad = [dict(count=None), dict(loss_upper=None), dict(live_ticks=None),
               dict(calibration_ok=False), dict(clock_ok=False), dict(integrity_ok=False),
               dict(loss_contract_ok=False), dict(complete=False), dict(overflow=True),
               dict(saturation=True), dict(reset=True), dict(selftest_bad=True),
               dict(start=1), dict(end=self.p.window-1), dict(config_id="unknown"),
               dict(count=-1), dict(count=U64, loss_upper=1), dict(count=True)]
        for change in bad:
            with self.subTest(change=change):
                r = Rule(self.p)
                r.epoch_begin(1, 0, self.p.config_id)
                self.assertEqual(r.message(packet(self.p, **change), self.p.deadline(0)), "alarm")
                self.assertIsNone(r.low)

    def test_early_wait_late_no_LOW(self):
        r = Rule(self.p)
        r.epoch_begin(1, 0, self.p.config_id)
        d = self.p.deadline(0)
        self.assertEqual(r.message(packet(self.p), d-1), "buffer_until_deadline")
        self.assertEqual(r.last_index, -1)
        self.assertEqual(r.message(packet(self.p), d+1), "alarm")
        self.assertFalse(r.timing_valid)

    def test_duplicate_and_reordering_cannot_extend_or_resample(self):
        r = self.fresh(1)
        before = (r.low, r.last_index, tuple(r.snapshots))
        for index in (0, 1):
            self.assertEqual(r.message(packet(self.p, index), r.now), "duplicate_or_reordered")
        self.assertEqual((r.low, r.last_index, tuple(r.snapshots)), before)
        r.message(packet(self.p, 2, count=224), self.p.deadline(2))
        self.assertEqual(r.message(packet(self.p, 2, count=0), r.now), "duplicate_or_reordered")
        self.assertIsNone(r.low)

    def test_loss_recovery_uses_original_index_and_full_fresh_epoch(self):
        r = self.fresh(2)
        cert = r.lifetime_certificate
        reset = r.now + 1
        r.epoch_begin(2, reset, self.p.config_id)
        # Window3 starts before reset, so cannot repair the missing coverage.
        self.assertEqual(r.message(packet(self.p, 3, epoch=2), self.p.deadline(3)), "alarm")
        i = (reset + self.p.stride - 1) // self.p.stride
        self.assertEqual(r.message(packet(self.p, i, epoch=2), self.p.deadline(i)), "LOW")
        self.assertEqual(r.lifetime_certificate, cert)
        self.assertEqual(r.last_index, i)
        self.assertGreater(r.low[0], self.p.deadline(2))
        self.assertFalse(r.epoch_begin(1, r.now, self.p.config_id))

    def test_gap_and_missing_clear_only_working_LOW(self):
        r = self.fresh(2)
        r.err(r.now)
        holdE, cert = r.holdE, r.lifetime_certificate
        r.missing(3, self.p.deadline(3))
        self.assertIsNone(r.low)
        self.assertEqual((r.holdE, r.lifetime_certificate), (holdE, cert))
        self.assertEqual(r.message(packet(self.p, 5), self.p.deadline(5)), "LOW")
        self.assertEqual(r.low[0], self.p.deadline(5))
        self.assertGreater(r.holdM, r.now)

    def test_ERR_preserves_LOW_and_independent_hold(self):
        r = self.fresh(2)
        old, hm = r.low, r.holdM
        r.err(r.now)
        self.assertEqual((r.low, r.holdM), (old, hm))
        self.assertEqual(r.holdE, r.now + self.p.hold)

    def test_heartbeat_does_not_renew_freshness(self):
        r = self.fresh(4)
        a, b = r.permission(r.now), r.permission(r.now+1)
        self.assertEqual(a.valid_until, b.valid_until)
        self.assertEqual(a.low_right, b.low_right)

    def test_clock_rollback_and_range_fail_closed(self):
        r = self.fresh(1)
        with self.assertRaises(ValueError):
            r.err(r.now-1)
        self.assertIsNone(r.low)
        self.assertFalse(r.timing_valid)
        with self.assertRaises(ValueError):
            Calendar(self.p).slot(U64)

    def test_small_model_all_skip_masks_keep_mandatory_and_phase(self):
        p = replace(self.p, W=8, ka=3)
        skipped = 0
        for mask in itertools.product((False, True), repeat=8):
            gate, c = Gate(p), Calendar(p)
            exe = Executor(p, gate)
            for j in range(16):
                s = c.slot(j)
                a = self.permissive(s, sequence=j+1, force_S=not mask[j % 8])
                gate.receive(a, 0)
                d = gate.freeze(s, max(0, s.decision))
                exe.start(d, s.start)
                if d.execute:
                    exe.latch(s.start+48, j)
                    exe.finish(s.fence)
                self.assertEqual(exe.j, j+1)
                if s.initial or s.mandatory:
                    self.assertTrue(d.execute)
                if not d.execute:
                    skipped += 1
        self.assertGreater(skipped, 0)

    def test_delayed_exit_needs_past_radius_and_hold(self):
        r, p = self.fresh(0), self.p
        g = Gate(p)
        self.assertTrue(g.receive(r.permission(r.now), r.now))
        early = self.optional_at(r.now)
        later = self.optional_at(r.now + p.Ps)
        self.assertTrue(g.freeze(early, early.decision).execute)
        self.assertFalse(g.freeze(later, later.decision).execute)
        g.err(later.decision)
        s = self.optional_at(later.start+1000)
        self.assertTrue(g.freeze(s, s.decision).execute)

    def test_return_after_loss_no_retroactive_revocation(self):
        r, p = self.fresh(4), self.p
        g = Gate(p)
        g.receive(r.permission(r.now), r.now)
        s = self.optional_at(r.now)
        committed = g.freeze(s, s.decision)
        self.assertFalse(committed.execute)
        g.loss(s.decision+1)
        r.loss(s.decision+1)
        self.assertIs(g.freeze(s, s.start), committed)
        after = self.optional_at(s.start+1000)
        self.assertTrue(g.freeze(after, after.decision).execute)
        cert = r.lifetime_certificate
        r.message(packet(p, 5), p.deadline(5))
        g.receive(r.permission(r.now), r.now)
        held = self.optional_at(r.now)
        self.assertTrue(g.freeze(held, held.decision).execute)
        r.message(packet(p, 6), p.deadline(6))
        g.receive(r.permission(r.now), r.now)
        recovered = self.optional_at(max(r.now, r.holdM))
        self.assertFalse(g.freeze(recovered, recovered.decision).execute)
        self.assertEqual(r.lifetime_certificate, cert)

    def test_write_before_scrub_is_the_image_read_by_scrub(self):
        p = replace(self.p, W=8, ka=3)
        g, c = Gate(p), Calendar(p)
        e = Executor(p, g, functional_writes=True)
        for j in (0, 1):
            s = c.slot(j)
            e.start(g.freeze(s, max(0, s.decision)), s.start)
            e.latch(s.start+48, 1)
            e.finish(s.fence)
        target = c.slot(2)
        self.assertTrue(e.write(target.word, 99, 200, 45, target.start))
        e.application_finish(245)
        e.start(g.freeze(target, target.decision), target.start)
        e.latch(target.start+48, e.values[target.word])
        e.finish(target.fence)
        self.assertEqual(e.values[target.word], 99)

    def test_committed_skip_allows_crossing_application_write_W8(self):
        p, c, g, e, s, d = self.small_committed_skip()
        self.assertEqual((c.slot(7).fence, s.decision, s.start, c.slot(9).start),
                         (1040, 1064, 1120, 1220))
        self.assertTrue(c.slot(9).mandatory)
        self.assertTrue(e.write(s.word, 99, 1100, 44, c.slot(9).start))
        accepted = e.app_pending
        self.assertEqual(accepted, (s.word, 99, 1144))
        e.start(d, s.start)
        self.assertEqual(e.j, 9)
        self.assertTrue(e.service_valid)
        self.assertIs(e.app_pending, accepted)
        self.assertIsNone(e.busy)
        self.assertIsNone(e.pending)
        self.assertEqual(e.values[s.word], 0)  # Not committed early at skip.
        e.application_finish(1144)
        self.assertEqual((e.values[s.word], e.versions[s.word], e.j), (99, 1, 9))
        self.assertIsNone(e.app_pending)
        self.assertEqual([x for x in e.trace if x[0] == "skip"],
                         [("skip", 8, 1120, s.word)])
        self.assertTrue(e.service_valid)
        self.assertFalse(e.probability_scope)

    def test_committed_skip_crossing_write_survives_ERR_and_loss(self):
        for events in (("ERR",), ("loss",), ("ERR", "loss")):
            with self.subTest(events=events):
                p, c, g, e, s, d = self.small_committed_skip()
                self.assertTrue(e.write(s.word, 99, 1100, 44, c.slot(9).start))
                accepted = e.app_pending
                if "ERR" in events:
                    g.err(1104)
                if "loss" in events:
                    g.loss(1108)
                self.assertIs(g.freeze(s, s.start), d)
                self.assertFalse(d.execute)
                e.start(d, s.start)
                self.assertEqual(e.j, 9)
                self.assertIs(e.app_pending, accepted)
                e.application_finish(1144)
                self.assertEqual((e.values[s.word], e.versions[s.word], e.j),
                                 (99, 1, 9))
                # Slot 9 is mandatory; slot 10 demonstrates the alarm effect
                # on a not-yet-frozen OPTIONAL decision, independently per input.
                n = c.slot(9)
                e.start(g.freeze(n, n.decision), n.start)
                e.latch(n.start + 48, 0)
                e.finish(n.fence)
                after = c.slot(10)
                self.assertFalse(after.initial or after.mandatory)
                later = g.freeze(after, after.decision)
                self.assertTrue(later.execute)
                self.assertEqual(later.reason, "default_S")
                e.start(later, after.start)
                e.latch(after.start + 48, 0)
                e.finish(after.fence)
                self.assertEqual(e.j, 11)
                self.assertEqual(e.values[s.word], 99)
                self.assertTrue(e.service_valid)
                self.assertFalse(e.probability_scope)

    def test_committed_skip_crossing_write_at_working_W_local_state(self):
        p, r = self.p, self.fresh(4)
        c, g = Calendar(p), Gate(p)
        self.assertEqual((p.W, p.ka), (524288, 367))
        self.assertEqual(r.now, 4_100_011_001)
        self.assertTrue(g.receive(r.permission(r.now), r.now))
        e = Executor(p, g, functional_writes=True)
        # Declared local precondition, not a simulated 29-million-slot prefix:
        # original j/phase retained, all earlier commitments completed, bus
        # idle after previous fence, no repair/application pending; this word
        # stores zero with version zero. The five full diagnostic windows
        # above establish the actual Rule/Gate state, not an all-covering LOW.
        e.j = 29_285_794
        s = c.slot(e.j)
        e.values[s.word], e.versions[s.word] = 0, 0
        self.assertIsNone(e.busy)
        self.assertIsNone(e.pending)
        self.assertIsNone(e.app_pending)
        self.assertEqual((c.slot(s.j-1).fence, s.decision, s.start,
                          c.slot(s.j+1).start),
                         (4_100_011_080, 4_100_011_104, 4_100_011_160,
                          4_100_011_260))
        d = g.freeze(s, s.decision)
        self.assertFalse(d.execute)
        self.assertTrue(e.write(s.word, 99, 4_100_011_140, 44,
                                c.slot(s.j+1).start))
        accepted = e.app_pending
        self.assertEqual(accepted, (s.word, 99, 4_100_011_184))
        e.start(d, s.start)
        self.assertEqual(e.j, s.j+1)
        self.assertIs(e.app_pending, accepted)
        self.assertEqual(e.values[s.word], 0)
        e.application_finish(4_100_011_184)
        self.assertEqual((e.values[s.word], e.versions[s.word], e.j),
                         (99, 1, s.j+1))
        self.assertTrue(e.service_valid)
        self.assertFalse(e.probability_scope)

    def test_skip_calendar_guards_and_executed_U_write_lock(self):
        # Advancing a skip still validates the complete slot and exact phase.
        for bad in ("j", "word", "start", "decision", "fence", "time", "busy", "duplicate"):
            with self.subTest(bad=bad):
                p, c, g, e, s, d = self.small_committed_skip()
                self.assertTrue(e.write(s.word, 99, 1100, 44, c.slot(9).start))
                accepted = e.app_pending
                now = s.start
                if bad == "time":
                    now += 4
                elif bad == "busy":
                    e.busy = c.slot(7)  # Inject an unfinished real U.
                    e.pending = (e.busy.word, 0, 0)
                elif bad == "duplicate":
                    e.start(d, now)
                else:
                    d = replace(d, slot=replace(s, **{bad: getattr(s, bad)+1}))
                before_j, before_trace = e.j, list(e.trace)
                with self.assertRaises(ValueError):
                    e.start(d, now)
                self.assertEqual(e.j, before_j)
                self.assertEqual(e.trace, before_trace)
                self.assertIs(e.app_pending, accepted)
                self.assertFalse(e.service_valid)

        p, c, g, e, s, d = self.small_committed_skip()
        e.start(d, s.start)
        n = c.slot(9)
        real = g.freeze(n, n.decision)
        self.assertTrue(real.execute)
        self.assertFalse(e.write(n.word, 99, 1200, 44, n.start))
        self.assertIsNone(e.app_pending)
        # Deliberately supply an incorrect next_reserved: start must detect
        # the caller's illegal overlap even if the write was already accepted.
        self.assertTrue(e.write(n.word, 99, 1200, 44, c.slot(10).start))
        accepted = e.app_pending
        with self.assertRaises(ValueError):
            e.start(real, n.start)
        self.assertEqual(e.j, 9)
        self.assertIs(e.app_pending, accepted)
        self.assertIsNone(e.busy)
        self.assertFalse(e.service_valid)

        # The opposite order stays locked: a new write cannot enter an active
        # U; injected version drift must never permit the older repair commit.
        g, s = Gate(p), c.slot(0)
        e = Executor(p, g, functional_writes=True)
        e.start(g.freeze(s, 0), 0)
        e.latch(48, 1)
        self.assertFalse(e.write(s.word, 99, 49, 44, c.slot(2).start))
        e.values[s.word], e.versions[s.word] = 99, 1  # Deliberate lock violation.
        with self.assertRaises(AssertionError):
            e.finish(s.fence)
        self.assertEqual(e.values[s.word], 99)

    def test_pending_write_drains_on_monitor_or_program_reset(self):
        for event in ("loss", "program_reset"):
            g = Gate(self.p)
            e = Executor(self.p, g)
            s = Calendar(self.p).slot(0)
            e.start(g.freeze(s, 0), 0)
            e.latch(48, 123, err=True)
            if event == "loss":
                g.loss(49)
            else:
                e.program_reset(49)
            self.assertIsNotNone(e.pending)
            e.finish(100)
            self.assertEqual((e.values[0], e.j, g.err_count), (123, 1, 1))

    def test_unconditional_write_even_zero_ERR(self):
        g, s = Gate(self.p), Calendar(self.p).slot(0)
        e = Executor(self.p, g)
        e.start(g.freeze(s, 0), 0)
        e.latch(48, 7, err=False)
        e.finish(100)
        self.assertEqual(e.values[0], 7)
        self.assertEqual(g.err_count, 0)

    def test_repeated_ERR_is_not_a_new_parent_counter(self):
        g = Gate(self.p)
        g.err(100)
        g.err(200)
        self.assertEqual(g.err_count, 2)  # observations only, parent count unknowable
        self.assertEqual(g.holdE, 200+self.p.hold)

    def test_lost_clock_invalidates_not_new_K0(self):
        g, s = Gate(self.p), Calendar(self.p).slot(0)
        e = Executor(self.p, g)
        e.start(g.freeze(s, 0), 0)
        e.latch(48, 17)
        e.clock_reset(49)
        e.finish(100)
        self.assertFalse(e.service_valid)
        self.assertEqual(e.j, 1)

    def test_hidden_failure_continues_mask_and_cost(self):
        p = replace(self.p, W=8, ka=3)
        g, c = Gate(p), Calendar(p)
        e = Executor(p, g)
        e.hidden_failure = True
        for j in range(8):
            s = c.slot(j)
            e.start(g.freeze(s, max(0, s.decision)), s.start)
            e.latch(s.start+48, 0)
            e.finish(s.fence, qualified=False)
        self.assertEqual(len([x for x in e.trace if x[0] == "fence"]), 8)
        self.assertFalse(e.service_valid)

    def test_missing_latch_or_shifted_fence_rejected(self):
        for kind in ("latch", "fence"):
            g, s = Gate(self.p), Calendar(self.p).slot(0)
            e = Executor(self.p, g)
            e.start(g.freeze(s, 0), 0)
            if kind == "fence":
                e.latch(48, 0)
            with self.assertRaises(ValueError):
                e.finish(101 if kind == "fence" else 100)

    def test_read_only_rejects_application_write(self):
        e = Executor(self.p, Gate(self.p))
        self.assertFalse(e.write(0, 5, 200, 45, 280))
        self.assertTrue(e.probability_scope)

    def test_write_offer_during_pending_is_not_accepted(self):
        g, s = Gate(self.p), Calendar(self.p).slot(0)
        e = Executor(self.p, g, functional_writes=True)
        e.start(g.freeze(s, 0), 0)
        e.latch(48, 1)
        self.assertFalse(e.write(0, 2, 49, 45, 100))
        e.finish(100)
        self.assertTrue(e.write(0, 2, 200, 45, 280))
        self.assertEqual(e.values[0], 1)
        e.application_finish(245)
        self.assertEqual(e.values[0], 2)
        self.assertFalse(e.probability_scope)

    def test_old_pending_counterexample_is_detected(self):
        g, s = Gate(self.p), Calendar(self.p).slot(0)
        e = Executor(self.p, g, functional_writes=True)
        e.start(g.freeze(s, 0), 0)
        e.latch(48, 1)
        # Fault injection deliberately violates lock, modelling the rejected design.
        e.values[0], e.versions[0] = 2, 1
        with self.assertRaises(AssertionError):
            e.finish(100)

    def test_CPU_priority_only_when_request_fits(self):
        self.assertTrue(can_grant(200, 45, 280))
        self.assertTrue(can_grant(235, 45, 280))
        self.assertFalse(can_grant(236, 45, 280))
        trace = fifo_grants([(99, 45, "cpu"), (99, 40, "X")], [(0, 200), (280, 480)])
        self.assertEqual(trace[0], ("cpu", 99, 200, 245))
        self.assertEqual(trace[1], ("X", 99, 480, 520))

    def test_unbounded_absolute_CPU_priority_counterexample(self):
        self.assertFalse(can_grant(0, 45, 0))
        # An absolute-priority grant at0 would end45, missing mandatory s0=0.
        self.assertGreater(45, Calendar(self.p).slot(0).start)

    def test_sliding_window_exact_all_small_phase_edges(self):
        # Independent direct occupancy integration, fractional window and phase.
        p, b = F(280), F(200)
        for length in (F(1, 2), F(79), F(200), F(280), F(421), F(1000)):
            phases = {F(0), b, (b-length) % p, (-length) % p}
            measured = []
            for phase in phases:
                total = sum(max(F(0), min(phase+length, k*p+b)-max(phase,k*p))
                            for k in range(-1, 8))
                measured.append(total)
            self.assertEqual(max(measured), mask_max(length, p, b))

    def test_resource_bound_with_X_and_margin(self):
        r = resource_bounds(self.row)
        self.assertLessEqual(r["peak_upper"], F(4, 5))
        self.assertGreater(r["stability_slack"], 0)
        self.assertLessEqual(r["application_delay_margin_upper_s"], F(3, 10**6))
        self.assertAlmostEqual(float(r["peak_upper"]), .7145371408, places=9)

    def test_exact_4tick_calendar_and_non_4tick_lease(self):
        report = mapping_report(self.p, self.h, self.row)
        self.assertTrue(report["calendar_exact"])
        self.assertEqual(report["post_window_required_s"], F("0.9999999999"))
        self.assertGreater(report["correct_lease_margin_s"], 0)
        self.assertLess(report["wrong_rounded_lease_margin_s"], 0)
        self.assertGreater(report["naive_rounded_45_plus_45_s"], report["joint_U_required_s"])
        for j in (0, 1, 366, 367, self.p.W, self.p.end // self.p.g):
            s = Calendar(self.p).slot(j)
            self.assertTrue(all(t % 4 == 0 for t in (s.start, s.fence, s.decision)))

    def test_actual_gate_decisions_do_not_round_LOW(self):
        s = self.optional_at(4_000_000_000)
        for tail in range(4):
            right = s.fence + self.p.Ps - tail
            g = Gate(self.p)
            g.receive(self.permissive(s, low_right=right), 0)
            self.assertEqual(g.freeze(s, s.decision).execute, tail != 0)

    def test_finite_window_family_and_integer_limits(self):
        self.assertLess(self.p.end, 1 << 59)
        self.assertLess(self.p.end // self.p.g + 2, 1 << 52)
        self.assertLess(self.p.J, 1 << 30)
        with self.assertRaises(ValueError):
            self.p.deadline(self.p.J)


if __name__ == "__main__":
    unittest.main(verbosity=2)
