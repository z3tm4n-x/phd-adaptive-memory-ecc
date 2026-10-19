"""Stage 2 training, deterministic replay and bounded engineering benchmark.

Run from any cwd. Only stage2 outputs are written; accepted stage1 is read.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from bounds import calculate
from checks import validate
from engine import run
from policies import make,NS
from scenarios import generate,save,digest,dumps,benchmark_marks
from training import fit
from resources import calculate as resource_bounds

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REL=HERE.relative_to(ROOT).as_posix()


def norm_hash(raw):
    return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()


def git_bytes(ref,path):
    return subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=ROOT)


def verify_provenance():
    p=json.loads((HERE/'provenance.json').read_text(encoding='utf-8'))
    for entry in p['working_dependencies']:
        assert norm_hash((ROOT/entry['path']).read_bytes())==entry['sha256'],('working dependency',entry['path'])
    for entry in p['documentary_snapshots']:
        assert norm_hash(git_bytes(entry['commit'],entry['path']))==entry['sha256'],('git snapshot',entry['path'])
    return dict(working_dependencies=len(p['working_dependencies']),documentary_snapshots=len(p['documentary_snapshots']),
                live_organization_files_read=False)


def training_result(cfg,write=False):
    history={};datahash={};deliveryhash={}
    for ep in cfg['episodes']:
        if ep['split']!='train': continue
        data=generate(ep,cfg)
        path=HERE/'data'/f"{ep['id']}.json"
        if write:
            save(path,data)
        else:
            assert json.loads(path.read_text(encoding='utf-8'))==data,('training input',ep['id'])
        r=run(data['horizon_ns'],data['marks'],data['applications'],make(dict(family='constant',k=1)))
        history[ep['id']]=r['delivered_ERR']
        datahash[ep['id']]=digest(data)
        deliveryhash[ep['id']]=digest(history[ep['id']])
    result=fit(history)
    result['input_sha256']=datahash
    result['delivered_ERR_sha256']=deliveryhash
    result['frozen_plan_commit']='449de0e12863196476b819ccbd4c864eea3429c0'
    result['training_source_sha256']={name:norm_hash((HERE/name).read_bytes()) for name in ['inputs.json','engine.py','policies.py','scenarios.py','training.py','IMPLEMENTATION.md']}
    if write: save(HERE/'training.json',result)
    return result


def compact(r,spec,episode,data):
    kept=['horizon_ns','first_exceedance','Q_MC','bus','mean_bus_fraction_exact','mean_bus_percent',
          'started_control_operations','completed_control_operations','started_application_operations',
          'unfinished_operations','bus_after_first_exceedance','algorithm_cost','max_application_delay_ns','simulator_work']
    out={key:r[key] for key in kept}
    out.update(method=spec['id'],primary=spec['primary'],episode=episode,input_sha256=digest(data),mark_count=len(data['marks']))
    out['ERR_count']=len(r['err_events'])
    out['ERR_sha256']=digest(r['err_events'])
    out['delivered_ERR_sha256']=digest(r['delivered_ERR'])
    out['mode_history_sha256']=digest(r['mode_history'])
    out['mode_changes']=len(r['mode_history'])-1
    out['residual_errors']=r['residual_errors']
    out['whole_deterministic_result_sha256']=digest(r)
    time_by={str(k):0 for k in [1,3,9,27]}
    modes=r['mode_history']+[dict(t_ns=r['horizon_ns'],k=1)]
    for a,b in zip(modes,modes[1:]):time_by[str(a['k'])]+=b['t_ns']-a['t_ns']
    out['decision_time_by_stride_ns']=time_by
    return out


def comparison(cfg,weights,outdir,record=False):
    results=[]
    for ep in cfg['episodes']:
        if ep['split']!='test':continue
        data=generate(ep,cfg)
        path=HERE/'data'/f"{ep['id']}.json"
        if record:save(path,data)
        else:assert json.loads(path.read_text(encoding='utf-8'))==data,('test input',ep['id'])
        for spec in cfg['methods']:
            r=run(data['horizon_ns'],data['marks'],data['applications'],make(spec,weights=weights))
            results.append(compact(r,spec,ep['id'],data))
        print(ep['id'],len(data['marks']),'marks, 15 methods',flush=True)
    assert len(results)==60
    return dict(status='OWN RESULT / pending review',scope='one marked history per test episode; 60 deterministic rows; no MC probability or expected cost',rows=results)


def table(results):
    lines=['# T186 этап 2: диагностические истории','',
           'OWN RESULT, требуется рецензия. Занятость — вся история, включая после A; Q_MC не оценено.',
           'Все 60 строк с чувствительностью — results.json; здесь заранее выбранные 20 основных.','',
           '| Эпизод | Правило | bus, % времени | ERR | Первое A, с | Смен режима |',
           '|---|---|---:|---:|---:|---:|']
    for r in results['rows']:
        if r['primary']:
            first='нет в этой истории' if r['first_exceedance'] is None else f"{r['first_exceedance']['t']/NS:.9f}"
            lines.append(f"| {r['episode']} | {r['method']} | {r['mean_bus_percent']:.9f} | {r['ERR_count']} | {first} | {r['mode_changes']} |")
    return '\n'.join(lines)+'\n'


def bench(cfg,weights):
    spec=cfg['benchmark']; start=time.perf_counter(); deadline=start+spec['total_wall_budget_s']
    rows=[]; stop=False
    for H in spec['horizons_s']:
        for n in spec['counts']:
            marks=benchmark_marks(n,H,spec['seed'])
            for method in [m for m in cfg['methods'] if m['primary']]:
                times=[]; result=None;status='completed'
                for rep in range(spec['repeats']):
                    if stop or time.perf_counter()>=deadline:
                        status='skipped: total wall budget';stop=True;break
                    before=time.perf_counter()
                    try:result=run(H*NS,marks,[],make(method,weights=weights),deadline=deadline)
                    except TimeoutError:
                        status='stopped: total wall budget';stop=True;break
                    times.append(time.perf_counter()-before)
                rows.append(dict(horizon_s=H,marks=n,method=method['id'],status=status,repeats_completed=len(times),
                                 elapsed_s=times,median_s=statistics.median(times) if times else None,
                                 simulator_work=result['simulator_work'] if result else None,
                                 virtual_controls=result['started_control_operations'] if result else None,
                                 algorithm_cost=result['algorithm_cost'] if result else None))
            print('benchmark',H,n,'completed or explicitly skipped',flush=True)
    elapsed=time.perf_counter()-start
    # Old watch-all is measured only on the accepted 400-second pilot.
    oldspec=importlib.util.spec_from_file_location('t186_stage1_bench',HERE.parent/'model.py')
    old=importlib.util.module_from_spec(oldspec);sys.modules[oldspec.name]=old;oldspec.loader.exec_module(old)
    oldcfg=json.loads((HERE.parent/'inputs.json').read_text(encoding='utf-8'))
    pilot=[]
    for method,policy in [('constant_fast',dict(family='constant',k=1)),('our_err_r4',dict(family='our'))]:
        t=time.perf_counter();before=old.run(oldcfg,method);oldtime=time.perf_counter()-t
        t=time.perf_counter();after=run(oldcfg['horizon_ns'],oldcfg['injections'],oldcfg['application_reads'],make(policy,our_cfg=oldcfg['policy']));newtime=time.perf_counter()-t
        assert before['bus']==after['bus'] and before['first_exceedance']==after['first_exceedance']
        pilot.append(dict(method=method,watch_all_s=oldtime,active_queue_s=newtime,
                          watch_all_event_count=sum(before['simulator_work']['event_counts'].values()),
                          active_event_count=sum(after['simulator_work']['event_counts'].values())))
    return dict(scope='fixed-count engineering load; Python wall time, not radiation samples/ARM/WCET',
                budget_s=spec['total_wall_budget_s'],matrix_elapsed_s=elapsed,rows=rows,pilot_only_old_solver=pilot,
                python=sys.version,platform=platform.platform(),processor=platform.processor(),logical_CPUs=os.cpu_count())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--train',action='store_true')
    parser.add_argument('--record',action='store_true')
    parser.add_argument('--skip-benchmark',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    cfg=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    if args.train:
        assert not args.record
        val=validate(cfg,ROOT)
        model=training_result(cfg,True)
        print('training complete; checks:',val['count'],'pairs:',model['training_pairs'])
        print('Commit training.json and training inputs before evaluation.')
        return
    provenance=verify_provenance()
    trained=json.loads((HERE/'training.json').read_text(encoding='utf-8'))
    assert norm_hash(git_bytes('HEAD',REL+'/training.json'))==norm_hash((HERE/'training.json').read_bytes()),'training must be committed before test evaluation'
    assert training_result(cfg)==trained,'frozen training result changed'
    val=validate(cfg,ROOT);val['provenance']=provenance
    out=args.output or (HERE/'outputs' if args.record else ROOT/'.cache/t186-stage2-replay')
    out.mkdir(parents=True,exist_ok=True)
    results=comparison(cfg,trained['weights'],out,args.record)
    limits=calculate(cfg)
    for name,obj in [('validation.json',val),('results.json',results),('bounds.json',limits),('resources.json',resource_bounds(cfg))]:
        save(out/name,obj)
        if not args.record:
            assert json.loads((HERE/'outputs'/name).read_text(encoding='utf-8'))==obj,('replay differs',name)
    (out/'table.md').write_text(table(results),encoding='utf-8',newline='\n')
    if not args.record:assert (out/'table.md').read_bytes()==(HERE/'outputs/table.md').read_bytes().replace(b'\r\n',b'\n')
    if not args.skip_benchmark:save(out/'benchmark.json',bench(cfg,trained['weights']))
    save(out/'environment.json',dict(python=sys.version,platform=platform.platform(),git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),command=sys.argv))
    print('Stage 2 complete:',val['count'],'checks, 60 rows;',out,flush=True)


if __name__=='__main__':main()
