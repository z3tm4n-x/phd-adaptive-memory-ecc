"""Production-linked Python-body checks; explicitly not a Numba/JIT rerun.

Run with --package in an isolated exact-target checkout. Original files are
unchanged. The in-memory numba stub leaves function bodies unchanged.
"""
import argparse, copy, hashlib, importlib, json, math, sys, types, unittest
from pathlib import Path
import numpy as np

def install_python_numba():
    module=types.ModuleType('numba')
    def njit(*args,**kwargs):
        def decorate(fn):fn.py_func=fn;return fn
        return decorate(args[0]) if args and callable(args[0]) else decorate
    module.njit=njit;sys.modules['numba']=module

def explicit_oracle(groups,W,period,P,H):
    """Dense chronological integer-bitsets and explicit bus-interval integrals.

    This uses no production advance/read_reservation/decoder helpers.
    """
    queue=[];slots=[];end=period;pid=0
    while end-P<H:
        scan=end-P
        for w in range(W):
            finish=scan+(w+1)*P/W;latch=finish-8e-8
            slots.append((finish,pid,w))
            queue.extend([(finish,0,'commit',w,pid),(latch,2,'latch',w,pid)])
        pid+=1;end=pid*period+period
    for at,marks in groups:queue.append((at,1,'group',marks,-1))
    queue.sort(key=lambda e:(e[0],e[1]));state=[0]*W;latched={};dirty=[];writes=0;counts={};failed=False;stop=H
    for at,priority,kind,value,p in queue:
        if at>H:break
        if kind=='commit':
            if latched.get((p,value),False):state[value]=0;writes+=1;counts[p]=counts.get(p,0)+1
        elif kind=='latch':
            latched[p,value]=state[value]!=0
            if state[value]:dirty.append((p,value))
        else:
            toggles={}
            for w,bits in value:toggles[w]=toggles.get(w,0)^bits
            for w,bits in toggles.items():state[w]^=bits
            if any(x.bit_count()>1 for x in state):failed=True;stop=at;break
    def covered(left,right):return max(0.,min(stop,right)-max(0.,left))
    reserved=sum(covered(c-1e-7,c) for c,_,_ in slots)
    readtime=sum(covered(c-1e-7,c-8e-8) for c,_,_ in slots)
    completed_reads=sum(c-8e-8<=stop for c,_,_ in slots)
    writebus=sum(covered(c-4e-8,c-2e-8) for c,p,w in slots if (p,w) in dirty)
    passes=sum((p+1)*period<=stop for p in range(pid))
    return dict(failed=failed,stop=stop,writes=writes,counts=counts,reservation=reserved,bus=readtime+writebus,reads=completed_reads,passes=passes)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    install_python_numba();sys.path.insert(0,str(args.package));ref=importlib.import_module('reference');engine=importlib.import_module('engine');tests=importlib.import_module('test_engine')
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(tests.Tests)
    legacy=args.package.parent;sys.path.insert(0,str(legacy));oldtests=importlib.import_module('test_prerequisites')
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(oldtests.Prerequisites))
    outcome=unittest.TextTestRunner(verbosity=2).run(suite);assert outcome.wasSuccessful()
    p=ref.packed();small=copy.deepcopy(p);small.words=4;small.pass_seconds=8e-7;small.horizon=.6
    a=int(np.flatnonzero(small.periods==.2)[0]);policy=np.array([2,a,a,0.,0.,0.,0.]);fixtures=[]
    # Every bit, dirty/clean latch, same/different hit; exact and adjacent times.
    commit=.2-small.pass_seconds+2e-7;latch=commit-8e-8
    for bit in range(39):
        for at in [latch-1e-9,latch,latch+1e-9,commit-3e-8,commit-1e-9,commit,commit+1e-9]:
            for marks in [1<<bit,(1<<bit)|(1<<((bit+1)%39))]:
                fixtures.append([(.01,[(0,1<<bit)]),(at,[(0,marks)])])
    # Full-pass ties, simultaneous multiword marks, stop within a write, parity.
    fixtures.extend([[ (.6,[(3,3)])],[(.01,[(0,1)]),(commit-3e-8,[(1,3)])],[(.01,[(0,1<<38)]),(.02,[(0,(1<<38)|1),(1,1<<32)])]])
    maximum=0.
    for groups in fixtures:
        times=np.array([g[0] for g in groups]);ptr=np.r_[0,np.cumsum([len(g[1]) for g in groups])].astype(np.int64)
        loc=np.array([w for _,marks in groups for w,m in marks],np.int32);mask=np.array([m for _,marks in groups for w,m in marks],np.uint64)
        r,trace=engine.run(times,ptr,loc,mask,policy,ref.accepted.args(small),8e-8,True)
        o=explicit_oracle(groups,4,.2,8e-7,.6)
        for value,expected in [(r[0],o['failed']),(r[1],o['stop']),(r[5],o['writes']),(r[4],o['reads'])]:assert value==expected,(groups,value,expected)
        assert list(trace[:,3])==[o['counts'].get(i,0) for i in range(len(trace))]
        for value,expected in [(r[6],o['bus']),(r[7],o['reservation'])]:
            maximum=max(maximum,abs(value-expected));assert abs(value-expected)<2e-15,(value,expected)
    print('Independent explicit executor fixtures',len(fixtures),'PASS',flush=True)
    cfg=ref.config();m=ref.core.build_model(cfg,60,cache=False);fresh=ref.accepted.pack(m,.1)
    max_table=0.
    for key in p.__dataclass_fields__:
        x,y=getattr(p,key),getattr(fresh,key)
        if isinstance(x,np.ndarray):max_table=max(max_table,float(np.max(np.abs(x-y))));np.testing.assert_allclose(x,y,rtol=2e-10,atol=3e-12)
        else:assert math.isclose(x,y,rel_tol=2e-10,abs_tol=3e-12)
    print('Reference tables rebuilt and compared',flush=True)
    # Author numerical checker: shared tables, independent expression/ODE.
    numerics=importlib.import_module('check_numerics');numerics.main()
    # Short bounded full-scale replay: 1 fixed seed per case, all five policies.
    records=[]
    for case,name in enumerate(cfg['cases']):
        with np.load(args.package/'outputs'/('test_'+name+'.npz')) as z:
            expected=z['rows'][0];policies=z['policies'];h=z['event_sha256'][0].decode();counts=z['stream_counts'][0]
        s=engine.stream(cfg['simulation']['validation_seed'],case,0,cfg);assert s[4]==h and s[6]==counts[0] and len(s[2])==counts[1]
        for j,policy in enumerate(policies):
            r,trace=engine.run(*s[:4],policy,ref.accepted.args(p),8e-8)
            np.testing.assert_allclose(r,expected[j],rtol=3e-11,atol=3e-9)
            for k in [0,2,4,5,8,9,11]:assert r[k]==expected[j,k]
            records.append({'case':name,'policy':j,'max_abs_difference':float(np.max(np.abs(r-expected[j])))})
        print(name,'5 policy replays PASS',flush=True)
    result=dict(mode='Python bodies, no JIT; no source modification',unit_tests=outcome.testsRun,independent_executor_fixtures=len(fixtures),max_resource_difference=maximum,reference_table_max_abs_difference=max_table,replays=records,numerics=json.loads((args.package/'outputs/numerical_checks.json').read_text()),status='PASS')
    args.out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
