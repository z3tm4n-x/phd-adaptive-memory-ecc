"""Independent physical/event and numerical-input checks; no production trials."""
import argparse, dataclasses, inspect, json, math, sys, unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
import numpy as np
from scipy.stats import binom, chisquare
from experiment import core,sim,model,execute,stream,event_hash,cp,eb,gain_interval,fixed300,POLICIES,HERE
from prepare import load_g16,select_windows,sha,dump

def oracle(events,p,policy):
    """Explicit all-word chronology. Does NOT call production physical update.

    Shared dependency: controller _choose/_observe/_analog_next and its tables.
    Oracle owns masks, scan times, toggles, counts, first passage, pass accounting.
    """
    kind,first_a,second_a,ms,cap,growth,zero=policy
    q=p.initial.copy();slack=p.slack;state=[set() for _ in range(p.words)]
    ticks=0;idx=0;passes=0;trace=[];previous=-1
    if kind==4:
        rate=(p.low+p.high)/2;mm=1+2*p.words*ms/(rate*p.horizon)
        raw=p.horizon*mm*(mm-1)/(2*ms*p.words)
        action=max(i for i,x in enumerate(p.periods) if x<=max(p.periods[0],min(raw,cap))+1e-12)
    else:action=first_a
    while ticks<round(p.horizon/p.tick):
        t=ticks*p.tick;remain=round(p.horizon/p.tick)-ticks
        if kind<=1:action,slack,*_=sim._choose(q,slack,remain,p.H,p.J,p.constant,p.coefficient,p.first,p.second,p.ticks,p.tick,p.words,p.dwell,p.low,p.high)
        if kind==2:action=first_a
        if kind==3:action=first_a if t<p.horizon/2-1e-10 else second_a
        end=t+p.periods[action];start=end-p.pass_seconds;count=0
        timeline=[(start+(w+1)*p.pass_seconds/p.words,0,w,-1) for w in range(p.words) if start+(w+1)*p.pass_seconds/p.words<=min(end,p.horizon)]
        while idx<len(events[0]) and events[0][idx]<min(end,p.horizon)-1e-12:
            timeline.append((float(events[0][idx]),1,int(events[1][idx]),int(events[2][idx])));idx+=1
        for at,typ,w,b in sorted(timeline):
            if typ==0:
                count+=bool(state[w]);state[w].clear()
            else:
                if b in state[w]:state[w].remove(b)
                else:state[w].add(b)
                if len(state[w])>=2:return True,at,passes,trace
        if end>p.horizon+1e-10:break
        passes+=1;trace.append((t,p.periods[action],end,count,sum(bool(x) for x in state)))
        ticks+=p.ticks[action]
        if kind<=1 and ticks<round(p.horizon/p.tick):q,_=sim._observe(q,action,count,kind==0,p.kernels,p.transition)
        if kind==4 and ticks<round(p.horizon/p.tick):
            action=sim._analog_next(count,previous,action,ms,cap,growth,zero,p.periods,p.words,p.horizon);previous=count
    return False,p.horizon,passes,trace

def events(rows):
    return (np.array([r[0] for r in rows],float),np.array([r[1] for r in rows],np.int32),np.array([r[2] for r in rows],np.int8))
