"""Negative and cost tests for the whole-top clean-case accelerator."""
import bisect
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from check_accel import HERE,check,compare_short,window_peak

class AccelTests(unittest.TestCase):
    def test_peak_against_fully_expanded_pulses(self):
        # A mixed price trace, independent of the transfer algorithm.
        h=2600000;blocks=[(120,752760,False),(1129080,2258040,True)]
        all_pulses=[];explicit=[]
        for frame in range(h//1568+1):
            for k in range(8):
                a=frame*1568+k*164;b=min(h,a+92)
                if a>=h:continue
                block=next((x for x in blocks if x[0]<=a<x[1]),None)
                if block and block[2] and (frame*8+k)%3:continue
                all_pulses.append((a,b))
                if not block:explicit.append((a,b))
        ends=[b for a,b in all_pulses];prefix=[0]
        for a,b in all_pulses:prefix.append(prefix[-1]+b-a)
        def integral(t):
            i=bisect.bisect_right(ends,t)
            return prefix[i]+(max(0,t-all_pulses[i][0]) if i<len(ends) else 0)
        for width in (1000000,376320,4704):
            points={0,h-width}
            for a,b in all_pulses:points.update((a,b,a-width,b-width))
            literal=max((integral(t+width)-integral(t),-t) for t in points if 0<=t<=h-width)
            self.assertEqual(window_peak(explicit,blocks,h,width),(literal[0],-literal[1]))

    def corrupt(self,stem,edit):
        path=HERE/f'outputs/{stem}.trace.gz'
        with gzip.open(path,'rt') as f:lines=f.readlines()
        self.assertTrue(edit(lines),'mutation not exercised')
        meta=json.loads((HERE/f'outputs/{stem}.json').read_text())
        root=HERE/'.build';root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='mutant-',dir=root) as d:
            bad=Path(d)/'bad.trace.gz'
            with gzip.open(bad,'wt') as f:f.writelines(lines)
            with self.assertRaisesRegex(AssertionError,r'bad.trace.gz:\d+:'):
                check(bad,meta)

    def test_wrong_address_transfer(self):
        def edit(lines):
            seen=False
            for i,line in enumerate(lines):
                f=line.split()
                if f[0]=='JUMP':seen=True
                elif seen and f[0]=='SLOT':
                    f[4]=f'{int(f[4],16)^1:x}';lines[i]=' '.join(f)+'\n';return True
        self.corrupt('accel-short-adaptive-skip',edit)

    def test_lost_empty_packet_sequence(self):
        def edit(lines):
            for i,line in enumerate(lines):
                f=line.split()
                if f[0]=='JUMP':
                    f[7]=f'{int(f[7],16)-1:x}';lines[i]=' '.join(f)+'\n';return True
        self.corrupt('accel-short-adaptive-skip',edit)

    def test_dropped_err(self):
        def edit(lines):
            for i,line in enumerate(lines):
                if line.startswith('EVENT '):lines.pop(i);return True
        self.corrupt('accel-quiet-adaptive-skip',edit)

    def test_early_low(self):
        def edit(lines):
            for i,line in enumerate(lines):
                f=line.split()
                if f[0]=='PERMISSION' and f[3]=='1':
                    f[1]=str(int(f[1])-1000000);lines[i]=' '.join(f)+'\n';return True
        self.corrupt('accel-lowprobe-adaptive-skip',edit)

    def test_lost_same_edge_veto(self):
        def edit(lines):
            for i,line in enumerate(lines):
                f=line.split()
                if f[0]=='PERMISSION' and f[2:5]==['0','1','1']:
                    lines.pop(i);return True
        self.corrupt('accel-loss-adaptive-skip',edit)

    def test_modified_frozen_bit(self):
        def edit(lines):
            for i,line in enumerate(lines):
                f=line.split()
                if f[0]=='FREEZE' and f[3]=='1' and f[5]=='0':
                    f[3]='0';lines[i]=' '.join(f)+'\n';return True
        self.corrupt('accel-lowprobe-adaptive-skip',edit)

    def test_literal_tails(self):
        for case,base in (('short','literal'),('lowprobe','no-low')):
            result=compare_short(HERE/f'outputs/accel-{case}-adaptive-{base}.trace.gz',
                                 HERE/f'outputs/accel-{case}-adaptive-skip.trace.gz')
            self.assertGreater(result['compared_rows'],50000)

if __name__=='__main__':unittest.main()
