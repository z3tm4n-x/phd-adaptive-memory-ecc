import unittest
from check import Memory,Request,exact_peak

class MemoryTests(unittest.TestCase):
    def test_all_38_positions_and_repeated_inversion(self):
        for bit in range(38):
            m=Memory();m.toggle(7,bit,1);m.begin(0,Request(0,7),10)
            self.assertEqual(m.sample(0,0,70),(m.value(7)&65535,1))
            m.toggle(7,bit,72)
            self.assertEqual(m.mask(7),0)
            self.assertIsNone(m.first_exceedance)
    def test_post_start_error_is_not_free_clean(self):
        m=Memory();m.toggle(3,35,1);m.begin(0,Request(0,3),10);m.sample(0,0,70)
        m.toggle(3,35,71);m.toggle(3,35,72)
        m.write(0,0,m.value(3)&65535,3,142);m.release(0,158)
        self.assertEqual(m.mask(3),1<<35)
    def test_absorbing_exceedance(self):
        m=Memory();m.toggle(5,0,1);m.toggle(5,37,2);m.toggle(5,37,3)
        self.assertEqual(m.first_exceedance,2)
    def test_read_does_not_clean(self):
        m=Memory();m.toggle(9,32,1);m.begin(0,Request(1,9),10)
        m.sample(0,0,70);m.sample(0,1,162);m.release(0,194)
        self.assertEqual(m.mask(9),1<<32)
    def test_partial_write_preserves_other_bytes(self):
        m=Memory();old=m.value(9);m.begin(0,Request(2,9,0x12345678,4),10)
        m.sample(0,0,70);m.write(0,0,old&65535,3,142)
        m.write(0,1,0x1234,1,210);m.release(0,226)
        self.assertEqual(m.value(9),(old&~0xff0000)|0x340000)
    def test_lock_and_unobserved_write_rejected(self):
        m=Memory();m.begin(0,Request(2,9),10)
        with self.assertRaises(AssertionError):m.begin(1,Request(0,10),12)
        with self.assertRaises(AssertionError):m.write(0,0,0,3,142)
    def test_exact_sliding_window(self):
        spans=[(0,4,'a'),(7,10,'a'),(13,18,'a')]
        got,_=exact_peak(spans,0,20,10)
        want=max(sum(max(0,min(b,s+10)-max(a,s)) for a,b,k in spans)/10 for s in range(11))
        self.assertEqual(got,want)

if __name__=='__main__':unittest.main()