class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg=core.load_config();cfg['memory']['words']=4;cfg['horizon_seconds']=6;cfg['environment']['b_low']=.04;cfg['environment']['b_high']=.45
        cls.p=sim.pack(core.build_model(cfg,3,False),.99)
    def compare(self,ev,pol,p=None):
        p=p or self.p;r,tr=execute(ev,p,pol,record=True);o=oracle(ev,p,pol)
        self.assertEqual(bool(r[0]),o[0]);self.assertAlmostEqual(r[5],o[1],places=11);self.assertEqual(int(r[1]),o[2])
        np.testing.assert_allclose(tr[:,[0,1,2,3,16]],np.array(o[3]).reshape(-1,5),rtol=0,atol=1e-12)
    def test_deterministic_physics(self):
        pol=POLICIES[2];reset=1-self.p.pass_seconds+self.p.pass_seconds/4
        cases=[[],[(.1,0,1)],[(.1,0,1),(.2,0,1)],[(.1,0,1),(.2,0,2),(.3,0,2)],
             [(.1,0,1),(reset-1e-7,0,2)],[ (.1,0,1),(reset,0,2)],[(.1,0,1),(reset+1e-7,0,2)],
             [(reset+1e-7,0,1),(1.01,0,2)],[(.1,0,1),(1.,0,2)],[(5.99,0,1)]]
        for rows in cases:
            with self.subTest(rows=rows):self.compare(events(rows),pol)
        self.assertEqual(execute(events([(.1,0,1),(.2,0,1)]),self.p,pol)[0][0],0)
        self.assertEqual(execute(events([(.1,0,1),(.2,0,2)]),self.p,pol)[0][0],1)
    def test_terminal_partial(self):
        p=dataclasses.replace(self.p,horizon=2.1);pol=[2,3,3,0,0,0,0]
        # Next 2-second pass is beyond H; terminal arrivals must still accumulate.
        self.compare(events([(2.02,0,1),(2.09,0,2)]),pol,p)
        p=dataclasses.replace(self.p,horizon=2.1);pol=[2,0,0,0,0,0,0]
        self.compare(events([(2.02,0,1),(2.08,3,2)]),pol,p)
    def test_bounded_random_oracle(self):
        r=np.random.default_rng(314159)
        for i in range(80):
            n=r.poisson(3);ev=events(sorted(zip(r.uniform(0,6,n),r.integers(0,4,n),r.integers(0,32,n))))
            for pol in POLICIES:self.compare(ev,pol)
    def test_wrong_mapping_sentinel(self):
        ev=events([(.1,0,0),(.2,1,1)])
        bad=(ev[0],np.zeros(2,np.int32),ev[2])
        self.assertFalse(oracle(ev,self.p,POLICIES[2])[0]);self.assertEqual(execute(bad,self.p,POLICIES[2])[0][0],1)
    def test_count_disabled(self):
        q=self.p.initial
        for a in range(len(self.p.periods)):
            ref=q@self.p.transition[a];ref/=ref.sum()
            for c in [0,1,32,999]:np.testing.assert_allclose(sim._observe(q,a,c,False,self.p.kernels,self.p.transition)[0],ref,rtol=1e-14,atol=1e-16)
    def test_interface_and_failures(self):
        for f in [sim._choose,sim._observe]:
            args=list(inspect.signature(f.py_func).parameters)
            for forbidden in ['times','locations','eventbits','bitstate','window','utc','rates','failure','active_n']:self.assertNotIn(forbidden,args)
        k=np.zeros_like(self.p.kernels)
        with self.assertRaises(ValueError):sim._observe(self.p.initial,0,0,True,k,self.p.transition)
        with self.assertRaises(ValueError):sim._choose(self.p.initial,-100,60,self.p.H,self.p.J,self.p.constant,self.p.coefficient,self.p.first,self.p.second,self.p.ticks,self.p.tick,self.p.words,self.p.dwell,self.p.low,self.p.high)
    def test_stream_distribution(self):
        rates=np.array([.01,.02]*6);ev=[stream(rates,1234,i,seed=8871,words=16,bits=4) for i in range(4000)]
        counts=np.array([len(x[0]) for x in ev]);mu=300*sum(rates)
        self.assertLess(abs(counts.mean()-mu),6*np.sqrt(mu/len(ev)))
        self.assertLess(abs(counts.var(ddof=1)-mu),6*mu*np.sqrt(2/(len(ev)-1)))
        for pos,size in [(1,16),(2,4)]:
            hist=np.bincount(np.concatenate([x[pos] for x in ev]),minlength=size)
            self.assertGreater(chisquare(hist).pvalue,1e-6)
        expected=[event_hash(stream(rates,1234,i,seed=8871)) for i in range(10)]
        self.assertEqual(expected,[event_hash(stream(rates,1234,i,seed=8871)) for chunk in [range(3),range(3,10)] for i in chunk])
        for x in ev[:20]:self.assertTrue(np.all(np.diff(x[0])>=0));self.assertTrue(np.all((x[0]>=0)&(x[0]<3600)))
    def test_statistics(self):
        lo,hi=cp(0,20000);self.assertEqual(lo,0);self.assertAlmostEqual((1-hi)**20000,.025,places=12)
        for k in [1,10,100]:
            lo,hi=cp(k,20000);self.assertAlmostEqual(binom.sf(k-1,20000,lo),.025,places=10);self.assertAlmostEqual(binom.cdf(k,20000,hi),.025,places=10)
        x=np.full(20000,100.);lo,hi=eb(x);self.assertLess(lo,100);self.assertGreater(hi,100)
        l,u=gain_interval(x,2*x);self.assertLess(l,.5);self.assertGreater(u,.5)
    def test_window_selection(self):
        t=[datetime(2024,1,1,tzinfo=timezone.utc)+timedelta(seconds=i*300) for i in range(24)]
        wins,n=select_windows(t,np.ones(24));self.assertEqual(n,13);self.assertEqual(wins[0]['index'],0);self.assertEqual(wins[-1]['index'],6)
        nu=np.ones(24);nu[11]=np.nan
        wins,n=select_windows(t,nu);self.assertEqual(n,1);self.assertEqual(wins[0]['index'],12)
    def test_original_floor(self):model()
    def test_fixed300_gaps(self):
        W=524288;P=.18874368;delta=P*np.arange(W)/W
        for rates in [np.ones(12)*.2,np.array([.01,.3]*6)]:
            # Explicitly enumerate actual check gaps, independently of moments.
            ss=(rates[0]*(300-delta))**2+(rates[-1]*delta)**2
            for k in range(1,12):ss+=(rates[k-1]*delta+rates[k]*(300-delta))**2
            direct=31/(64*W*W)*sum(ss)
            self.assertAlmostEqual(direct,fixed300(rates)['upper'],places=13)

