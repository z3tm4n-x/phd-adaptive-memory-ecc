"""Four frozen epsilon points; no changes to historical experiments."""
import argparse,json
from fractions import Fraction as F
from model import HERE,NS,load,setup,lower_classes,fixed_candidate,adaptive_candidate,encode,sha,ceil

def calculate(progress=False):
    manifest,canonical,cfg,cases=load(); rows=[]; c=setup(canonical,cfg)
    for filename,inp in cases:
        eps=F(inp['fixed']['epsilon'])
        lower=lower_classes(c,eps); fixed=fixed_candidate(c,eps); adaptive=adaptive_candidate(c,eps)
        comparisons={}
        if adaptive.get('Q_upper') is not None and fixed.get('Q_upper') is not None:
            for cls,key in [('constant','constant_bus_lower'),('schedule','schedule_bus_lower')]:
                comparisons[cls]=dict(
                    evidence='interval comparisons of expected protection SRAM bus; unknown controller additions separate',
                    guaranteed_saving_from_sufficient_A_upper_and_class_lower=1-adaptive['hard_bus_upper']/lower[key] if lower[key]>0 else None,
                    saving_ceiling_for_this_family_vs_optimum_using_feasible_member=1-adaptive['mandatory_expected_bus_lower']/fixed['bus_upper'],
                    max_extra_competitor_bus_fraction_for_family_nonadvantage=adaptive['mandatory_expected_bus_lower']-fixed['bus_upper'],
                    necessary_competitor_extra_bus_fraction_for_20percent=adaptive['mandatory_expected_bus_lower']/F(4,5)-fixed['bus_upper'],
                    needed_adaptive_bus_upper_for_20percent=F(4,5)*lower[key],
                    needed_adaptive_bus_upper_for_30percent=F(7,10)*lower[key],
                    proved_optimum=False,positive_20percent_gain_established=False,
                    condition='same frozen p+r; lower/upper service contracts; if competitor overhead<=reported positive margin, even mandatory family cost exceeds feasible competitor')
        rows.append(dict(input=filename,epsilon=eps,mandatory=eps>=F('.001'),
            lower_bounds=lower,fixed=fixed,
            strong_schedule=dict(class_lower_bus=lower['schedule_bus_lower'],
                class_lower_core=lower['schedule_core_lower'],
                best_known_feasible_upper=fixed,
                nonconstant_optimum_status='UNKNOWN; upper is constant member, not restriction of comparison class',
                p_known_exactly=True,learning_price=0),adaptive=adaptive,comparisons=comparisons))
        if progress: print('epsilon',float(eps),'fixed k',fixed.get('k'),'adaptive',adaptive.get('status'),'N',adaptive.get('N'),flush=True)
    app=cfg['application']; obs=cfg['observation']; quotas=canonical['retained_quotas']
    appN=ceil((c['T']*NS-app['first_ns'])/app['epoch_ns'])
    return dict(status='ENGINEERING_EPSILON_SLICE_WITH_EXPLICIT_UNRESOLVED_TRANSFERS',
        scientific_acceptance=False,direction_A_closed=False,
        manifest_sha256=sha((HERE/'manifest.json').read_bytes()),
        scientific_input=manifest['canonical_raw_sha256'],only_scientific_change='fixed.epsilon',
        implementation_sha256={name:sha((HERE/name).read_bytes()) for name in ('model.py','run.py','plot.py','test_slice.py')},
        rows=rows,coefficients=c,
        shared_app_init=dict(application_reads=appN,useful_writes=0,
            app_bus_upper_fraction=appN*c['Rbus_plus']/(c['T']*NS),
            app_core_upper_fraction=appN*c['Rcore_plus']/(c['T']*NS),
            init_bus_upper_fraction=c['W']*(56*c['xp']+c['J'])/(c['T']*NS),
            init_core_upper_fraction=c['W']*(76*c['xp']+c['J'])/(c['T']*NS),
            init_encodes=c['W'],init_write_beats=3*c['W'],ECC_included_once=True,
            physical_initialization_and_environment_escape_probabilities=None),
        observation_cost=dict(cuts_upper=ceil(c['T']*NS/(obs['cut_ns']*c['xm']))+2,
            raw_records_upper=ceil(c['T']*NS/(4*c['xm']))+2,
            false_expected_upper=F(quotas['ordinary_false_expected_per_s'])*c['T'],
            outage_seconds_upper=F(quotas['ordinary_outage_fraction'])*c['T'],
            loss_episodes_upper=quotas['ordinary_loss_episodes_upper'],restores_upper=quotas['recoveries_upper'],
            retained_transport_loss_bytes=131136,record_bytes=32,
            extra_veto_expected=None,raw_records_expected=None,
            main_counter_and_group_state_bytes=None,stack_code_LUT_BRAM=None,
            CPU='sum E[N_i]*c_i_ns/(T*1e9)+idle_CPU; c_i unknown',
            energy='sum E[N_i]*e_i_J+T*idle_W; all nonoverlapping unit prices unknown',
            scope='full T, including unsuccessful/invalid attempts and post-A; competitors have no unused observation chain'),
        unresolved=['#196 confirmation of epsilon transfer and proposed relative-time repeated family',
            'optimal/stronger nonconstant feasible schedule under known p; current upper is a constant member',
            'actual full-prefix/WCET/delta_C and all-history service obligations',
            'nonzero CPU/energy/controller coefficients and admissible-channel guard/success law'],
        old_results_changed=False,no_MC_no_hardware_no_other_physical_axes=True)

