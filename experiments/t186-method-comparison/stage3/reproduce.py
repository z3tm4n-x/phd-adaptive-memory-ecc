"""Replay the registered stage3 cost matrix; no inference from zero failures."""
import argparse
from decimal import Decimal as D, localcontext
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from application import Application
from checks import validate
from cost import ledger, resource_bounds
from engine import run
from generator import generate, parts
from reuse import HERE, ROOT, formats, policies

PLAN_COMMIT='42f839b827b91019c335a40e3ab1dcea8990de15'
REL=HERE.relative_to(ROOT).as_posix()


def norm_hash(raw):return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()


def git_bytes(ref,path):
    return subprocess.check_output(['git','show',f'{ref}:{path}'],cwd=ROOT)


def provenance():
    manifest=json.loads((HERE/'provenance.json').read_text(encoding='utf-8'))
    for entry in manifest['working_dependencies']:
        assert norm_hash((ROOT/entry['path']).read_bytes())==entry['sha256'],entry['path']
    for entry in manifest['documentary_snapshots']:
        assert norm_hash(git_bytes(entry['commit'],entry['path']))==entry['sha256'],entry['path']
    assert norm_hash(git_bytes(PLAN_COMMIT,REL+'/inputs.json'))==norm_hash((HERE/'inputs.json').read_bytes())
    return dict(working_dependencies=len(manifest['working_dependencies']),
                documentary_snapshots=len(manifest['documentary_snapshots']),plan_commit=PLAN_COMMIT)


def envelope(ep,cfg):
    with localcontext() as ctx:
        ctx.prec=50
        ss=parts(ep,cfg['environment']);b=D(cfg['environment']['background_per_s'])
        B=D(cfg['environment']['peak_per_s']);Fs=D(cfg['environment']['solar_fluence_budget'])
        rho=D(cfg['environment']['rho_per_s'])
        mass=sum(s.mass for s in ss);solar=mass-b*ep['horizon_s'];slope=max(abs(s.slope) for s in ss)
        assert all(b<=s.low<=B and b<=s.high<=B for s in ss) and solar<=Fs and slope<=rho
        return dict(total_integrated_intensity=str(mass),solar_integral=str(solar),solar_budget=str(Fs),
                    maximum_abs_log_slope_per_s=str(slope),rho=str(rho),within_registered_envelope=True,
                    scope='these profiles only; no maximization over full Theta or physical calibration')


def compact(r,spec,ep,profile,input_hash):
    out={k:r[k] for k in ['horizon_ns','first_exceedance','Q_MC','bus','mean_bus_fraction_exact',
                          'mean_bus_percent','bus_after_first_exceedance','started_control_operations',
                          'completed_control_operations','unfinished_control','application','algorithm','simulator_work']}
    out.update(episode=ep['id'],application_profile=profile['id'],method=spec['id'],input_sha256=input_hash,
               cost=ledger(r,spec),mode_changes=len(r['mode_history'])-1,
               ERR_sha256=formats.digest(r['err_events']),delivered_ERR_sha256=formats.digest(r['delivered_ERR']),
               mode_history_sha256=formats.digest(r['mode_history']),whole_result_sha256=formats.digest(r),
               residual_errors=r['residual_errors'])
    durations={str(k):0 for k in (1,3,9,27)}
    modes=r['mode_history']+[dict(t_ns=r['horizon_ns'],k=1)]
    for a,b in zip(modes,modes[1:]):durations[str(a['k'])]+=b['t_ns']-a['t_ns']
    out['decision_time_by_stride_ns']=durations
    return out


def comparison(cfg,specs,weights,out):
    start=time.perf_counter();deadline=start+cfg['budgets']['comparison_wall_s']
    rows=[];inputs=[];timings=[];skipped=[];stopped=False
    for ep in cfg['episodes']:
        t=time.perf_counter();data=generate(ep,cfg);generation_s=time.perf_counter()-t
        input_hash=formats.digest(data)
        inputs.append(dict(episode=ep['id'],seed=ep['seed'],input_sha256=input_hash,
                           generation=data['generation'],envelope=envelope(ep,cfg)))
        for profile in cfg['application']['profiles']:
            app=Application(profile,cfg['application'],cfg['memory']['words'])
            for spec in specs:
                key=dict(episode=ep['id'],application_profile=profile['id'],method=spec['id'])
                if stopped or time.perf_counter()>=deadline:
                    stopped=True;skipped.append(dict(**key,reason='registered matrix wall budget'));continue
                before=time.perf_counter()
                try:
                    r=run(data['horizon_ns'],data['marks'],app,policies.make(spec,weights=weights,
                          words=cfg['memory']['words'],cut=cfg['delivery']['cut_ns']),deadline=deadline)
                except TimeoutError:
                    stopped=True;skipped.append(dict(**key,reason='cooperative wall-budget interruption'));continue
                elapsed=time.perf_counter()-before
                rows.append(compact(r,spec,ep,profile,input_hash));timings.append(dict(**key,elapsed_s=elapsed))
            print(ep['id'],profile['id'],len(data['marks']),'marks;',len(rows),'rows complete',flush=True)
        timings.append(dict(episode=ep['id'],generation_s=generation_s))
    results=dict(status='OWN RESULT / pending review',complete=len(rows)==75,expected_rows=75,rows=rows,skipped=skipped,
                 scope='one shared marked history per episode; full path price, not expected price or Q; no new tuning',
                 delivery=cfg['delivery'])
    formats.save(out/'timing.json',dict(budget_s=cfg['budgets']['comparison_wall_s'],elapsed_s=time.perf_counter()-start,rows=timings))
    return results,dict(inputs=inputs,scope='regenerate from frozen seeds and hash; no large generated input copy required')