def input_checks(raw,cache):
    g,q=load_g16(raw)
    with np.load(cache/'spectral_check.npz') as archive:z={k:archive[k] for k in archive.files}
    maxrel=0
    # Independent nested scalar trapezoidal sum, not shared trap_weights/matmul.
    for i in [0,157,732,753,1439]:
        for d in range(2):
            e=z['energy'];inp=4*math.pi*(z['J'][i,d]+z['L'][i,d]);out=[]
            for row in range(len(e)):
                out.append(math.fsum(float((z['primary'][row,k]+z['secondary'][row,k])*inp[k]) for k in range(len(e))))
            direct=math.fsum((e[k+1]-e[k])*(out[k]*z['sigma'][k]+out[k+1]*z['sigma'][k+1])/2 for k in range(len(e)-1))
            from sigma_model import load_experimental_points,sigma_hat
            hi=float(sigma_hat([600],load_experimental_points(HERE.parent/'RE-CY62167-PROTON-01/sigma_bit_experimental.csv'))[0])
            direct+=4*math.pi*(z['gap'][i,d]+z['p11'][i,d])*hi
            maxrel=max(maxrel,abs(direct/z['perbit'][i,d]-1));assert abs(direct/z['perbit'][i,d]-1)<2e-13
    # Raw native/per-MeV and explicit sensor swap are verified independently.
    import h5py,csv
    with h5py.File(raw/'sci_sgps-l2-avg5m_g16_d20241008_v3-0-2.nc') as f:
        for d,sensor in [(0,1),(1,0)]:np.testing.assert_array_equal(g.flux[0,d],np.asarray(f['AvgDiffProtonFlux'][0,sensor],float)*1000)
    rows=list(csv.DictReader((HERE/'derived_rates.csv').open()))
    for i,r in enumerate(rows):
        a=float(r['lambda_bit_E_s_1']);b=float(r['lambda_bit_W_s_1']);nu=float(r['nu_array_s_1'])
        assert math.isclose(nu,(a+b)/2*16777216,rel_tol=2e-15)
        assert (datetime.fromisoformat(r['end_utc'])-datetime.fromisoformat(r['timestamp_utc'])).total_seconds()==300
    frozen=json.loads((HERE/'selected_windows.json').read_text());nu=np.array([float(r['nu_array_s_1']) for r in rows])
    # Independent Python window enumeration, no select_windows helper.
    candidates=[]
    for i in range(1429):
        x=nu[i:i+12]
        if all(math.isfinite(v) and v>=0 for v in x):candidates.append((i,300*sum(x),300*(sum(x[6:])-sum(x[:6]))))
    expected=[max(candidates,key=lambda z:(z[2],-z[0]))[0],max(candidates,key=lambda z:(z[1],-z[0]))[0],sorted(candidates,key=lambda z:(z[1],z[0]))[(len(candidates)-1)//2][0]]
    assert expected==[next(w['index'] for w in frozen['windows'] if label in w['labels']) for label in ['growth','peak','typical']]
    return dict(spectral_rows_checked=10,max_relative_convolution_error=maxrel,raw_units_and_direction_check=True,array_normalization_rows=1440,time_bins=1440,independent_selected_indices=expected)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path);ap.add_argument('--cache',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    data=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),success=result.wasSuccessful())
    if a.raw:data['input']=input_checks(a.raw,a.cache)
    _,_,data['certificate']=model();dump(a.out,data)
    sys.exit(0 if result.wasSuccessful() else 1)
