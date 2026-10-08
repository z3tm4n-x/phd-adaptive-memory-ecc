#!/usr/bin/env python3
"""T126 starter map: accepted anchors + necessary-bound regressions.

No new engineering grid or physical campaign. Default: read-only byte check.
--write writes only the three T126 outputs listed below, never accepted files.
Python >=3.10, standard library and local Git objects at the declared base.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import subprocess
import sys
import unittest
from dataclasses import replace
from fractions import Fraction as F

from bounds import plateau, moderate_lower, tail_lower, price_floor, ratio_or_status, status

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = "67bf34b4f06a0410461e728f4217b8c58f704b04"
sys.path.insert(0, str(ROOT/"experiments/t58-fixed-baseline-r0b"))
from certificate import Risk, Resource, fixed_period, first_resource_tick, class_lower


def load(path):
    return json.loads((ROOT/path).read_text())


def serial(obj):
    if isinstance(obj, F):
        return str(obj)
    if isinstance(obj, dict):
        return {k: serial(v) for k, v in obj.items()}
    if isinstance(obj, (tuple, list)):
        return [serial(v) for v in obj]
    return obj


def decimal(x, places=12, upper=True):
    if x is None:
        return "не установлено"
    x = F(x); scale = 10**places
    z = -((-x*scale).__floor__()) if upper else (x*scale).__floor__()
    sign = "−" if z < 0 else ""
    z = abs(z)
    return f"{sign}{z//scale}.{z%scale:0{places}d}"


def pin_sources():
    paths = [
        "theory/fixed-period-resource-contract.md",
        "theory/fixed-period-resource-contract-appendix.md",
        "theory/t95-method-regime-selection.md",
        "theory/t95-method-regime-selection-appendix.md",
        "theory/t114-two-stage-err.md",
        "theory/t114-two-stage-err-appendix.md",
        "experiments/t58-fixed-baseline-r0b/config.json",
        "experiments/t58-fixed-baseline-r0b/certificate.py",
        "experiments/t58-fixed-baseline-r0b/summary.json",
        "experiments/t95-method-regime-map/inputs.json",
        "experiments/t95-method-regime-map/report.json",
        "experiments/t90-monitor-physical/outputs/pinned_inputs.json",
        "experiments/t88-dstar-sensitivity/outputs/constant_U.json",
        "experiments/t110-err-write-service/report.json",
        "experiments/t114-two-stage-err/report.json",
        "experiments/t114-two-stage-err/config.json",
        "experiments/t114-two-stage-err/HANDOFF.md",
    ]
    result = []
    for p in paths:
        data = (ROOT/p).read_bytes()
        want = subprocess.check_output(["git", "show", f"{BASE}:{p}"], cwd=ROOT)
        if data != want:
            raise AssertionError("accepted source differs: "+p)
        result.append(dict(path=p, git_blob=hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest(),
                           sha256=hashlib.sha256(data).hexdigest()))
    return result


def coordinates(n, W, T, eps, D, b, B, FS, P_min=None):
    # The reference plateau saturates the rarity bound for these anchors.
    # These are NOT the actual time-series integrals or the ratio of unknowns.
    bg = b*b*T
    excess = (B*B-b*b)*min(T, FS/(B-b)) if B > b else F(0)
    k = F(n-1, 2*n*W)
    return dict(delta=D/eps, k_singleton=k,
                S2_background_reference=bg, S2_excess_reference=excess,
                S2_reference=bg+excess,
                eta_reference=ratio_or_status(bg+excess, bg),
                eta_actual=None,
                eta_kind="attainable_reference_envelope_not_actual_or_ratio_bound",
                P_min_certified_family=P_min,
                sigma_reference=None if P_min is None else k*P_min*excess/eps,
                sigma_is_necessary_impossibility_test=False)


def r0b_anchors(budgets):
    source = load("experiments/t58-fixed-baseline-r0b/summary.json")
    h = {k: F(v) for k, v in source['history'].items() if k in
         ('T_s', 'B_per_bit_s_inverse', 'bbar_per_bit_s_inverse', 'FS_per_bit')}
    cfg = load("experiments/t58-fixed-baseline-r0b/config.json")
    out = []
    for W, speed, name in [(262144, 64000000, "R0-B малый / U"),
                           (1935832, 256000000, "R0-B большой / U")]:
        old = next(r for r in source['core'] if r['W']==W and r['R_eff_bit_s']==speed and F(r['tax'])==F('.01'))
        c = F(39, speed); N = 39*W; T = h['T_s']
        p = Risk(T, h['B_per_bit_s_inverse']*N, h['bbar_per_bit_s_inverse']*N,
                 h['FS_per_bit']*N, F(1,W), F(1), F(38,39*W), F(38,39*W*W), D=c)
        r = Resource(W,c,T,F('.001'),F('.01'),F('.05'),F('3e-6'),F('1e-7'),F('.5'),F('1e-7'),F('1e-8'))
        test = fixed_period(p,r,F('.01'),1,2**64-1)
        assert serial(test)==old['rarity_diagnostic'], "T58 anchor drift"
        wit = plateau(T,p.B,p.b,p.FS)
        low = class_lower(W,39,p.B,wit['L'],c,c,T,F('.01'),
                          witness_admissible=True,deterministic_window_contract=True)
        assert serial(low)==old['lower_fixed_U']
        # Same accepted resource tests; remove only the objective tax cap.
        Pmin = first_resource_tick(replace(r,tax=F(1)),1,2**64-1)*r.tick
        upper = test['upper_components']['total'] if test['selected_tick'] else None
        cost = test['resource']['tax_upper'] if test['selected_tick'] else None
        labels = [status(constant_ok=cost is not None and cost<=b,
                         fixed_excluded=b<=F('.01') and low['lower']>F('.01')) for b in budgets]
        out.append(dict(id="r0b_"+str(W),example_id="A1" if W==262144 else "A2",
            name=name,domain="T58/rareness-diagnostic/full39/U/no-app-corrections",
            qualification="conditional_model",n=39,W=W,T=T,epsilon=F('.01'),
            Dstar=F(0),Dstar_status="exact zero in declared singleton model, not physical data",
            coordinates=coordinates(39,W,T,F('.01'),F(0),p.b,p.B,p.FS,Pmin),
            risk_upper=upper,selected_tick=test['selected_tick'],
            risk_at_resource_boundary=F(old['rarity_diagnostic_evaluated']['upper']['total']),
            fixed_class_risk_lower_at_1pct=low['lower'],
            constant_quiet_upper=cost,constant_mission_upper=cost,
            adaptive_quiet_upper=None,adaptive_mission_upper=None,
            price_metric="protection occupancy, full-horizon quiet; no returning-Q contract",
            application="T58 workload <= sigma+u*t, sigma=g=1e-7 s, u=.5; no ECC reset",
            full_bus_upper=None if cost is None else cost+F('.5')+F('1e-7')/T,
            resource=test['resource'],P_min_kind="minimum of accepted sufficient resource tests, not architecture optimum",
            margin_10pct="conditional extra requirement: joint operation WCET <= reserved c/1.1; not qualified by T58",
            channel="none",statuses=labels,
            constant_excluded_by_budget=[b<=F('.01') and low['lower']>F('.01') for b in budgets],
            unresolved="adaptive lifetime certificate absent; physical class and preparation not qualified"))
    return out


def monitor_anchors(budgets):
    source = load("experiments/t95-method-regime-map/report.json")
    pinned = next(x for x in load("experiments/t90-monitor-physical/outputs/pinned_inputs.json") if x['shield']=='3')
    env = pinned['effective_T88_input']['environment']
    fixed = load("experiments/t88-dstar-sensitivity/outputs/constant_U.json")
    out=[]
    for a in source['rows']:
        D = F(a['Dstar']); price = F(a['normal_price_upper'])
        lower = F(source['lower_bound']['fixed_class_cost_lower'])
        cf = F(a['fixed_cost_upper'])
        fr = next(x for x in fixed if x['shield']=='3' and x['mode_context']=='combined' and F(x['Dstar'])==D)
        labels = [status(constant_ok=cf<=b,adaptive_ok=price<=b,fixed_excluded=lower>b) for b in budgets]
        out.append(dict(id="cy_T95_"+a['name'],example_id="A3",name="CY / U / монитор / "+a['name'],
            domain="T95/U/T80-slow-entry-fast-internal/combined/old-atomic-app",
            qualification="conditional_monitor_not_a_device",n=env['n'],W=env['W'],T=F(env['T']),epsilon=F(env['eps']),
            Dstar=D,coordinates=coordinates(env['n'],env['W'],F(env['T']),F(env['eps']),D,F(env['b']),F(env['B']),F(env['FS'])),
            risk_upper=F(a['risk_upper']),constant_risk_upper=F(fr['risk_upper']),
            constant_quiet_lower=lower,constant_quiet_upper=cf,
            adaptive_quiet_upper=price,adaptive_mission_upper=F(a['S_full_price_upper']),
            mission_price_kind="accepted all-FAST cap only; no new mission-price minimization",
            quiet_gain_lower=lower/price,
            price_metric="max(whole quiet mission, quiet returns), all protection/channel/control costs",
            application="T95 joint U timing and old atomic-app contract only; T114 observed writes excluded",
            full_bus_upper=None,full_bus_unknown="useful offered application work not specified",
            resource_pass=True,selected_short_period_upper=F(a['g'])*env['W']*F('1.00001e-9'),
            P_min_kind="unknown global minimum; selected short period is not P_min",
            channel=dict(a_M=1000000,A_M=1000000,window_s=1,step_s=F('.5'),
                         post_window_s=1,eta=F('.001'),rho_entry=F('1e-6'),rho_internal=F('.048'),
                         complete_contract="theory/t95-method-regime-selection.md §1; T80 lower/MGF/upper",
                         real_qualification=None),
            statuses=labels,constant_excluded_by_budget=[lower>b for b in budgets],
            unresolved="full real-monitor/direct/WCET qualification; new #127 class not substituted"))
    return out


def err_anchor(budgets):
    source=load("experiments/t114-two-stage-err/report.json")
    env=load("experiments/t110-err-write-service/report.json")['rows'][0]['environment']
    r=next(x for x in source['rows'] if x['profile']=='MCU_calibrated_write' and x['growth']=='main'
           and x['stages']==2 and x['candidate_role']=='presented')
    one=next(x for x in source['rows'] if x['profile']=='MCU_calibrated_write' and x['growth']=='main'
             and x['stages']==1 and x['candidate_role']=='presented')
    c=source['constant_E']['3']; pr=r['price']; T=F(env['T'])
    # Accepted T114 price is affine in rates of offered observed writes.
    # Display the certified intercept, never silently a zero-load physical point.
    q=F(pr['quiet_upper_intercept']); m=F(pr['mission_upper_intercept'])
    obs=F(pr['write_observation_price_per_request'])
    # Same common burst=1 domain of T114 HANDOFF. Quiet rates refer to the
    # expanded components required by that HANDOFF, not to undilated windows.
    rate=min(F(r['resources']['rate_max_sigma1']),F(c['resources']['rate_max_sigma1']))
    offered_q=rate+(1+F('3e-6')*rate)*1000/(F('.9')*T)
    offered_T=rate+1/T
    q_full=q+obs*offered_q; m_full=m+obs*offered_T
    lower=F(c['class_lower']['read_price_lower'])
    return dict(id="cy_T114_ERR",example_id="A3",name="CY / E / ERR / основной рост",
        domain="T114/E/main-rho.048/MCU-a.9-zeta.1/observed-writes",
        qualification="conditional_ERR_and_joint_WCET_not_measured",n=38,W=524288,T=T,epsilon=F('.001'),Dstar=F(env['D']),
        coordinates=coordinates(38,524288,T,F('.001'),F(env['D']),F(env['b']),F(env['B']),F(env['FS'])),
        sufficient_pair_coefficient=F(1,2*524288),
        risk_upper=F(r['risk_upper']),
        adaptive_quiet_upper_intercept=q,adaptive_mission_upper_intercept=m,
        write_observation_per_request=obs,
        adaptive_quiet_upper=q_full,adaptive_mission_upper=m_full,
        price_scope="T114 full admitted burst=1 load envelope; read/write mix not invented",
        application=dict(burst=1,rate_max=rate,quiet_expanded_write_rate_upper=offered_q,
            full_bus_affine_write=F(pr['total_bus_application_write_per_request']),
            full_bus_affine_read=F(pr['total_bus_application_read_per_request']),
            note="for total bus replace observation addend, do not add it twice"),
        full_bus_quiet_upper=q+max(F(pr['total_bus_application_write_per_request']),F(pr['total_bus_application_read_per_request']))*offered_q,
        full_bus_mission_upper=m+max(F(pr['total_bus_application_write_per_request']),F(pr['total_bus_application_read_per_request']))*offered_T,
        constant_quiet_lower=lower,constant_quiet_upper=None,
        constant_mission_lower=lower,constant_mission_upper=F(c['mission_price_upper_intercept'])+obs*offered_T,
        constant_risk_upper=F(c['risk_upper']),constant_resource_pass=c['feasible'],
        constant_quiet_gap="mission scalar not silently used for returning quiet upper; engineer to export accepted price formula",
        mission_gain_lower=lower/m_full,
        channel=dict(a=F('.9'),zeta=F('.1'),phi=F(r['calendar']['phi']),rho=F('.048'),
                     tau=F(r['calendar']['tau']),w=F(r['calendar']['w']),h=F(r['calendar']['h']),
                     ERR_or_loss_delivery_s=F('1.2e-6'),lifetime_miss_quota=F('1e-6'),
                     complete_contract="experiments/t114-two-stage-err/HANDOFF.md"),
        one_stage=dict(risk_upper=F(one['risk_upper']),quiet_intercept=F(one['price']['quiet_upper_intercept']),
                       mission_intercept=F(one['price']['mission_upper_intercept'])),
        resource=r['resources'],P_min_kind="not inferred from chosen g196 or busy Wc",
        statuses=[status(adaptive_ok=q_full<=b,fixed_excluded=lower>b) for b in budgets],
        constant_excluded_by_budget=[lower>b for b in budgets],
        unresolved="lower ERR channel/full direct/joint observed-write WCET remain unqualified; no new ERR tuning")


def necessary_cases():
    src=load("experiments/t95-method-regime-map/report.json")
    p=next(x for x in load("experiments/t90-monitor-physical/outputs/pinned_inputs.json") if x['shield']=='3')['effective_T88_input']
    e,s=p['environment'],p['service']
    T,B,b,FS=[F(e[k]) for k in ('T','B','b','FS')]
    cp=s['c_ticks']*F(s['tick_upper_s']); cm=s['c_ticks']*F(s['tick_lower_s'])
    S2=b*b*T+(B+b)*FS; mesh=F('1e-9'); out=[]
    for fraction,P1 in [(F(1),F(2)),(F(1,2),F(4)),(F(1,4),F(8))]:
        w=plateau(T,B,b,FS,S2_cap=fraction*S2)
        assert w['admissible'] and w['S2']<=fraction*S2 and w['solar_exposure']<=FS
        L=w['L']; tail=tail_lower(e['W'],e['n'],B,L,cp,P1,F(p['quotas']['delta_exec']))
        risk=lambda P: moderate_lower(e['W'],e['n'],B,L,cp,P,P1,F(p['quotas']['delta_exec']))
        lo=cp//mesh+1; hi=P1//mesh
        assert tail>F(e['eps']) and risk(lo*mesh)<=F(e['eps'])<risk(hi*mesh)
        while hi-lo>1:
            mid=(lo+hi)//2
            if risk(mid*mesh)>F(e['eps']):hi=mid
            else:lo=mid
        P0=hi*mesh; low=price_floor(e['W'],cm,cp,P0,T)
        if fraction==1:
            assert P0==F(src['lower_bound']['P0_s']) and low==F(src['lower_bound']['fixed_class_cost_lower'])
        out.append(dict(S2_fraction=fraction,witness=w,P_split=P1,P0=P0,
                        Q_lower_at_P0=risk(P0),Q_lower_at_predecessor=risk(P0-mesh),
                        tail_Q_lower=tail,constant_price_lower=low,
                        scope="arithmetic cap sensitivity; not physical #127 input or a new controller"))
    return out


def build():
    grid=load("experiments/t126-regime-map/grid.json")
    budgets=list(map(F,grid['quiet_protection_budgets']))
    rows=r0b_anchors(budgets)+monitor_anchors(budgets)+[err_anchor(budgets)]
    rows += [dict(id="cy_physical",example_id="A3",name="CY / новая кривая защиты #127",
                  qualification="missing",statuses=["unknown"]*len(budgets),
                  unresolved="full response, Dstar/S2 per thickness, coverage and lower-channel contract pending #127"),
             dict(id="other_sram",example_id="A4",name="Другая SRAM / external39",
                  qualification="missing",statuses=["unknown"]*len(budgets),
                  unresolved="exact specimen/revision and transferable low-energy proton curve missing")]
    for r in rows:
        r['constant_relative_quiet_price']=[dict(budget=b,
            lower=None if r.get('constant_quiet_lower') is None else r['constant_quiet_lower']/b,
            upper=None if r.get('constant_quiet_upper') is None else r['constant_quiet_upper']/b)
            for b in budgets]
    return dict(task=126,base_sha=BASE,stage="starter_anchor_map_not_engineering_grid",date="2026-10-08",
                budgets=budgets,rows=rows,necessary_cap_checks=necessary_cases(),sources=pin_sources(),
                epsilon_grid_executed=False,physical_qualification_claimed=False,
                historical_comparison=dict(gain="12.3873885545",source_repository="z3tm4n-x/chapter4-risk-limited-scrubber",
                    source_sha="cf7ab706224f7872fdafcf34febda70e3f6c8dd1",
                    role="reported historical pass-count ratio only; not map color or lifetime robust gain"),
                reproductions_completed=dict(T58="31 tests; 54 core / 2916 old rows; source hashes",T95="71 checks",T114="19 state + 439 numeric checks including T110"),
                independent_engineering_confirmation="requested through orchestrator, not performed by this script")


LABELS={"constant_sufficient":"Постоянный достаточен", "adaptation_needed_and_sufficient":"Адаптация нужна и достаточна",
        "adaptive_sufficient_necessity_unknown":"Адаптация достаточна", "period_class_excluded":"Класс периода исключён", "unknown":"Не установлено"}
COLORS={"constant_sufficient":"#d8ecdf", "adaptation_needed_and_sufficient":"#b5d9eb",
        "adaptive_sufficient_necessity_unknown":"#e0d7ed", "period_class_excluded":"#f4caca", "unknown":"#e7e9ec"}


def svg(report):
    # A categorical evidence map, not an interpolated physical phase diagram.
    width=1240; height=225+70*len(report['rows'])
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         '<rect width="100%" height="100%" fill="white"/>',
         '<g font-family="DejaVu Sans, sans-serif" fill="#192b3c">',
         '<text x="28" y="34" font-size="24">T126 · Стартовая карта принятых условных точек</text>',
         '<text x="28" y="62" font-size="15">08.10.2026 · Разные классы показаны отдельно; это не квалификация аппаратуры и не новая сетка.</text>',
         '<text x="28" y="91" font-size="15">Строка / сопоставимый класс</text>']
    for j,b in enumerate(report['budgets']):
        out.append(f'<text x="{460+250*j}" y="91" font-size="16">Бюджет защиты {int(100*b)}%</text>')
    for i,r in enumerate(report['rows']):
        y=108+70*i
        out.append(f'<text x="28" y="{y+25}" font-size="15">{html.escape(r["name"])}</text>')
        for j,s in enumerate(r['statuses']):
            x=450+250*j
            text=LABELS[s]
            lines=["Адаптация нужна", "и достаточна"] if s=='adaptation_needed_and_sufficient' else [text]
            if s=='unknown' and r.get('constant_excluded_by_budget',[False]*len(report['budgets']))[j]:
                lines=["Не установлено", "постоянный исключён"]
            out.append(f'<rect x="{x}" y="{y}" width="240" height="56" rx="5" fill="{COLORS[s]}"/>')
            for k,line in enumerate(lines):
                out.append(f'<text x="{x+12}" y="{y+22+18*k}" font-size="14">{html.escape(line)}</text>')
    y=124+70*len(report['rows'])
    out += [f'<text x="28" y="{y}" font-size="14">T58: весь тихий срок; T95: максимум тихих метрик; T114: допустимая нагрузка приложения включена.</text>',
            f'<text x="28" y="{y+24}" font-size="14">Ни одна строка не доказывает исключение всего адаптивного класса. Серый ≠ физическая невозможность.</text>',
            f'<text x="28" y="{y+48}" font-size="14">Точные Q, цены, единицы, предпосылки и пропуски — starter-map.json и основной текст.</text>', '</g></svg>']
    return '\n'.join(out)+'\n'


def table(report):
    out=['# T126. Воспроизведённые опорные строки, 08.10.2026','',
         'Не новая инженерная сетка. Цена — доля шины, ниже в процентах. '
         'Неизвестное не заменено нулём. Все строки условные; область каждой строки — в JSON.','',
         '| Строка | Верх риска | Тихая защита, верх % | Защита за срок, верх % | Необходимый низ постоянной цены, % |',
         '|---|---:|---:|---:|---:|']
    for r in report['rows']:
        cq=r.get('adaptive_quiet_upper')
        cm=r.get('adaptive_mission_upper')
        if cq is None:cq=r.get('constant_quiet_upper')
        if cm is None:cm=r.get('constant_mission_upper')
        low=r.get('constant_quiet_lower')
        out.append('| '+r['name']+' | '+decimal(r.get('risk_upper'))+' | '+decimal(None if cq is None else 100*cq,8)+' | '+decimal(None if cm is None else 100*cm,8)+' | '+decimal(None if low is None else 100*low,8,False)+' |')
    out += ['', 'T95: миссионный upper — грубый all-FAST cap, не средняя цена экономного режима. '
            'Его большой коэффициент относится только к объявленной тихой цене.',
            'T114: таблица оплачивает весь общий burst=1 envelope, не нулевое приложение; '
            'intercept и аффинные коэффициенты сохранены отдельно. '
            'Постоянный E имеет предъявленный миссионный верх; returning-тихий верх не подменён им.', '',
            'Нижний риск большого R0-B при бюджете 1%: '+decimal(report['rows'][1]['fixed_class_risk_lower_at_1pct'],12,False)+
            '; адаптивная достаточность не установлена.','',
            'Новые проверки необходимого свидетеля (искусственные caps, не данные #127):','',
            '| Доля прежнего S₂ | Допустимое плато, с | P₀, с | Нижняя цена U, % |',
            '|---|---:|---:|---:|']
    for r in report['necessary_cap_checks']:
        out.append(f"| {r['S2_fraction']} | {decimal(r['witness']['L'],6,False)} | {decimal(r['P0'],9)} | {decimal(100*r['constant_price_lower'],8,False)} |")
    return '\n'.join(out)+'\n'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');args=ap.parse_args()
    suite=unittest.defaultTestLoader.discover(str(HERE),'test_bounds.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise AssertionError('necessary-bound regressions')
    r=build();r['new_unit_tests']=result.testsRun
    outputs={'starter-map.json':json.dumps(serial(r),ensure_ascii=False,indent=2)+'\n',
             'starter-map.svg':svg(r),'ANCHORS.md':table(r)}
    for name,data in outputs.items():
        target=HERE/name
        if args.write:target.write_text(data)
        if not target.exists() or target.read_text()!=data:raise AssertionError('T126 output differs: '+name)
    print(f'T126: {result.testsRun} tests; {len(r["rows"])} anchor/missing-input rows; 3 cap witnesses; accepted sources unchanged.')
    print('Engineering epsilon grid NOT run; physical qualification NOT claimed.')


if __name__=='__main__':main()
