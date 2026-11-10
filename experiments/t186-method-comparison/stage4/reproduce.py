"""Resumable stage4 replay; operational budgets never alter scientific inputs."""
import argparse
from decimal import Decimal as D,localcontext
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
from adapter import Adapter
from application import Application
from bounds import calculate
from checks import validate
from cost import ledger
from engine import run
from grid import Grid
from reuse import HERE,ROOT,formats,generator

PLAN='e4ed618d5425114938bf1ef52f3dcef0665ea9a8'
REL=HERE.relative_to(ROOT).as_posix()

def norm_hash(b):return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()
def git_bytes(ref,path):return subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=ROOT)

def verify():
    p=json.loads((HERE/'provenance.json').read_text(encoding='utf-8'))
    for e in p['working_dependencies']:
        assert norm_hash((ROOT/e['path']).read_bytes())==e['sha256'],('working dependency',e['path'])
    for e in p['documentary_snapshots']:
        assert norm_hash(git_bytes(e['commit'],e['path']))==e['sha256'],('documentary snapshot',e['path'])
    assert norm_hash(git_bytes(PLAN,REL+'/common-input.json'))==norm_hash((HERE/'common-input.json').read_bytes())
    return p

def envelope(ep,cfg):
    with localcontext() as ctx:
        ctx.prec=50;s=generator.parts(ep,cfg['environment']);env=cfg['environment'];b=D(env['background_per_s']);B=D(env['peak_per_s'])
        mass=sum(x.mass for x in s);solar=mass-b*ep['horizon_s'];slope=max(abs(x.slope) for x in s)
        assert all(b<=x.low<=B and b<=x.high<=B for x in s) and solar<=D(env['solar_fluence_budget']) and slope<=D(env['rho_per_s'])
        return dict(solar_integral=str(solar),integrated_intensity=str(mass),max_abs_log_slope=str(slope),within_envelope=True)

def compact(r,spec,ep,profile,ih):
    kept=['horizon_ns','first_exceedance','Q_MC','bus','mean_bus_fraction_exact','mean_bus_percent',
          'bus_after_first_exceedance','started_control_operations','completed_control_operations','unfinished_control',
          'application','algorithm','simulator_work','residual_errors']
    row={k:r[k] for k in kept}
    row.update(method=spec['id'],episode=ep['id'],profile=profile['id'],input_sha256=ih,cost=ledger(r,spec),
               whole_result_sha256=formats.digest(r),mode_changes=len(r['mode_history'])-1)
    for key in ['err_events','delivered_ERR','transport_batches','unknown_ranges','source_records','mode_history']:
        row[key+'_sha256']=formats.digest(r[key])
    durations={str(k):0 for k in (1,3,9,27)}
    history=r['mode_history']+[dict(t_ns=r['horizon_ns'],k=1)]
    for a,b in zip(history,history[1:]):durations[str(a['k'])]+=b['t_ns']-a['t_ns']
    row['decision_time_by_stride_ns']=durations
    return row

def table(rows,bounds):
    lines=['# T186: согласованный численный вариант','',
           'OWN RESULT, условные основания T196; окончательная независимая рецензия впереди.',
           'Цена истории отделена от lifetime upper при полном договоре; Q_MC не оценивается.','',
           '| Правило | Нагрузка |10лет, bus %|4 суток, диапазон bus %|Lifetime Q upper|Статус риска|',
           '|---|---|---:|---:|---:|---|']
    for r in rows:
        if r['episode']!='s4_mission':continue
        days=[d['mean_bus_percent'] for d in rows if d['method']==r['method'] and d['profile']==r['profile'] and d['episode']!='s4_mission']
        b=bounds['methods'][r['method']]
        status='условно выполнено' if b['lifetime_Q_upper']['value']<=.001 else 'не установлено'
        lines.append(f"| {r['method']} | {r['profile']} | {r['mean_bus_percent']:.9f} | {min(days):.6f}–{max(days):.6f} | {b['lifetime_Q_upper']['value']:.12g} | {status} |")
    return '\n'.join(lines)+'\n'

