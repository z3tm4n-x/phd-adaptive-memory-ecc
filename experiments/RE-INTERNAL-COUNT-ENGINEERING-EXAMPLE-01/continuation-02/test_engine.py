"""Independent scheduled word/bit oracle; no production transition helpers."""
import copy, unittest
import numpy as np
from reference import packed,accepted,config,ROOT
import engine

def oracle(groups,W,period,P,H,delay):
    queue=[];step=P/W;end=period;passid=0
    while end-P<=H:
        for w in range(W):
            commit=end-P+(w+1)*step
            if commit-delay<=H:queue.append((commit-delay,2,'latch',w,passid))
            if commit<=H:queue.append((commit,0,'commit',w,passid))
        end+=period;passid+=1
    for t,marks in groups:queue.append((t,1,'group',marks,-1))
    queue.sort(key=lambda x:(x[0],x[1]))
    bits=[set() for _ in range(W)];pending=[False]*W;count={};writes=0;failed=False;stop=H
    for t,_,kind,data,passid in queue:
        if t>H:break
        if kind=='latch':pending[data]=bool(bits[data])
        elif kind=='commit':
            if pending[data]:
                bits[data].clear();writes+=1;count[passid]=count.get(passid,0)+1
            pending[data]=False
        else:
            for w,mask in data:
                for b in range(39):
                    if mask>>b&1:
                        if b in bits[w]:bits[w].remove(b)
                        else:bits[w].add(b)
            if any(len(b)>1 for b in bits):failed=True;stop=t;break
    return failed,stop,writes,count

def small_run(groups,W=4,H=1.,period=.2,delay=8e-8):
    p=copy.deepcopy(packed());p.words=W;p.pass_seconds=W*2e-7;p.horizon=H
    times=np.array([g[0] for g in groups]);ptr=np.r_[0,np.cumsum([len(g[1]) for g in groups])].astype(np.int64)
    locations=np.array([w for _,g in groups for w,m in g],np.int32)
    marks=np.array([m for _,g in groups for w,m in g],np.uint64)
    a=int(np.where(p.periods==period)[0][0])
    r,tr=engine.run(times,ptr,locations,marks,np.array([2,a,a,0.,0.,0.,0.]),accepted.args(p),delay,True)
    return r,tr,oracle(groups,W,period,p.pass_seconds,H,delay)

class Tests(unittest.TestCase):
    def assert_stream(self,groups,**kw):
        r,tr,o=small_run(groups,**kw)
        self.assertEqual(bool(r[0]),o[0]);self.assertAlmostEqual(r[1],o[1],places=12)
        self.assertEqual(r[5],o[2])
        self.assertEqual(list(tr[:,3].astype(int)),[o[3].get(i,0) for i in range(len(tr))])
    def test_atomic_toggle_not_false_failure(self):
        self.assert_stream([(0.01,[(0,1)]),(.02,[(0,3)]),(.03,[(0,2)])])
    def test_group_immediate_and_parity(self):
        self.assert_stream([(.01,[(0,(1<<32)|(1<<38))])])
    def test_repeat_and_accumulation(self):
        self.assert_stream([(.01,[(1,1)]),(.02,[(1,1)]),(.03,[(2,1)]),(.04,[(2,2)])])
    def test_latch_commit_and_boundaries(self):
        commit=.2-8e-7+2e-7;latch=commit-8e-8
        for t in [latch-1e-9,latch,latch+1e-9,commit-1e-9,commit,commit+1e-9]:
            self.assert_stream([(.01,[(0,1)]),(t,[(0,2)])])
            self.assert_stream([(t,[(0,1)]),(.21,[(0,2)])])
    def test_terminal_partial(self):
        self.assert_stream([(.01,[(3,1)]),(.21,[(3,1<<36)])],H=.3)
        self.assert_stream([(.21,[(0,1)]),(.22,[(3,1<<38)])],H=.3999997)
    def test_group_tied_to_complete_pass_counts_completed_service(self):
        r,tr,o=small_run([(1.,[(3,3)])])
        self.assertEqual(r[2],5);self.assertTrue(bool(r[0]));self.assertEqual(r[4],20)
    def test_randomized_oracle(self):
        rng=np.random.default_rng(87231)
        for i in range(100):
            t=np.sort(rng.uniform(0,1,30));g=[]
            for ti in t:
                w=int(rng.integers(4));b=int(rng.integers(39));g.append((ti,[(w,1<<b)]))
            self.assert_stream(g)
    def test_translate_preserves_xor_padding(self):
        points=np.array([16*10+2,16*18+2],np.int32);off=np.array([0,2],np.int32)
        a=[np.array([v],np.int32) for v in [0,0,7,3]]
        ptr,loc,mask=engine.translate(points,off,*a,100)
        self.assertEqual(int(loc[0]^loc[1]),10^18)
        self.assertTrue(np.all(mask==2))
        # Sentinel: independent scattering has same number of bits, violates joint XOR.
        mutant=np.array([11,25]);self.assertNotEqual(int(mutant[0]^mutant[1]),10^18)
        a[1][0]=2;a[3][0]=15
        self.assertEqual(len(engine.translate(points,off,*a,100)[1]),0)
    def test_fullword_rate_not_group_rate(self):
        import json
        m=json.loads((ROOT/'inputs/manifest.json').read_text(encoding='utf-8'));c=config()
        expected=m['raw_bits']/m['total_duration_s']*39/64
        self.assertAlmostEqual(c['environment']['b_high'],expected,places=12)
        mutant=m['groups']/m['total_duration_s']*39/64
        self.assertGreater(abs(mutant/expected-1),.1)
    def test_mapping_mutation_rejected_by_oracle(self):
        correct=[(.01,[(0,3)])]
        mutant=[(.01,[(0,1),(1,2)])]
        actual=small_run(mutant)[0]
        expected=oracle(correct,4,.2,8e-7,1.,8e-8)
        self.assertTrue(expected[0]);self.assertFalse(bool(actual[0]))
    def test_disabled_observation_invariance(self):
        p=packed()
        a=accepted._observe(p.initial,0,0,False,p.kernels,p.transition)[0]
        b=accepted._observe(p.initial,0,1000,False,p.kernels,p.transition)[0]
        np.testing.assert_array_equal(a,b)
    def test_stream_reproducible_hash(self):
        c=config();c['horizon_seconds']=2
        a=engine.stream(481,0,5,c);b=engine.stream(481,0,5,c)
        self.assertEqual(a[4],b[4]);np.testing.assert_array_equal(a[0],b[0])

if __name__=='__main__':unittest.main(verbosity=2)