def table(result):
    lines=['# T186 этап 3: полная цена зарегистрированных историй','',
           'OWN RESULT / pending review. Полная bus-цена включает приложение; CPU/энергия параметрические.',
           'Q_MC не оценивается. Время моделирования включает все операции после первого A.','',
           '| Эпизод | Приложение | Правило | bus, % | ERR write / все | Первое A, с |',
           '|---|---|---|---:|---:|---:|']
    for r in result['rows']:
        first='нет' if r['first_exceedance'] is None else f"{r['first_exceedance']['t']/10**9:.9f}"
        lines.append(f"| {r['episode']} | {r['application_profile']} | {r['method']} | {r['mean_bus_percent']:.9f} | {r['algorithm']['observed_write_ERR']} / {r['algorithm']['source_ERR']} | {first} |")
    return '\n'.join(lines)+'\n'


def benchmark(cfg):
    start=time.perf_counter();deadline=start+cfg['budgets']['benchmark_wall_s'];rows=[]
    oldcfg=json.loads((HERE.parent/'stage2/inputs.json').read_text(encoding='utf-8'))
    for ep in [cfg['episodes'][2],cfg['episodes'][4]]:
        for name in (['inverse50','accepted_global_thinning'] if ep['shape']!='mission' else ['inverse50']):
            elapsed=[];data=None;status='complete';repeat_hash=None
            for rep in range(cfg['benchmark']['repeats']):
                if time.perf_counter()>=deadline:status='skipped: benchmark budget';break
                before=time.perf_counter()
                data=generate(ep,cfg) if name=='inverse50' else formats.generate(dict(ep,split='benchmark'),oldcfg)
                elapsed.append(time.perf_counter()-before)
                current=formats.digest(data)
                assert repeat_hash is None or repeat_hash==current
                repeat_hash=current
            rows.append(dict(episode=ep['id'],algorithm=name,elapsed_s=elapsed,
                             median_s=statistics.median(elapsed) if elapsed else None,status=status,
                             mark_count=len(data['marks']) if data else None,repeat_sha256=repeat_hash,
                             candidate_count=data.get('candidate_count') if data else None,
                             generation=data.get('generation') if data else None))
            print('generator benchmark',ep['id'],name,status,flush=True)
    return dict(scope='Python generation wall time; repeated same seeds check determinism, not fresh MC; different algorithms have different paths',
                elapsed_s=time.perf_counter()-start,budget_s=cfg['budgets']['benchmark_wall_s'],rows=rows,
                old_mission='not run: expected candidates reported, no wall-time extrapolation asserted')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--record',action='store_true')
    parser.add_argument('--skip-benchmark',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    cfg=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    oldcfg=json.loads((HERE.parent/'stage2/inputs.json').read_text(encoding='utf-8'))
    weights=json.loads((HERE.parent/'stage2/training.json').read_text(encoding='utf-8'))['weights']
    specs=[next(m for m in oldcfg['methods'] if m['id']==id_) for id_ in cfg['method_ids']]
    check=validate(cfg);check['provenance']=provenance()
    out=args.output or (HERE/'outputs' if args.record else ROOT/'.cache/t186-stage3-replay')
    out.mkdir(parents=True,exist_ok=True)
    result,inputs=comparison(cfg,specs,weights,out)
    resources={p['id']:resource_bounds(Application(p,cfg['application']),cfg['environment']['mission_s']*10**9)
               for p in cfg['application']['profiles']}
    for name,obj in [('validation.json',check),('results.json',result),('inputs.json',inputs),('resources.json',resources)]:
        formats.save(out/name,obj)
        if not args.record:
            assert json.loads((HERE/'outputs'/name).read_text(encoding='utf-8'))==obj,('replay differs',name)
    (out/'table.md').write_text(table(result),encoding='utf-8',newline='\n')
    if not args.record:
        assert (out/'table.md').read_bytes()==(HERE/'outputs/table.md').read_bytes().replace(b'\r\n',b'\n')
    if not args.skip_benchmark:formats.save(out/'benchmark.json',benchmark(cfg))
    formats.save(out/'environment.json',dict(python=sys.version,platform=platform.platform(),processor=platform.processor(),logical_CPUs=os.cpu_count(),
                 git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),command=sys.argv,
                 source_sha256={p.name:norm_hash(p.read_bytes()) for p in sorted(HERE.glob('*.py'))},
                 result_manifest={name:norm_hash((out/name).read_bytes()) for name in ['validation.json','results.json','inputs.json','resources.json','table.md']}))
    assert result['complete'],('matrix incomplete; partial evidence saved',len(result['rows']))
    print('Stage3 complete:',check['count'],'checks;',len(result['rows']),'rows;',out,flush=True)


if __name__=='__main__':main()