def read_checkpoint(path,signature):
    if not path.exists():return None
    x=json.loads(path.read_text(encoding='utf-8'))
    assert x['signature']==signature and formats.digest(x['result'])==x['result_sha256'],('checkpoint integrity',path.name)
    return x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--record',action='store_true');ap.add_argument('--output',type=Path)
    ap.add_argument('--budget-seconds',type=float,default=180)
    ap.add_argument('--max-new-rows',type=int);ap.add_argument('--pilot',action='store_true')
    args=ap.parse_args();assert args.budget_seconds>0
    cfg=json.loads((HERE/'common-input.json').read_text(encoding='utf-8'))
    provenance=verify();signature=formats.digest(provenance)
    out=args.output or (HERE/'outputs' if args.record else ROOT/'.cache/t186-stage4-replay')
    out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    cache=ROOT/'.cache/t186-stage4-state'/hashlib.sha256(str(out).encode()).hexdigest()[:16]/signature[:16]
    cache.mkdir(parents=True,exist_ok=True)
    validation=validate(cfg)
    legacy=subprocess.check_output([sys.executable,'-B',str(HERE.parent/'stage2/checks.py')],cwd=ROOT,text=True,encoding='utf-8')
    accepted=json.loads(legacy);assert accepted['count']==59
    validation['accepted_stage2_checks']=accepted
    validation['provenance']=dict(working_dependencies=len(provenance['working_dependencies']),documentary_snapshots=len(provenance['documentary_snapshots']),signature=signature)
    bounds=calculate(cfg)
    old=json.loads((HERE.parent/'stage2/inputs.json').read_text())
    weights=json.loads((HERE.parent/'stage2/training.json').read_text())['weights']
    specs=[dict(id=id_,family='constant',k=1) if id_=='constant_sufficient' else next(x for x in old['methods'] if x['id']==id_) for id_ in cfg['method_ids']]
    all_jobs=[(e,p,s) for e in cfg['episodes'] for p in cfg['application']['profiles'] for s in specs]
    pilot_ids={('s4_rise_fall','uniform','constant_sufficient'),('s4_rise_fall','uniform','our_r4')}
    jobs=[j for j in all_jobs if not args.pilot or tuple(x['id'] for x in j) in pilot_ids]
    start=time.perf_counter();deadline=start+args.budget_seconds;new=0;reused=0;timings=[];stop=None;inputs={}
    for ep,profile,spec in jobs:
        key='__'.join(x['id'] for x in (ep,profile,spec));path=cache/(key+'.json')
        if read_checkpoint(path,signature):reused+=1;continue
        if time.perf_counter()>=deadline or args.max_new_rows is not None and new>=args.max_new_rows:
            stop='requested operational budget or row limit';break
        data_path=cache/(ep['id']+'__input.json')
        cached=read_checkpoint(data_path,signature)
        if cached:data=cached['result']
        else:
            t=time.perf_counter();data=generator.generate(ep,cfg)
            formats.save(data_path,dict(signature=signature,result=data,result_sha256=formats.digest(data)))
            timings.append(dict(episode=ep['id'],generation_s=time.perf_counter()-t))
        ih=formats.digest(data);grid=Grid(cfg['memory']['words'],cfg['fixed']['period_ns'] if spec['id']=='constant_sufficient' else None)
        app=Application(profile,cfg['application'],grid)
        before=time.perf_counter()
        try:r=run(data['horizon_ns'],data['marks'],app,Adapter(spec,cfg['delivery'],words=grid.words,weights=weights),deadline=deadline)
        except TimeoutError:stop='cooperative row interruption; complete previous rows retained';break
        elapsed=time.perf_counter()-before;row=compact(r,spec,ep,profile,ih)
        formats.save(path,dict(signature=signature,result=row,result_sha256=formats.digest(row),elapsed_s=elapsed))
        timings.append(dict(row=key,solver_s=elapsed));new+=1
        print(key,'complete;',len(data['marks']),'marks;',round(elapsed,3),'solver seconds',flush=True)
    rows=[]
    for e,p,s in all_jobs:
        x=read_checkpoint(cache/('__'.join(v['id'] for v in (e,p,s))+'.json'),signature)
        if x:rows.append(x['result'])
    complete=len(rows)==len(all_jobs)
    for ep in cfg['episodes']:
        x=read_checkpoint(cache/(ep['id']+'__input.json'),signature)
        if x:
            data=x['result'];inputs[ep['id']]=dict(seed=ep['seed'],sha256=x['result_sha256'],generation=data['generation'],envelope=envelope(ep,cfg))
    progress=dict(complete=complete,completed_rows=len(rows),expected_rows=len(all_jobs),new_rows=new,reused_rows=reused,reason=stop,
                  signature=signature,elapsed_s=time.perf_counter()-start,budget_seconds=args.budget_seconds,timings=timings)
    formats.save(out/'progress.json',progress)
    formats.save(cache/('invocation-'+str(time.time_ns())+'.json'),progress)
    print('progress',len(rows),'/',len(all_jobs),'new',new,'reused',reused,'complete',complete,flush=True)
    if not complete:
        print('Repeat the same command to resume; scientific inputs and completed rows are unchanged.',flush=True)
        return 0 if args.pilot else 3
    result=dict(status='OWN RESULT / pending review',signature=signature,complete=True,rows=rows,
                scope='full path cost of five diagnostic singleton inputs, not full-Theta MC; lifetime bounds are separate',
                theoretical_horizon_s=cfg['environment']['mission_s'],additional_tuning_budget=0)
    objects={'validation.json':validation,'results.json':result,'inputs.json':inputs,'bounds.json':bounds}
    for name,obj in objects.items():
        formats.save(out/name,obj)
        if not args.record:assert json.loads((HERE/'outputs'/name).read_text(encoding='utf-8'))==obj,('replay differs',name)
    content=table(rows,bounds);(out/'table.md').write_text(content,encoding='utf-8',newline='\n')
    if not args.record:assert (HERE/'outputs/table.md').read_bytes().replace(b'\r\n',b'\n')==content.encode('utf-8')
    times={}
    for e,p,s in all_jobs:
        key='__'.join(v['id'] for v in (e,p,s));times[key]=read_checkpoint(cache/(key+'.json'),signature)['elapsed_s']
    formats.save(out/'timing.json',dict(solver_seconds_by_row=times,sum_solver_s=sum(times.values()),last_invocation=progress,
                                      scope='host/run-specific Python wall time; resumable budget, no ARM/WCET inference'))
    formats.save(out/'environment.json',dict(python=sys.version,platform=platform.platform(),command=sys.argv,
                 git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),signature=signature,
                 deterministic_hashes={name:norm_hash((out/name).read_bytes()) for name in list(objects)+['table.md']}))
    print('Stage4 complete:',validation['count'],'new checks +59 accepted;60 rows;',out,flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
