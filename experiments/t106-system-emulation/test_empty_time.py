import dataclasses
import random
import unittest
from empty_time import EmptyGuard, WORDS, integrate, peak, skip, first_slot, slot


def literal(a, b, low, words):
    # Deliberately ordinary slot enumeration and interval overlap, no residue
    # functions from the accelerator. This can operate far along the mission.
    first = max(0, (a//1568-1)*8)
    last = (b//1568+1)*8
    spans = [(1568*(j//8)+164*(j%8), 1568*(j//8)+164*(j%8)+92)
             for j in range(first, last)
             if not low or j < words or j % 3 == 0]
    return {'occupied_ns': sum(max(0, min(y,b)-max(x,a)) for x,y in spans),
            'started': sum(a<=x<b for x,y in spans),
            'completed': sum(a<y<=b for x,y in spans),
            'partial_begin': sum(x<a<y for x,y in spans),
            'partial_end': sum(x<b<y for x,y in spans)}


class EmptyTimeTests(unittest.TestCase):
    def test_all_integer_phases_and_partial_release(self):
        for low in (False, True):
            for words in (8, 524288):
                for a in range(4704):
                    for length in (1, 91, 92, 93):
                        self.assertEqual(integrate(a,a+length,low,words), literal(a,a+length,low,words))

    def test_random_far_from_origin_and_warmup(self):
        rng=random.Random(10620261015)
        for _ in range(1000):
            a=rng.choice((0, slot(WORDS), 180310097920, (1<<48)))-rng.randrange(4704)
            a=max(0,a);b=a+rng.randrange(1,20000)
            low=bool(rng.randrange(2))
            self.assertEqual(integrate(a,b,low),literal(a,b,low,WORDS))

    def test_inverse(self):
        for t in range(15000):
            j=first_slot(t)
            self.assertGreaterEqual(slot(j),t)
            if j:self.assertLess(slot(j-1),t)

    def test_peak_every_integer_phase(self):
        for words in (8,64):
            for low in (False,True):
                for a,b,width in ((0,6000,1000),(1200,15000,6000),(9000,18000,1200)):
                    values=[(literal(t,t+width,low,words)['occupied_ns'],-t) for t in range(a,b-width+1)]
                    expected=max(values)
                    got=peak(a,b,width,low,words)
                    self.assertEqual((got['occupied_ns'],-got['window_start_ns']),expected)

    def test_period_and_full_warmup(self):
        # Independent counting: W clean reads and a steady LOW period of24
        # slots containing8 reads. Large times must not enter float math.
        self.assertEqual(integrate(0,slot(WORDS),True)['completed'],WORDS)
        a=slot(WORDS+24-(WORDS%24))
        self.assertEqual(integrate(a,a+4704*1000000000,True)['occupied_ns'],8*92*1000000000)
        self.assertEqual(integrate(a,a+4704*1000000000,False)['occupied_ns'],24*92*1000000000)

    def test_guard_rejects_unknown_dirty_pending_events(self):
        g=EmptyGuard(True,0,0,0,True,True,None,None)
        skip(1500,3068,g)
        for name,value in [('clean',False),('clean',None),('pending_operations',1),
                ('pending_applications',1),('pending_cdc',1),('permit_stable',False),
                ('frozen_prefix_settled',False),('next_external_ns',2000),('next_rule_boundary_ns',2000)]:
            with self.assertRaises(ValueError):skip(1500,3068,dataclasses.replace(g,**{name:value}))
        with self.assertRaises(ValueError):skip(1500,1600,g)

    def test_mutants_are_detected(self):
        reference=literal(0,10000,True,WORDS)
        self.assertNotEqual(integrate(0,10000,True,2),reference) # missing warmup
        self.assertNotEqual(integrate(1,93,False),literal(0,92,False,WORDS)) # phase shift
        result=integrate(0,91,False)
        self.assertNotEqual(result['started'],result['completed']) # free drain


if __name__=='__main__':unittest.main()
