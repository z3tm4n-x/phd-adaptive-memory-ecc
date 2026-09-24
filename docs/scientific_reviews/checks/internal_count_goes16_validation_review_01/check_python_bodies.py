"""Bounded execution of unchanged Python function bodies, NOT Numba/JIT.

Only the numba import and njit decorators are omitted in memory. Experiment
and test definitions are extracted without prepare.py's unused HDF5 imports.
No source file is patched; no full production matrix is rerun.
"""
import argparse, ast, csv, dataclasses, hashlib, inspect, io, json, math
import platform, subprocess, sys, types, unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
import numpy as np
from scipy.stats import beta, binom, chisquare

ROOT=Path(__file__).resolve().parents[4]
HERE=ROOT/'experiments/RE-INTERNAL-COUNT-GOES16-VALIDATION-01'
OLD=ROOT/'experiments/RE-INTERNAL-COUNT-CONTROL-01'
sys.path.insert(0,str(OLD))
import core

def load_sim():
    tree=ast.parse((OLD/'simulate.py').read_text())
    tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and n.module=='numba')]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef):node.decorator_list=[]
    module=types.ModuleType('sr_python_sim');module.__file__=str(OLD/'simulate.py')
    sys.modules[module.__name__]=module
    exec(compile(ast.fix_missing_locations(tree),str(OLD/'simulate.py'),'exec'),module.__dict__)
    for v in module.__dict__.values():
        if inspect.isfunction(v):v.py_func=v
    return module

def definitions(path,env,classes=False):
    tree=ast.parse(path.read_text())
    keep=[n for n in tree.body if isinstance(n,ast.FunctionDef) or (classes and isinstance(n,ast.ClassDef))]
    exec(compile(ast.Module(body=keep,type_ignores=[]),str(path),'exec'),env)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    sim=load_sim();env=dict(globals(),sim=sim,__name__='sr_extracted')
    env['sha']=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    cfg=json.loads((HERE/'config.json').read_text())
    env['POLICIES']=cfg['policies'];env['NAMES']=['Proposed','Count-disabled','Fixed','Precomputed','PA-DOM']
    definitions(HERE/'experiment.py',env)
    definitions(HERE/'prepare.py',env)
    definitions(HERE/'check.py',env,classes=True)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(env['Checks'])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful()
    print('Python-body unit suite done',flush=True)
    m,p,cert=env['model']();windows=json.loads((HERE/'selected_windows.json').read_text())['windows']
    # Production-linked controller check using full dense state matrices/rewards,
    # not the packed affine H/J/constant/coefficient computation in _choose.
    rng=np.random.default_rng(7319);choices=observations=0
    for remaining in [1,2,7,10,50,999,18000,36000]:
        for repeat in range(8):
            q=rng.dirichlet(np.ones(26));slack=.2
            candidates=[]
            for idx,ticks in enumerate(p.ticks):
                dt=min(remaining,int(ticks))
                if ticks>remaining:
                    first,second=core.moments(dt*p.tick,p.dwell,p.low,p.high)
                    reward=np.array([(k*first[z]+second[z]/2)/p.words for z in range(2) for k in range(13)])
                    delta=float(q@reward-q@m.value[remaining])
                else:
                    delta=float(q@(m.reward[idx]+m.transition[idx]@m.value[remaining-int(ticks)])-q@m.value[remaining])
                if delta<=slack*dt/remaining+1e-13:candidates.append(idx)
            got=sim._choose(q,slack,remaining,p.H,p.J,p.constant,p.coefficient,p.first,p.second,p.ticks,p.tick,p.words,p.dwell,p.low,p.high)
            assert got[0]==max(candidates);choices+=1
            for idx in [0,2,11]:
                for count in [0,1,32,99]:
                    for enabled in [True,False]:
                        matrix=m.kernels[idx,min(count,32)] if enabled else m.transition[idx]
                        ref=q@matrix;ref/=ref.sum()
                        actual,_=sim._observe(q,idx,count,enabled,p.kernels,p.transition)
                        np.testing.assert_allclose(actual,ref,rtol=3e-14,atol=3e-16);observations+=1
    records=[];maxdiff=0.
    for case in ['growth','peak','typical']:
        with np.load(a.data/(case+'_trials.npz'),allow_pickle=False) as archive:samples=archive['samples'];key=int(archive['utc_index'])
        w=next(w for w in windows if case in w['labels']);buf=env['buffers'](p)
        for trial in [0,1,2,19999]:
            ev=env['stream'](w['nu_array_s-1'],key,trial)
            for j,policy in enumerate(cfg['policies']):
                actual,_=env['execute'](ev,p,policy,buf)
                diff=float(np.abs(actual[:8]-samples[trial,j]).max());maxdiff=max(maxdiff,diff)
                np.testing.assert_array_equal(actual[:7],samples[trial,j,:7])
                np.testing.assert_allclose(actual[7],samples[trial,j,7],rtol=3e-12,atol=3e-12)
                records.append(dict(case=case,trial=trial,policy=j,max_abs_difference=diff))
            print(case,trial,'replayed',flush=True)
    # Fixed illustration, all exported fields, independently checked against CSV.
    w=next(w for w in windows if 'growth' in w['labels']);key=int(datetime.fromisoformat(w['utc']).timestamp())//300
    ev=env['stream'](w['nu_array_s-1'],key,0,2026091602)
    actual,tr=env['execute'](ev,p,cfg['policies'][0],record=True)
    rows=list(csv.DictReader((HERE/'outputs/growth_illustration.csv').open()))
    published=np.array([[float(v) for v in row.values()] for row in rows])
    np.testing.assert_allclose(tr,published,rtol=2e-11,atol=3e-11)
    summary=dict(status='PASS',mode='Python bodies, no Numba/JIT; original source unchanged',
       unit_tests=result.testsRun,controller_dense_choices=choices,controller_dense_observations=observations,
       policy_trial_replays=len(records),max_replay_abs_difference=maxdiff,replays=records,
       illustration_rows=len(tr),illustration_max_abs_difference=float(np.abs(tr-published).max()),certificate=cert)
    a.out.write_text(json.dumps(summary,indent=2)+'\n')

if __name__=='__main__':main()
