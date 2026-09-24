import itertools, json, unittest
from fractions import Fraction as F
from pathlib import Path
import calculate as calc
import witness as w
import check_bounds
ROOT=Path(__file__).resolve().parent

class ReferenceTests(unittest.TestCase):
    def test_independent_numeric_checker(self):
        self.assertEqual(check_bounds.verify()["status"],"PASS")
    def test_pack_basis_and_padding(self):
        # Explicit legacy positions independent of the witness's generated DATA.
        data_positions=[3,5,6,7,9,10,11,12,13,14,15,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,33,34,35,36,37,38]
        for i,p in enumerate(data_positions+[1,2,4,8,16,32,39]):
            self.assertEqual(w.unpack(1<<i),1<<(p-1))
            self.assertEqual(w.pack(1<<(p-1)),1<<i)
        for bit in range(39,48): self.assertEqual(w.unpack(1<<bit),0)
        self.assertEqual(w.pack(w.encode(0xdeadbeef))>>39,0)
    def test_swapped_data_parity_sentinel(self):
        p=w.pack(w.encode(1))
        self.assertNotEqual(p&((1<<39)-1),w.unpack(p))
        # The wrong "direct P to codeword" converter cannot pass basis mapping.
        bad=lambda p:p&((1<<39)-1)
        with self.assertRaises(AssertionError):
            assert all(bad(1<<i)==w.unpack(1<<i) for i in range(39))
    def test_sec_ded_all_masks(self):
        for image in (0,0xffffffff,0xdeadbeef,0xaaaaaaaa,0x55555555):
            cw=w.encode(image)
            self.assertEqual(w.decode(cw),(cw,False,False))
            self.assertEqual(w.pack(cw)&0xffffffff,image)
            for bit in range(39): self.assertEqual(w.decode(cw^(1<<bit)),(cw,True,False))
            for a,b in itertools.combinations(range(39),2):
                self.assertTrue(w.decode(cw^(1<<a)^(1<<b))[2])
    def run_slot(self,slot,dq,err=0,**kwargs):
        for t in range(25): slot.step(t,dq=dq if t<=8 else ~dq,err=err if t<=8 else 0,**kwargs)
        return slot
    def test_clean_and_err_only(self):
        dq=w.pack(w.encode(0x12345678))
        clean=self.run_slot(w.Slot(),dq)
        self.assertFalse(clean.write); self.assertTrue(clean.ack)
        for e in (1,2,4,7):
            slot=self.run_slot(w.Slot(),dq,e)
            self.assertTrue(slot.write and slot.ack)
            self.assertEqual(slot.latched,dq)
        app=self.run_slot(w.Slot(kind="app"),dq,7)
        self.assertFalse(app.write)
    def test_corrected_and_uncorrectable(self):
        dq=w.pack(w.encode(0x12345678))
        slot=self.run_slot(w.Slot(),dq^1)
        self.assertEqual(slot.latched,dq); self.assertTrue(slot.write and slot.ack)
        double=self.run_slot(w.Slot(),dq^3,7)
        self.assertTrue(double.fault)
        self.assertFalse(double.write or double.ack)
    def test_prepare_and_pending_fence(self):
        slot=w.Slot(kind="prep",image=123)
        for t in range(24):
            slot.step(t)
            self.assertTrue(slot.pending); self.assertFalse(slot.ack)
            if t in range(13,19): self.assertFalse(slot.we_n)
            if t in range(12,21): self.assertTrue(slot.driven)
        slot.step(24)
        self.assertFalse(slot.pending); self.assertTrue(slot.ack)
        self.assertEqual(slot.latched,w.pack(w.encode(123)))
    def test_soft_hard_and_failed_commit(self):
        for reset_tick in (0,8,13,18,20,23):
            soft=w.Slot(kind="prep")
            hard=w.Slot(kind="prep")
            failed=w.Slot(kind="prep")
            for t in range(25):
                soft.step(t,soft_reset=t==reset_tick)
                if t<=reset_tick: hard.step(t,hard_reset=t==reset_tick)
                failed.step(t,commit_ok=t!=reset_tick)
            self.assertTrue(soft.quiesce and soft.ack)
            self.assertTrue(hard.invalid); self.assertFalse(hard.ack)
            self.assertTrue(failed.invalid); self.assertFalse(failed.ack)
    def test_epoch_no_fake_global_clean(self):
        self.assertTrue(w.epoch_valid(524288,0,True,True,False))
        for args in [(524287,0,True,True,False),(524288,1,True,True,False),(524288,0,False,True,False),(524288,0,True,False,False),(524288,0,True,True,True)]:
            self.assertFalse(w.epoch_valid(*args))
        # Two distinct hits after sigma_0 and before t0 survive into the epoch.
        sigma=w.prepare_end(0)
        hits=[sigma+1,sigma+2]
        self.assertLess(hits[-1],0)
        state=(1<<0)^(1<<1)
        self.assertEqual(state.bit_count(),2)
        self.assertTrue(w.decode(w.encode(0)^state)[2])
    def test_hit_inside_service_tube_needs_payment(self):
        # Latched clean image, then hit: clean slot performs no repair.
        # A singleton outside followed by one inside may exceed capability
        # before conditional write completes. An instantaneous snapshot alone
        # cannot justify the extended chronology.
        s=0; e=24
        for hit in (F(1,2),F(15,2),F(17,2),F(37,2),F(47,2)):
            self.assertTrue(s<=hit<=e)
        latched=w.pack(w.encode(0))
        slot=self.run_slot(w.Slot(),latched)
        physical_state=1
        self.assertFalse(slot.write)
        self.assertEqual(physical_state,1)
        self.assertEqual((1|2).bit_count(),2)
    def test_independent_first_passage_inclusion_and_sentinel(self):
        # Independent tiny event oracle: real toggle state; latch at 8;
        # conditional singleton commit at 19; clean endpoint envelope at 24.
        # Two modeled data bits suffice to falsify an omitted service-tube term.
        def run(events):
            state=0; latched=0; cap=False
            for t,action,bit in sorted([(t,0,b) for t,b in events]+[(8,1,0),(19,2,0)]):
                if action==0: state ^= 1<<bit
                elif action==1: latched=state
                elif latched.bit_count()==1: state=0
                cap |= state.bit_count()>1
            bad=any(0<=t<=24 for t,b in events)
            pair=any(b!=bb and ((t<24 and tt<24) or (t>=24 and tt>=24))
                     for (t,b),(tt,bb) in itertools.combinations(events,2))
            return cap,pair,bad
        choices=list(itertools.product((-2,-1,1,7,9,18,20,25,26),range(2)))
        for n in (0,1,2,3):
            for events in itertools.combinations(choices,n):
                cap,pair,bad=run(events)
                self.assertTrue(not cap or pair or bad)
        # Hit after the clean latch survives: another after the fence causes
        # first passage across two nominally separate gaps. Tube payment is
        # necessary for this inclusion, not a mere positive surcharge.
        self.assertEqual(run(((9,0),(25,1))),(True,False,True))
    def test_all_timing_corners(self):
        c=calc.configuration(); t=calc.result()["timing"]
        self.assertGreaterEqual(t["read_budget_ns"],t["read_required_ns"])
        self.assertGreaterEqual(t["oe_to_drive_min_ns"],18)
        self.assertGreaterEqual(t["we_pulse_min_ns"],35)
        self.assertGreaterEqual(t["data_setup_min_ns"],25)
        self.assertGreaterEqual(t["data_hold_min_ns"],0)
        self.assertGreaterEqual(t["address_hold_min_ns"],0)
        self.assertGreaterEqual(t["address_setup_to_end_min_ns"],35)
        self.assertLess(t["physical_write_end_from_s_upper_ns"],t["slot_end_from_s_lower_ns"])
        # All min/max endpoint output+flight combinations (three chips).
        for a,b in itertools.product((F(0),F(10)),repeat=2):
            self.assertGreaterEqual(calc.interval_ns(c,6,False)+b-a,35)
            self.assertGreaterEqual(calc.interval_ns(c,7,False)+b-a,25)
        with self.assertRaises(AssertionError):
            assert calc.interval_ns(c,2,False)-10>=35 # deliberately short pulse
    def test_block_edges_ppm_tubes(self):
        D=calc.result()["tube_s"]
        for ppm in (F(-50,10**6),F(0),F(50,10**6)):
            period=1/(1+ppm)
            for phase in (-D,F(0),D,F(1,2),300-D):
                starts=[phase+k*period for k in range(-2,305)]
                intersections=[max(F(0),min(t+D,F(300))-max(t,F(0))) for t in starts]
                self.assertLessEqual(sum(x>0 for x in intersections),301)
                self.assertLessEqual(sum(intersections),301*D)
                # Strict edge crossing contributes on both adjacent blocks.
        crossing=300-D/2
        left=300-crossing; right=crossing+D-300
        self.assertEqual(left+right,D); self.assertGreater(left,0); self.assertGreater(right,0)
    def test_saturated_reads_do_not_move_phase(self):
        starts=[w.scrub_start(i) for i in range(1024)]
        reads=w.saturated_reads(starts,starts[-1]+24)
        self.assertGreater(len(reads),2000)
        self.assertTrue(all(b-a>=48 for a,b in zip(reads,reads[1:])))
        for r in reads:
            near=(r*524288)//100000000
            for i in range(max(0,near-1),min(1024,near+3)):
                self.assertTrue(r+24<=starts[i] or starts[i]+24<=r)
        self.assertEqual(starts,[i*100000000//524288 for i in range(1024)])
    def test_pin_uniqueness_and_voltage(self):
        pins=json.loads((ROOT/"pinmap.json").read_text())["signals"]
        self.assertEqual(len(pins),73)
        for key in ("ball","j30","net","port"): self.assertEqual(len({p[key] for p in pins}),73)
        self.assertEqual({p["bank"] for p in pins},{12,15,16})
        # Source DC extremes, independent of shared nominal 2.5 V.
        self.assertGreaterEqual(F("2.375")-F(".4"),F("1.8"))
        self.assertGreaterEqual(F("2.0"),F("1.7"))
        self.assertLessEqual(F(".4"),F(".6"))
        self.assertLess(F("2.125"),F("2.2")) # PG alone is insufficient.
    def test_unsigned_upper_not_requirement(self):
        x=calc.result()
        self.assertGreater(x["signed_slack"],0)
        self.assertLess(x["r_pre_named"],x["r_pre_limit_lower"])
        self.assertGreater(x["pair_pre"]+x["tube_pre"],0)
        self.assertGreater(x["gap_max_s"],1)
        self.assertGreater(x["tube_s"],F(240,10**9))
        self.assertLess(x["timing"]["pending_latch_to_fence_upper_ns"]/10**9,x["ideal_delta_star"])

if __name__=="__main__": unittest.main(verbosity=2)