def table(result):
    lines=['# Численный срез: операции защиты на SRAM-шине','',
        'Все цены — % полного T. Низы и верхи условны; управление/CPU/энергия добавляются параметрами.',
        'Верх расписания пока равен цене допустимого постоянного члена класса; optimum не найден.','',
        '| ε | Постоянный: k; Q⁺ | Цена постоянного [L; U], % | Расписание [L; U], % | Адаптация: k_b / k_e / N; Q⁺ | Обязательная цена семейства L_A, % | s_A/fixed; s_A/schedule, потолок* |',
        '|---:|---|---:|---:|---|---:|---|']
    pct=lambda v:f'{float(F(v))*100:.9g}'
    for row in result['rows']:
        lo,f,a=row['lower_bounds'],row['fixed'],row['adaptive']
        fixed=f"{f['k']}; {float(F(f['Q_upper'])):.9g}" if f.get('k') else 'не сертифицирован'
        fb=f"[{pct(lo['constant_bus_lower'])}; {pct(f['bus_upper'])}]" if f.get('k') else 'UNKNOWN'
        sb=f"[{pct(lo['schedule_bus_lower'])}; {pct(f['bus_upper'])}]" if f.get('k') else 'UNKNOWN'
        if a.get('Q_upper') is not None:
            ac=f"{a['k_base']} / {a['k_rare']} / {a['N']}; {float(F(a['Q_upper'])):.9g}"
            acp=pct(a['mandatory_expected_bus_lower'])
            cs=row['comparisons']; upper=f"{pct(cs['constant']['saving_ceiling_for_this_family_vs_optimum_using_feasible_member'])}%; {pct(cs['schedule']['saving_ceiling_for_this_family_vs_optimum_using_feasible_member'])}%"
        else: ac='не сертифицировано этим семейством'; acp='—'; upper='—'
        lines.append(f"| {float(F(row['epsilon'])):g} | {fixed} | {fb} | {sb} | {ac} | {acp} | {upper} |")
    lines+=['','* Это верх возможной экономии конкретного семейства по известным операциям:',
        '1−L_A/U_допустимого_постоянного для координаты известных операций. Он применим также к оптимальному расписанию,',
        'чья цена не больше цены этого допустимого члена. Не является оценкой фактической',
        'экономии; условие на неизвестную добавку соперника и отдельные сравнения — result.json.',
        'Отрицательное число не исключает все адаптивные методы и не закрывает А.',
        'Для строгого положительного выигрыша нужно U_A<L_класса; это не установлено.','']
    return '\n'.join(lines).encode('utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--write',action='store_true'); p.add_argument('--check',action='store_true'); a=p.parse_args()
    r=calculate(progress=True); raw=encode(r); md=table(r)
    if a.write: (HERE/'result.json').write_bytes(raw); (HERE/'TABLE.md').write_bytes(md)
    elif a.check:
        assert raw==(HERE/'result.json').read_bytes(),'result mismatch'
        assert md==(HERE/'TABLE.md').read_bytes(),'table mismatch'
    else: print(raw.decode())
    print('result SHA256',sha(raw))
