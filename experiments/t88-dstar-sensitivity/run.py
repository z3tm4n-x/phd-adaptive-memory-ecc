"""One offline T88 command; accepted T36--T82 are read-only dependencies."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as F
import hashlib
import json
import lzma
import multiprocessing
from pathlib import Path
import platform
import subprocess
import sys
import time

import engine as e


def worker(job):
    shield,g=job;started=time.monotonic();ans=[]
    for mode in e.CFG['modes']:
        p=e.context(shield,mode);cap,slope=e.g_cap(p)
        if g>cap:continue
        q=e.calendar(p,g)
        front,fallback,counts=e.compile_g(q)
        ans.append(dict(shield=shield,mode=mode,g=g,frontier=front,fallback=fallback,counts=counts))
    return dict(shield=shield,g=g,seconds=time.monotonic()-started,items=ans)


def load_checkpoint(path):
    def restore(x):
        if isinstance(x,str):
            try:return F(x)
            except ValueError:return x
        if isinstance(x,list):return [restore(v) for v in x]
        if isinstance(x,dict):return {k:restore(v) for k,v in x.items()}
        return x
    obj=restore(json.loads(lzma.decompress(path.read_bytes()).decode()))
    # Identity fields are decimal-looking strings, not numeric operands.
    obj['shield']=str(obj['shield']) if obj['shield']!=F('2.5') else '2.5'
    for r in obj['items']:
        r['shield']=obj['shield']
        for w in r['frontier']+r['fallback']:w['shield']=obj['shield']
    return obj


def checkpoint(path,obj):
    data=json.dumps(obj,ensure_ascii=False,sort_keys=True,default=lambda v:str(v) if isinstance(v,F) else v).encode()
    path.write_bytes(lzma.compress(data))


def summary(out,groups):
    table=[];curves=[];handoff=[];selected=[];bounds=[];fixed_rows=[];failures=[];envelopes=[]
    threshold_checks=0
    for shield in e.CFG['shields_g_cm2']:
        for mode in e.CFG['modes']:
            parts=[r for gr in groups for r in gr['items'] if r['shield']==shield and r['mode']==mode]
            frontier=[w for r in parts for w in r['frontier']]
            fallback=[w for r in parts for w in r['fallback']]
            p=e.context(shield,mode)
            cost_best=max(frontier,key=lambda w:w['D_cost'],default=None)
            cert_best=max(frontier,key=lambda w:w['D_cert'],default=None)
            cb=e.bracket(cost_best['D_cost']) if cost_best else None
            rb=e.bracket(cert_best['D_cert']) if cert_best else None
            fb=e.bracket(max((w['D_cert'] for w in fallback),default=F(0)))
            for br,field in ((cb,'D_cost'),(rb,'D_cert')):
                if br:
                    assert all(w[field] <= br['upper'] for w in frontier)
                    assert any(w[field] >= br['lower'] for w in frontier)
                    threshold_checks+=len(frontier)+1
                else:
                    assert all(w[field] < e.DMIN for w in frontier)
                    threshold_checks+=len(frontier)
            key=dict(shield=shield,mode=mode)
            r=dict(**key,D_1pct_lower=cb['lower'] if cb else None,D_1pct_upper=cb['upper'] if cb else None,
                   D_certificate_lower=rb['lower'] if rb else None,D_certificate_upper=rb['upper'] if rb else None,
                   always_S_certificate_lower=fb['lower'] if fb else None,
                   status_1pct='certified_finite_family_bracket' if cb else 'empty_established_region_D_ge_5e-5',
                   status_certificate='certified_finite_family_bracket' if rb else 'empty_established_two_mode_region',
                   threshold_tolerance=e.TOL,global_optimum_claimed=False,frontier_witnesses=len(frontier))
            dg=e.DMIN
            upper=max((w['D_cert'] for w in frontier+fallback),default=e.DMIN)
            grid={e.DMIN,e.F('0.0001'),e.F('0.0002'),e.F('0.0005'),p['eps']-e.old.errors(p['q'],mode)}
            grid.update(e.DMIN+(p['eps']-e.old.errors(p['q'],mode)-e.DMIN)*i/64 for i in range(65))
            # Plot sampling only; thresholds are exact affine intersections,
            # never inferred from these display points or their interpolation.
            grid.update(e.DMIN+(upper-e.DMIN)*i/64 for i in range(65))
            for br in (cb,rb,fb):
                if br:grid.update((br['lower'],br['upper'],br['upper']+e.TOL))
            reserve=F(e.CFG['working_risk_reserve_proposal'])
            wp=e.DMIN+(cb['lower']-e.DMIN)/2 if cb else e.DMIN+(rb['lower']-e.DMIN)/2 if rb else None
            working=None
            if wp is not None:
                for _ in range(32):
                    working=e.best_at(frontier,wp,reserve)
                    if working is not None:break
                    if wp==e.DMIN:break
                    wp=max(e.DMIN,e.j.t58.floor(((wp+e.DMIN)/2)/e.TOL)*e.TOL)
            if working:
                row=e.evaluate(e.calendar(p,working['g']),working['spec'],wp)
                assert row['risk_slack']>=reserve
                r.update(working_D=wp,working_risk_upper=row['risk_upper'],working_risk_slack=row['risk_slack'],working_cost_upper=row['objective'],working_g=working['g'],working_ka=working['spec']['ka'])
                selected.append(dict(purpose='working',**row));grid.add(wp)
            else:r.update(working_D=None,working_risk_slack=None,working_note='proposed reserve not achieved within established two-mode family')
            if cb:
                # A second, separately labelled interior witness keeps the
                # 1%-threshold policy but reduces D halfway to D_min. It does
                # not replace the preregistered 5e-5-reserve working point.
                di=(e.DMIN+cb['lower'])/2
                inside=e.evaluate(e.calendar(p,cost_best['g']),cost_best['spec'],di)
                assert inside['objective']<=e.LIMIT and inside['risk_slack']>0
                r.update(interior_1pct_D=di,interior_1pct_cost=inside['objective'],
                         interior_1pct_risk_slack=inside['risk_slack'])
                selected.append(dict(purpose='interior_1pct_no_5pct_reserve_claim',**inside))
            for purpose,br,ws in [('cost_threshold',cb,cost_best),('certificate_threshold',rb,cert_best)]:
                if br:
                    witness=e.evaluate(e.calendar(p,ws['g']),ws['spec'],br['lower'])
                    assert witness['risk_upper']<=p['eps']
                    if purpose=='cost_threshold':assert witness['objective']<=e.LIMIT
                    selected.append(dict(purpose=purpose,**witness))
                    handoff.append(dict(**key,purpose=purpose,D_safe_lower=br['lower'],bracket_upper=br['upper'],
                        upper_scope='maximum over this declared finite, directed numerical family only',
                        witness=dict(g=ws['g'],**ws['spec']),risk_upper=witness['risk_upper'],risk_slack=witness['risk_slack'],full_quiet_tax_upper=witness['objective']))
            for d in sorted(grid):
                if d<e.DMIN:continue
                w=e.best_at(frontier,d);wf=e.best_at(fallback,d)
                cr=dict(**key,Dstar=d,status='certified_conditional' if w else 'no_two_mode_certificate')
                if w:
                    row=e.evaluate(e.calendar(p,w['g']),w['spec'],d)
                    assert row['status']=='certified_conditional'
                    assert e.cost_at(w,d)==(row['quiet_upper'],row['returns_upper'],row['objective'])
                    cr.update(row)
                    selected.append(dict(purpose='curve',**row))
                cr['always_S_upper']=e.cost_at(wf,d)[2] if wf else None
                curves.append(cr)
                fr=e.fixed(p,d);fixed_rows.append(dict(mode_context=mode,**fr))
            for part in parts:
                failures.extend(dict(**key,g=part['g'],category=k,count=v) for k,v in part['counts'].items())
                envelopes.append(dict(**key,g=part['g'],
                    D_cost_max=max((w['D_cost'] for w in part['frontier']),default=None),
                    D_cert_max=max((w['D_cert'] for w in part['frontier']),default=None),
                    always_S_D_cert_max=max((w['D_cert'] for w in part['fallback']),default=None),
                    frontier_count=len(part['frontier'])))
            cap,slope=e.g_cap(p)
            bounds.append(dict(**key,g_min=p['g'],g_max=cap,next_g_risk_lower_of_certificate=e.old.errors(p['q'],mode)+e.DMIN+(cap+1)*slope,
                statement='excludes this sufficient formula above g_max, not physical failure',D_budget_ceiling=p['eps']-e.old.errors(p['q'],mode)))
            table.append(r)
    e.csv_write(out/'thresholds.csv',table)
    e.csv_write(out/'curves.csv',curves)
    e.csv_write(out/'constant_U.csv',fixed_rows)
    e.json_write(out/'constant_U.json',fixed_rows)
    e.csv_write(out/'search_bounds.csv',bounds)
    e.csv_write(out/'search_counts.csv',failures)
    e.json_write(out/'calendar_envelopes.json',envelopes)
    e.json_write(out/'selected.json',selected)
    e.json_write(out/'summary.json',table)
    e.json_write(out/'handoff.json',dict(issue=88,to_issue=89,delivery_sha='see immutable PR commit and protocol source hashes',
        versions={k:e.CFG[k] for k in ('base_sha','theory_sha','engineering_sha','architecture_sha')},
        contract=e.CFG,only_safe_lower_ends_for_test_request=True,physical_qualification=False,
        thresholds=handoff,unresolved=[r for r in table if r['D_1pct_lower'] is None]))
    e.json_write(out/'necessary_constant_class.json',[e.necessary_constant(e.context(s,'combined')) for s in e.CFG['shields_g_cm2']])
    return table,selected,dict(exact_threshold_envelope_checks=threshold_checks,
        calendar_mode_groups=len(envelopes),monotone_feasible_sets=True,
        no_interpolation_used_for_certification=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--resume',action='store_true',help='reuse this config-hash-specific numerical cache')
    ap.add_argument('--pilot-g',action='store_true',help='development smoke: only g=131, no threshold claims')
    args=ap.parse_args()
    start=time.monotonic();out=e.HERE/'outputs';out.mkdir(exist_ok=True)
    previous=json.loads((out/'protocol.json').read_text()) if (out/'protocol.json').exists() else {}
    import audit
    audit.assert_configuration()
    accepted_before=audit.accepted_snapshot()
    cfg_hash=hashlib.sha256((e.HERE/'config.json').read_bytes()).hexdigest()
    checkpoints=out/('smoke_cache' if args.pilot_g else 'cache')/cfg_hash[:12];checkpoints.mkdir(parents=True,exist_ok=True)
    jobs=[];groups=[]
    for s in e.CFG['shields_g_cm2']:
        caps=[e.g_cap(e.context(s,m))[0] for m in e.CFG['modes']]
        for g in range(131,132 if args.pilot_g else max(caps)+1):
            path=checkpoints/f'{s}_{g}.json.xz'
            engine_hash=hashlib.sha256((e.HERE/'engine.py').read_bytes()).hexdigest()
            cache_valid=(previous.get('config_sha256')==cfg_hash and
                         previous.get('source_hashes',{}).get('engine.py')==engine_hash)
            if args.resume and path.exists() and cache_valid:groups.append(load_checkpoint(path))
            else:jobs.append((s,g))
    print(f'T88 {len(jobs)} calendar jobs, {args.workers} numeric workers; no agents',flush=True)
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn')) as pool:
        for gr in pool.map(worker,jobs,chunksize=1):
            checkpoint(checkpoints/f"{gr['shield']}_{gr['g']}.json.xz",gr)
            groups.append(gr)
            print(f"calendar {gr['shield']} g={gr['g']}: {gr['seconds']:.2f}s, {len(groups)} completed",flush=True)
    groups.sort(key=lambda gr:(gr['shield'],gr['g']))
    if args.pilot_g:
        print('Smoke only, no thresholds published',flush=True)
        return
    table,selected,envelope_checks=summary(out,groups)
    from verify import verify
    checks=verify(selected)
    e.json_write(out/'independent_checks.json',checks)
    regressions=audit.regressions(out)
    baseline=audit.baseline(out)
    constant_checks=audit.constant_checks(out)
    audit.effective_inputs(out)
    from plot import plots
    plots(out)
    assert accepted_before==audit.accepted_snapshot(), 'accepted dependency changed during run'
    e.json_write(out/'accepted_source_hashes.json',accepted_before)
    protocol=dict(versions=e.CFG,config_sha256=cfg_hash,python=platform.python_version(),
        wall_seconds=time.monotonic()-start,workers=args.workers,calendar_jobs=len(groups),
        first_full_scan_wall_seconds=(previous.get('first_full_scan_wall_seconds',previous.get('wall_seconds'))
            if args.resume else time.monotonic()-start),
        freshly_computed_calendars=len(jobs),cache_reused_calendars=len(groups)-len(jobs),
        calendar_compute_seconds_sum=sum(gr['seconds'] for gr in groups),
        source_hashes=audit.delivery_sources(),regressions=regressions,
        selected_rows=len(selected),independent_checks=checks,envelope_checks=envelope_checks,
        baseline_controls=baseline,constant_checks=constant_checks,
        accepted_files_unchanged=True,physical_qualification=False)
    e.json_write(out/'protocol.json',protocol)
    from report import report
    report(out,table,selected,protocol)
    for r in table:print(r['shield'],r['mode'],r['D_1pct_lower'],r['D_certificate_lower'],flush=True)


if __name__=='__main__':
    main()
