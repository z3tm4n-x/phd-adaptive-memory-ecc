"""Long-profile plumbing checks, not additional scientific scenarios."""
import ctypes as C
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from burst_run_inputs import HERE,build
from trace_codec import pack,digest
from burst_price import Ledger,integral


class BurstRunTests(unittest.TestCase):
    def test_integral_against_direct_slots(self):
        for low in (False,True):
            pulses=[((j//8)*1568+(j%8)*164,(j//8)*1568+(j%8)*164+92)
                    for j in range(250) if not low or j%3==0]
            for t in range(0,40000,13):
                self.assertEqual(integral(t,low),sum(max(0,min(b,t)-a) for a,b in pulses))

    def test_peak_against_direct_sum(self):
        import random
        rng=random.Random(106)
        for case in range(16):
            ledger=Ledger();pulses=[]
            for j in range(150):
                a=(j//8)*1568+(j%8)*164
                if rng.randrange(3)==0:continue
                b=a+(148 if rng.randrange(8)==0 else 92)
                pulses.append((a,b));ledger.explicit(a,b)
            h=32000;width=1017+case*137
            candidates={0,h-width}
            for a,b in pulses:
                candidates.update(x for x in (a,b,a-width,b-width) if 0<=x<=h-width)
            expected=max((sum(max(0,min(b,x+width)-max(a,x)) for a,b in pulses),-x) for x in candidates)
            got=ledger.peak(h,width)
            self.assertEqual(got,(expected[0],-expected[1]))
            self.assertEqual(ledger.total,sum(b-a for a,b in pulses))

    def test_price_rejects_overlap(self):
        ledger=Ledger();ledger.explicit(0,92)
        with self.assertRaises(AssertionError):ledger.explicit(64,156)

    def test_large_block_lossless_and_truncation(self):
        import burst_codec as c
        src=HERE/'outputs/sparse-short-adaptive-skip.trace.ctz'
        with tempfile.TemporaryDirectory(dir=HERE/'.build') as d:
            dest=Path(d)/'trial.ct3'
            report=c.pack(src,dest)
            self.assertEqual(report['raw_sha256'],digest(src))
            self.assertEqual(c.digest(dest),digest(src))
            dest.write_bytes(dest.read_bytes()[:-1])
            with self.assertRaises(ValueError):list(c.lines(dest))

    def test_fixed_full_input(self):
        a=build()
        self.assertEqual(a['horizon_ns'],363900_000_000_000)
        self.assertEqual(len(a['injections']),5237)
        self.assertEqual(a['applications'],[])
        self.assertNotIn('pilot_only',a)

    def test_prefix_preserves_original_epochs(self):
        a,b=build(),build(pilot_events=20)
        self.assertTrue(b['pilot_only'])
        self.assertEqual(b['injections'],[e for e in a['injections'] if e['at_ns']<b['horizon_ns']])
        self.assertEqual(a['injections'][0],b['injections'][0])
        self.assertGreater(b['horizon_ns'],2**32*20)
        with self.assertRaises(AssertionError):build(pilot_events=5237)

    @unittest.skipUnless(hasattr(os,'mkfifo') and os.name=='posix','Linux FIFO')
    def test_stream_lossless(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);pipe=d/'pipe';os.mkfifo(pipe)
            src=HERE/'outputs/sparse-short-adaptive-skip.trace.ctz'
            from trace_codec import lines
            errors=[]
            def send():
                try:
                    with pipe.open('w') as f:f.writelines(lines(src))
                except BaseException as e:errors.append(e)
            thread=threading.Thread(target=send);thread.start()
            pack(pipe,d/'stream.ctz');thread.join()
            self.assertFalse(errors)
            self.assertEqual((d/'stream.ctz').read_bytes(),src.read_bytes())

    @unittest.skipUnless(shutil.which('gcc') and os.name=='posix','Linux C bridge')
    def test_unsigned_64bit_tick_wire(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);so=d/'bridge.so'
            subprocess.run(['gcc','-shared','-fPIC','-Wall','-Wextra','-Werror',
                str(HERE/'bridge_burst.c'),'-o',str(so)],check=True)
            server=socket.socket(socket.AF_UNIX);server.bind(str(d/'rpc'));server.listen(1)
            prior=os.environ.get('T106_SOCKET');os.environ['T106_SOCKET']=str(d/'rpc')
            # Each new temporary shared library has its own static socket.
            lib=C.CDLL(str(so));lib.system_reply.argtypes=[C.c_int,C.c_int,C.c_uint64]
            values=[C.c_int() for _ in range(4)]
            received=[];errors=[]
            def peer():
                try:
                    conn,_=server.accept()
                    with conn:
                        conn.sendall(b'6 0 0 0\n')
                        for _ in range(4):
                            line=b''
                            while not line.endswith(b'\n'):line+=conn.recv(1)
                            received.append(line.decode().split())
                except BaseException as e:errors.append(e)
            thread=threading.Thread(target=peer);thread.start()
            try:
                lib.system_next(*[C.byref(v) for v in values])
                for tick in (2**31+7,2**32+9,363900_000_000_000//20,2**64-1):
                    lib.system_reply(0,0,tick)
                thread.join(timeout=10)
                self.assertFalse(thread.is_alive());self.assertFalse(errors)
                self.assertEqual([int(x[2]) for x in received],
                    [2**31+7,2**32+9,363900_000_000_000//20,2**64-1])
            finally:
                server.close()
                if prior is None:os.environ.pop('T106_SOCKET',None)
                else:os.environ['T106_SOCKET']=prior

if __name__=='__main__':unittest.main()
