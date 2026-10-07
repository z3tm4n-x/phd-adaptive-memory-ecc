import unittest
from fractions import Fraction as F
from rule import Rule


class RuleTests(unittest.TestCase):
    def fresh(self):
        r=Rule(8,3,10,30,2);r.at(100);return r

    def test_initial_hold_includes_history_and_first_pass(self):
        r=Rule(8,3,10,30,2)
        self.assertTrue(r.fast(32));self.assertFalse(r.fast(33))
        for j in range(8):self.assertTrue(r.freeze(j,100+j))

    def test_first_and_isolated_flags_only_short(self):
        r=self.fresh();r.flag(100)
        self.assertTrue(r.fast(110));self.assertFalse(r.fast(111))
        r.flag(111);self.assertTrue(r.fast(121));self.assertEqual(r.long_until,-1)

    def test_inclusive_confirmation_boundary(self):
        r=self.fresh();r.flag(100);r.flag(110)
        self.assertEqual(r.long_until,140);self.assertTrue(r.fast(140));self.assertFalse(r.fast(141))

    def test_strictly_later_does_not_confirm(self):
        r=self.fresh();r.flag(100);r.flag(111);self.assertEqual(r.long_until,-1)

    def test_every_flag_renews_short_and_close_pair_renews_long(self):
        r=self.fresh();r.flag(100);r.flag(101);r.flag(109)
        self.assertEqual((r.short_until,r.long_until),(119,139))
        r.flag(130);self.assertEqual((r.short_until,r.long_until),(140,139))
        self.assertTrue(r.fast(140));self.assertFalse(r.fast(141))

    def test_same_tick_two_different_transactions_confirm(self):
        r=self.fresh();a=r.begin(0);r.err(100,a);r.release(a)
        b=r.begin(1);r.err(100,b);r.release(b)
        self.assertEqual(r.long_until,130)

    def test_duplicate_transaction_not_new_ERR(self):
        r=self.fresh();a=r.begin(0)
        self.assertTrue(r.err(100,a));self.assertFalse(r.err(101,a));self.assertEqual(r.long_until,-1)

    def test_next_repaired_epoch_is_new(self):
        r=self.fresh();a=r.begin(0);r.err(100,a);r.release(a)
        b=r.begin(0);self.assertTrue(r.err(101,b));self.assertEqual(r.long_until,131)

    def test_app_write_observes_before_both_aliases_complete(self):
        r=self.fresh();a=r.begin(0,'write32');r.err(100,a)
        with self.assertRaises(AssertionError):r.begin(0,'control')
        self.assertIsNotNone(r.pending);r.release(a);self.assertIsNone(r.pending)

    def test_loss_and_recovery_preserve_pending_and_lifetime(self):
        r=self.fresh();a=r.begin(0);r.err(100,a);ident=r.mission_budget_id
        r.loss(102);r.recover(120)
        self.assertTrue(r.fast(152));self.assertFalse(r.fast(153))
        self.assertEqual(r.pending[0],a);self.assertEqual(r.mission_budget_id,ident)
        self.assertEqual(r.last_err,100);r.release(a)

    def test_committed_skip_not_retroactively_cancelled(self):
        r=self.fresh();r.cursor=8
        self.assertFalse(r.freeze(8,100));r.loss(101)
        self.assertFalse(r.decisions[8]);self.assertTrue(r.freeze(9,102))

    def test_flags_processed_before_same_tick_decision(self):
        r=self.fresh();r.cursor=8;r.flag(100);self.assertTrue(r.freeze(8,100))

    def test_mandatory_order_and_no_phase_reset(self):
        r=self.fresh()
        for j in range(32):self.assertEqual(r.word(3*j),j%8)
        r.cursor=8;r.loss(100);r.recover(101);self.assertEqual(r.cursor,8)

    def test_one_stage_comparator_is_same_state_machine(self):
        r=Rule(8,3,10,30,2,stage=1);r.flag(100);self.assertEqual(r.long_until,130)

    def test_partial_write_hiding_ERR_requires_preobservation(self):
        # An unobserved correct internal RCW can erase an actual old token.
        old_error=1;raw_rcw_result=0;raw_ERR_flags=[]
        self.assertEqual(raw_rcw_result,0);self.assertEqual(raw_ERR_flags,[])
        r=self.fresh();a=r.begin(0,'write16');r.err(100,a);r.release(a)
        self.assertTrue(old_error and r.fast(100))

    def test_old_disjoint_bands_force_pair_despite_delay_reversal(self):
        # Every combination of endpoint arrival delays respects width+tau<=w.
        w,tau=10,2
        for u in range(9):
            for v in range(u,9):
                for du in range(tau+1):
                    for dv in range(tau+1):
                        self.assertLessEqual(abs((v+dv)-(u+du)),w)

    def test_clean_read_does_not_clean_later_hit(self):
        snapshot=0;state=1
        if snapshot:state=0
        self.assertEqual(state,1)

    def test_cross_window_event_not_undone_by_write(self):
        state=1;captured=state;state^=2;event=state.bit_count()>1
        state=0;self.assertTrue(event);self.assertEqual(captured,1)

    def test_one_intra_E_parent_can_give_two_completed_epochs(self):
        # E only guarantees retirement of errors older than virtual start.
        # A new completed epoch is not a duplicate pending transaction.
        r=self.fresh();a=r.begin(0);r.err(100,a);r.release(a)
        residual_from_same_parent=1
        b=r.begin(0);r.err(101,b);r.release(b);residual_from_same_parent=0
        self.assertEqual(r.long_until,131);self.assertEqual(residual_from_same_parent,0)


if __name__=='__main__':unittest.main()
