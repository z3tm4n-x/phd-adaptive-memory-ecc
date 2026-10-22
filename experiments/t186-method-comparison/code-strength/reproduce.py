"""Reproduce the single three-variant table and its directed checks."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from codec import Code,ROOT,t187
from checks import run as codec_checks
from comparison import calculate
from comparison_checks import run as comparison_checks
from informational_checks import run as information_checks
from repair_checks import frozen_snapshot, run as repair_checks

HERE=Path(__file__).resolve().parent
REL=HERE.relative_to(ROOT).as_posix()
BASE='76413140a8ce4c3884a44df5dbeb619580339faa'

def digest(raw):return hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()

def encode(value):
    def default(x):
        if isinstance(x,F):return str(x)
        raise TypeError(type(x).__name__)
    return (json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True,default=default)+'\n').encode('utf-8')


def verify():
    manifest=json.loads((HERE/'sources.json').read_text(encoding='utf-8'))
    for s in manifest['files']:
        raw=subprocess.check_output(['git','cat-file','blob',s['commit']+':'+s['path']],cwd=ROOT)
        if digest(raw)!=s['sha256']:raise ValueError('pinned git source mismatch: '+s['path'])
        if s.get('mode')!='git_object_only' and digest((ROOT/s['path']).read_bytes())!=s['sha256']:
            raise ValueError('working source mismatch: '+s['path'])
    changed=subprocess.check_output(['git','diff','--name-only',BASE,'--','experiments/t186-method-comparison'],cwd=ROOT,text=True).splitlines()
    if any(not p.startswith(REL+'/') for p in changed):raise ValueError('previous comparison changed')
    return manifest


def fmt(x,places=6,upper=False):return t187.dec(F(x),places,upper)
def up(x,places=6):return fmt(x,places,True)
def pct(x,places=6,upper=True):return fmt(100*F(x),places,upper)+'%'


def render(cfg,result,resources):
    rows=list(result['rows'].values());a=rows[1]['cost'];T=cfg['mission_s']
    lines=['# Единая таблица трёх вариантов — #186 / #196 / #206','',
     'OWN RESULT, условный p1=1. Соавторская применимость трёх Q подтверждена #196',
     'на v4/0111d424; локальная правка цены R1 выполнена по64132c36. Приёмка впереди.',
     'Это достаточные кандидаты,',
     'без физической квалификации и без вывода об оптимуме постоянного класса.',
     'Общая среда: один per-bit r(t) на48 выделенных позиций; W=131072, полезные',
     '0,5МиБ; T=315576000с, epsilon=0,001; clean с оплаченной инициализацией.',
     'Общий lifetime-резерв6e-6 — предпосылка условной модели. Strict-uniform,',
     'app-read без ремонта/ERR, полный32 write с pre-read/decode/encode/write. Все цены',
     'учитывают весь срок, плохие истории и незавершённую работу. [Сервис](../SERVICE.md).','',
     '| Показатель | Одна ошибка, постоянный | Одна ошибка, адаптация | Две ошибки, постоянный |',
     '|---|---|---|---|']
    table=[]
    def add(label,values):table.append([label]+list(values))
    add('Код (n,k,t)',('(39,32,1)','(39,32,1)','(44,32,2)'))
    add('Полезная / кодовая / выделенная память, байт',('524288 / 638976 / 786432','524288 / 638976 / 786432','524288 / 720896 / 786432'))
    add('Упаковка; read / write / RMW',('3 отдельных x16; 3 / 3 / 6 beat',)*3)
    add('Период обязательной опоры, с; k',
        (f"{fmt(F(r['period']['nominal_ns'],10**9),9)}; {r['k_passes']}" for r in rows))
    add('Правило',('постоянный заданный календарь',f"own ERR90/180с; FAST или опора{rows[1]['k_passes']}; inverse-address T119",'постоянный заданный календарь'))
    add('Q_T, верх за весь срок',('≤'+up(r['risk']['upper'],15) for r in rows))
    add('Запас epsilon−U_Q, нижний; доля epsilon',
        (fmt(r['risk']['slack'],12)+'; '+pct(r['risk']['relative_slack'],5,False) for r in rows))
    add('Основание вероятности',('T196(5), moment+E-cross','новый T196(7)/T119: joint J, W/ell/phase и coupling E-cross','T196(5),(6), cubic/mixed/direct+E-cross'))
    add('SRAM: интервал для выбранного кандидата; +B_ctl',
        (pct(r['cost']['core_SRAM_fraction_lower'],6,False)+' … '+pct(r['cost']['core_SRAM_fraction_upper'],6)+(' при v=0' if i==1 else '') for i,r in enumerate(rows)))
    add('SRAM: безопасный верх при любых history/veto; +B_ctl',
        (pct(r['cost']['all_history_SRAM_core_upper'],6) for r in rows))
    add('Extra source-veto v, сообщений/с',('нет адаптивного канала',
        'upper=min('+pct(a['all_history_SRAM_core_upper'])+', '+pct(a['core_SRAM_fraction_upper'])+' + '+up(100*a['veto_core_fraction_slope_per_notification_per_s'],9)+'·v процентных пунктов); CPU/traffic отдельно','нет адаптивного канала'))
    add('Полный префикс инициализации SRAM, мс',
        (up(r['cost']['initialization']['full_prefix_bus_ns']/10**6,6)+'; также включён /T' for r in rows))
    add('R / E / full32 write, верх нс',
        (' / '.join(up(x,6) for x in (r['timing']['control_E_ns']-(56*F(cfg['service']['clock_upper'])),r['timing']['control_E_ns'],r['timing']['app_write_ns'])) for r in rows))
    add('Пик SRAM на каждом1мс, верх; +B_ctl,1ms',
        (pct(r['timing']['peak_bus_core_upper'])+'; остаток до80% '+pct(r['timing']['peak_bus_remaining_for_other_work'],6,False) for r in rows))
    add('Ответ приложению, верх; запас до3мкс, нс',
        (up(r['timing']['app_response_upper_ns'],6)+'; '+fmt(r['timing']['app_deadline_slack_ns'],6) for r in rows))
    add('Цели карты: Q≤0.5epsilon; latency≤2.4мкс; peak≤64%',
        ('Q: да; latency: нет; peak: '+('да' if r['timing']['peak_target_slack']>=0 else 'нет') for r in rows))
    add('Кодек: плотная ROM + регистры',
        (str(resources[str(r['t'])]['lookup_bytes'])+' байт + UNKNOWN' for r in rows))
    add('Кодек: syndrome / correction / encoder, XOR',
        (' / '.join(str(resources[str(r['t'])][key]) for key in ('syndrome_two_input_xors','correction_two_input_xors','encoder_two_input_xors')) for r in rows))
    add('Decode / encode, upper операций/с',
        (up(r['cost']['full_cost_rates']['decodes'],3)+' / '+up(r['cost']['full_cost_rates']['encodes'],3)+(' при v=0' if i==1 else '') for i,r in enumerate(rows)))
    add('Полезная нагрузка, байт/с; заголовки отдельно',
        (up(r['cost']['payload_rate_Bps'],6) for r in rows))
    add('Контроллер: cuts / decisions, операций/с',
        (up(r['cost']['full_cost_rates']['cuts'],3)+' / '+up(r['cost']['full_cost_rates']['decisions'],3) for r in rows))
    add('Память транспорта+loss, байт; остальное параметрически',
        (str(r['cost']['transport_plus_loss_state_bytes'])+' + policy/payload/registers' for r in rows))
    add('Полная CPU / энергия / LUT / BRAM цена',
        ('CPU=Σq_a c_a/1e9; J=TΣq_a e_a+idle·T; hardware resources UNKNOWN',)*3)
    add('Неизвестные caps',('RAM/LUT/BRAM/CPU/energy: UNKNOWN; допустимость не установлена',)*3)
    add('Добавочная задержка decode при сохранении прочих полей, нс',
        ('≤'+fmt(r['timing']['extra_decode_nominal_ns_limit'],6)+('; ресурсный предел, новый Q требует пересчёта' if i==1 else '; доп. controller work отдельно') for i,r in enumerate(rows)))
    add('Оптимум класса / физический победитель',('не установлен',)*3)
    lines += ['| '+' | '.join(v)+' |' for v in table]
    cmp=result['conditional_bus_comparison']
    lines += ['',
     'B_ctl — отдельная доля занятости SRAM контроллером; её нельзя молча',
     'занулить. Она должна укладываться в остаток и сохранять mandatory/app',
     'окна. В условной serial-модели весь decode/encode уже включён в SRAM.',
     'Поэтому кодек дополнительно оплачивается площадью/энергией, а не второй',
     'такой же bus-статьёй. Коэффициенты полного вектора — [results.json](results.json).','',
     'R1: repair-upper=min(S_upper,2F_parent+U_Q N_hard). Позднее рождение',
     'внутри E может потребовать две исправляющие записи; read/hold уже покрывал',
     'два ERR и не увеличен повторно. [Свидетели и точные поправки](repair-validation.json).','',
     'По одной SRAM-координате upper t2 ниже lower предъявленной адаптивной',
     'опоры. Допустимая разность прочих bus-затрат t2−adaptive меньше '+
     pct(cmp['allowance_for_t2_extra_bus_fraction'],6,False)+' от полного времени.',
     'При фиксированных счётчиках формальный ценовой порог decode44 — '+
     fmt(cmp['extra_t2_decode_bus_ns_cost_threshold'],3)+'нс, но сервис допускает',
     'лишь '+fmt(cmp['service_limit_extra_t2_decode_ns'],6)+'нс при остальных',
     'неизменных полях. На этой границе Q и цена repairs пересчитаны:',
     'U_Q≤'+up(cmp['t2_at_service_decode_limit']['Q_upper'],15)+', SRAM≤'+
     pct(cmp['t2_at_service_decode_limit']['SRAM_core_upper'])+'.',
     'Больший предел требует нового календаря и расчёта.',
     'Это сравнение выбранных кандидатов; общий победитель по энергии/площади/',
     'CPU и оптимум класса из него не следуют. При неизвестном v для адаптации',
     'используется hard upper, а не значение среза v=0.','',
     'Новая информационная строка и все q-клетки: [informational.json](informational.json),',
     '[обоснование переноса](../INFORMATIONAL.md). Верх цены адаптации при v=0',
     ('ниже' if cmp['adaptive_upper_below_selected_t1_fixed_lower'] else 'не ниже')+' lower выбранного t1-fixed; это не lower всего fixed-класса.',
     'При прочих равных такой запас сохраняется для v<'+
     fmt(cmp['extra_veto_rate_before_losing_selected_fixed_lower_comparison'],3)+' дополнительных уведомлений/с.',
     'Неизвестную разность controller-цены также нужно вычесть из этого запаса.','',
     '12 заранее объявленных p2/p3-срезов: [sensitivity.json](sensitivity.json).',
     'Периоды в них не подгоняются; direct, 1+2, 2+2 и E-cross сохранены.',
     'Для адаптации в смеси это **только mandatory-диагностика**: перенос',
     'информационного singleton-сертификата на новый нижний канал не заявлен.',
     'Физические p_s, interword-группы, delta_env и delta_init остаются UNKNOWN.',
     'Остаток и условия применения: [REPORT](../REPORT.md), [CONDITIONS](../CONDITIONS.md).','']
    return '\n'.join(lines).encode('utf-8')


def build(repair_only=False):
    sources=verify();raw=(HERE/'common-input.json').read_bytes();cfg=json.loads(raw)
    agreement=json.loads((HERE/'agreement.json').read_text(encoding='utf-8'))
    if agreement['common_input_sha256']!=digest(raw):raise ValueError('agreement input binding mismatch')
    frozen=frozen_snapshot()
    result=calculate(cfg,frozen['information'] if repair_only else None)
    if repair_only:
        resources=frozen['result']['resources'];validation=frozen['validation']
    else:
        resources={str(t):Code(t).resources() for t in (1,2)}
        old=codec_checks();new=comparison_checks(cfg,result);info_check=information_checks(cfg,result['informational_certificate'])
        validation=dict(count=old['count']+new['count']+info_check['count'],functional_codec_and_cost=old,
                        new_comparison=new,informational_transfer=info_check,previous_stage1_4_changed=False,
                        independent_scientific_acceptance=False)
    repair_validation=repair_checks(cfg,result,frozen)
    sensitivity=result.pop('sensitivity');information=result.pop('informational_certificate')
    result.update(status='CONDITIONAL_NUMERICAL_TABLE_READY_FOR_REVIEW',
        common_input_sha256=digest(raw),agreement=agreement,source_manifest=sources,
        resources=resources,implementation_sha256={p.name:digest(p.read_bytes()) for p in sorted(HERE.glob('*.py'))},
        service_contract_sha256=digest((HERE/'SERVICE.md').read_bytes()),
        scientific_inputs_in_previous_stages_changed=False,transport_changed=False)
    # render needs sensitivity only as a link, not as a second comparison table.
    files={'results.json':encode(result),'sensitivity.json':encode(sensitivity),'informational.json':encode(information),
           'validation.json':encode(validation),'table.md':render(cfg,result,resources),
           'repair-validation.json':encode(repair_validation)}
    for name in ('sensitivity.json','informational.json','validation.json'):
        if digest(files[name])!=frozen['output_sha256'][name]:
            raise ValueError('R1 changed frozen scientific/validation output: '+name)
    return files,result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--record',action='store_true')
    p.add_argument('--repair-only',action='store_true',help='R1 price replay with pinned v4 information/203-check evidence; does not rerun them')
    p.add_argument('--require-agreement',action='store_true',help='require a specific theorist service/row signature, not just engineering alignment')
    args=p.parse_args();files,result=build(repair_only=args.repair_only)
    signed=bool(result['agreement']['theorist'].get('certificate_sha'))
    if args.require_agreement and not signed:
        print(json.dumps(dict(numerical_table_ready=True,specific_theory_signature=False,
             reason='new service and calculated rows submitted; this is not independent acceptance'),indent=2))
        return 2
    out=HERE/'outputs';out.mkdir(exist_ok=True)
    for name,raw in files.items():
        if args.record:(out/name).write_bytes(raw)
        elif (out/name).read_bytes().replace(b'\r\n',b'\n')!=raw:raise ValueError('replay mismatch: '+name)
    print(json.dumps(dict(numerical_table_reproduced=True,
          executed_checks=json.loads(files['repair-validation.json'])['count']+(0 if args.repair_only else json.loads(files['validation.json'])['count']),
          historical_checks_reused=json.loads(files['validation.json'])['count'] if args.repair_only else 0,
          informational_search_repeated=not args.repair_only,specific_theory_signature=signed,
          output_sha256={k:digest(v) for k,v in files.items()}),indent=2))
    return 0


if __name__=='__main__':sys.exit(main())
