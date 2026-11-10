"""Independent chronological word-by-word reference and directed edge cases."""
from random import Random
import unittest

import numpy as np

from histories import D, DT, T, W, WIDTH, Profile
from replay import Calendar, decode, simulate
from risk import pair_upper, triangle


def stepped(marks, adaptive, end, cal):
    memory = [0]*cal.words
    i = 0
    failure = pending = None
    started = full = issued = reads = writes = partial = fast_time = 0
    sticky = invalid = invalid_cells = zeros = 0
    fast = True
    command_start = command_fast = 0
    switches, returns, records = [], [], []
    def births_before(limit):
        nonlocal i,failure
        while i < len(marks) and marks[i][0] < min(limit,end):
            t,one,b1,two,b2 = marks[i]
            memory[one] ^= 1<<b1
            memory[two] ^= 1<<b2
            if failure is None and max(memory[one].bit_count(),memory[two].bit_count()) > 1:
                failure = t
            i += 1
    for m in range((end-1)//cal.L+1):
        step = (1 if fast else 32) if adaptive else 4
        if m % step:
            continue
        started += 1
        in_pass = 0
        last_release = None
        for pos in range(cal.words):
            w = 3*pos % cal.words
            start = m*cal.L+1568*(pos//8)+164*(pos%8)
            if start >= end:
                break
            births_before(start)
            snapshot = memory[w]
            corrected,repair,due = decode(snapshot)
            release = start+68+56*repair
            in_pass += 1
            reads += 1
            writes += repair
            births_before(release)
            if release <= end:
                memory[w] ^= corrected^snapshot
                if failure is None and memory[w].bit_count() > 1:
                    failure = release
                sticky += repair
                invalid |= due
                if repair:
                    records.append((w,start,release))
            else:
                pending = [w,start,release]
            last_release = release
        if in_pass == cal.words and last_release <= end:
            full += 1
        else:
            partial = in_pass
        decision = m*cal.L+cal.drain
        issued += int(decision <= end)
        if m % 32 == 0:
            births_before(decision)
            if m and decision < end:
                invalid_cells += bool(invalid)
                zeros = 0 if invalid or sticky else min(zeros+1,cal.quiet)
                new_fast = zeros < cal.quiet
                if adaptive and new_fast != fast:
                    if fast:
                        command_fast += decision-command_start
                    command_start = decision
                    fast = new_fast
                    switches.append((m//32,fast,"invalid" if invalid else "correction" if sticky else "quiet"))
                    if fast:
                        returns.append((m//32,records.copy()))
            sticky = invalid = 0
            records.clear()
        if adaptive and fast:
            fast_time += min(cal.L,end-m*cal.L)
    births_before(end)
    assert i == len(marks)
    if adaptive and fast:
        command_fast += end-command_start
    return (dict(started_passes=started,complete_passes=full,public_passes=issued,
                 word_reads=reads,repair_writes=writes,protection_bus_ns=48*reads+56*writes,
                 fast_ns=fast_time if adaptive else None,fast_command_ns=command_fast if adaptive else None,
                 terminal_pending=pending,
                 terminal_partial_reads=partial,first_weight_above_one_ns=failure,
                 invalid_cells=invalid_cells),
            switches,returns,{w:mask for w,mask in enumerate(memory) if mask})


class ReplayChecks(unittest.TestCase):
    def compare(self,marks,end,c):
        marks = sorted(marks,key=lambda m:m[0])
        for adaptive in (False,True):
            got,sw,log,state = simulate(marks,adaptive,end,c)
            want,sw0,log0,state0 = stepped(marks,adaptive,end,c)
            self.assertEqual({k:got[k] for k in want},want)
            self.assertEqual((sw,log,state),(sw0,log0,state0))
        return simulate(marks,True,end,c)

    def test_registered_threshold(self):
        c = Calendar(8,730)
        t = 731*c.P+c.q(3)
        got,sw,_,_ = self.compare([(t,3,1,6,2)],734*c.P,c)
        self.assertEqual(sw[:2],[(730,False,"quiet"),(731,True,"correction")])
        self.assertEqual(got["repair_writes"],2)

    def test_two_publications_and_terminal_edges(self):
        c = Calendar(16,3)
        marks = [(4*c.P+c.q(3),3,2,6,1)]
        for offset in (-1,0,1,68,100,124,164,c.drain-1,c.drain,c.drain+1,c.L):
            self.compare(marks,5*c.P+offset,c)
        _,_,returns,_ = self.compare(marks,6*c.P,c)
        self.assertEqual([w for w,_,_ in returns[0][1]],[6])

    def test_pending_cancel_due_and_continuation(self):
        c = Calendar(16,2)
        a = 4*c.P
        marks = [(a-25,0,0,3,5),(a+20,0,1,3,6),(a+124,0,1,3,6),
                 (a+130,0,3,3,3),(a+143,0,4,3,4),(9*c.P+7,0,4,3,4)]
        for end in (a+80,a+124,a+165,9*c.P,14*c.P):
            self.compare([m for m in marks if m[0]<end],end,c)
        got,_,_,_ = self.compare(marks,14*c.P,c)
        self.assertEqual(got["first_weight_above_one_ns"],a+20)
        self.assertGreater(got["invalid_cells"],0)

    def test_dense_and_empty(self):
        c = Calendar(16,3)
        end = 25*c.P+171
        rng = Random(436)
        m = []
        for _ in range(130):
            a,b = rng.sample(range(c.words),2)
            m.append((rng.randrange(end),a,rng.randrange(39),b,rng.randrange(39)))
        self.compare(m,end,c)
        for cut in (1,c.drain,c.L,c.P,4*c.P+c.drain,18*c.P+123):
            self.compare([],cut,c)

    def test_full_bank_phase_and_partial_pass(self):
        c = Calendar()
        self.compare([(100,0,1,3,2),(c.L+50,0,2,65533,1)],c.L+112,c)

    def test_pair_geometry_and_crossing(self):
        self.assertEqual(triangle(.4,.1,.2),.1*.2)
        self.assertAlmostEqual(triangle(.2,.5,.6),.02)
        edges = np.arange(WIDTH+1,dtype=float)*DT
        rate = np.full(WIDTH,.001)
        group = np.zeros(WIDTH,dtype=np.uint8)
        group[WIDTH//2:] = 1
        profile = Profile("test","",edges,rate,rate,group,{})
        q = pair_upper(profile)
        c = Calendar()
        h = (4*c.L+124)/1e9
        factor = W*(39/D)**2*rate[0]**2
        self.assertAlmostEqual(q["4L"]["total"]/(factor*h*(T-h/2)),1,places=7)
        self.assertAlmostEqual(q["4L"]["different_groups"]/(factor*h*h/2),1,places=7)
        self.assertEqual(q["4L"]["earlier_by_later"][1][0],0)
        self.assertLess(q["L/32L"]["total"],factor*(32*c.L+124)/1e9*T)
        # One missing piece shorter than h. Pairs can cross both boundaries.
        mid = WIDTH//2
        ends = np.insert(edges,mid+1,edges[mid]+h/3)
        groups = np.insert(group,mid,2)
        rates = np.full(len(groups),rate[0])
        pieces = pair_upper(Profile("test","",ends,rates,rates,groups,{}))["4L"]
        width = ends[mid+1]-ends[mid]
        self.assertAlmostEqual(pieces["earlier_by_later"][0][1]/(factor*(h-width)**2/2),1,places=7)


if __name__ == "__main__":
    unittest.main(verbosity=2)
