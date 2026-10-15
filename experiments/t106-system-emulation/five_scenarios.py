"""Unify checked evidence; never substitute a prefix for the full burst."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from burst_run_inputs import build

HERE=Path(__file__).resolve().parent
OUT=HERE/'outputs'
REPO=HERE.parents[1]


def load(name):
    return json.loads((OUT/name).read_text())


def normalize(case,mode,result,meta):
    cold='ERR_events' in result  # historical schema only
    h=result['horizon_ns']
    work=result['bus_work_ns']
    if cold:
        app_read,app_write=work['app_read'],work['app_write'];control=work['control']
        extra=result['corrective_extra_within_control_ns'];total=sum(work.values())
    else:
        apps=result.get('application_work_ns',{'read':0,'write':0})
        app_read,app_write=apps['read'],apps['write'];total=work;control=work-app_read-app_write
        extra=result.get('control_corrective_extra_ns',56*result['err_events'])
    assert total==control+app_read+app_write
    assert total/h==result['mean_bus_fraction']
    cpu={k:meta.get(k,0) for k in
         ('ARM_instructions_runtime','ARM_instructions_including_boot','completed_driver_visits',
          'represented_full_services','represented_driver_visits','represented_MMIO_reads',
          'represented_MMIO_writes')}
    cpu['MMIO_observed']=meta['MMIO'];cpu['represented_ISA_count']=None
    cpu['actual_ARM_time_ns']=None;cpu['CPU_use_fraction_measured']=None
    cpu['allocated_cores']=int(mode=='adaptive')
    return dict(scenario=case,mode=mode,horizon_ns=h,
        mean_bus_fraction=result['mean_bus_fraction'],peak_any_1ms_fraction=result['peak_any_1ms_fraction'],
        max_application_delay_ns=result.get('observed_model_max_application_ns') if cold else result.get('max_application_delay_ns'),
        completed_operations=result['completed_operations'],
        unfinished_operations=result['unfinished_operations_at_horizon'] if cold else result['unfinished_operations'],
        application_completed=result.get('application_completed',0),
        ERR_events=result['ERR_events'] if cold else result['err_events'],
        physical_alias_writes=result['physical_alias_writes'],
        bus_work_ns=dict(control_base_including_partial=control-extra,control_correction_extra=extra,
                         application_reads=app_read,application_writes=app_write,total=total),
        model_full_service_ns=result['model_max_cut_to_cut_ns'] if cold and mode=='adaptive'
            else result.get('model_full_service_ns') if mode=='adaptive' else None,
        first_exceedance_relative_ns=result.get('first_exceedance_relative_ns'),
        CPU=cpu)


def collect(require_full=True):
    rows=[];missing=[]
    acc=load('accel-summary.json')['results'];sparse=load('sparse-summary.json')['results']
    for case,name in ((1,'quiet'),(2,'burst'),(3,'loss'),(4,'cold'),(5,'memory')):
        for mode in ('adaptive','fixed'):
            if case==2:
                path=OUT/f'burst2-burst-{mode}-skip-checked.json'
                if not path.exists():
                    missing.append(f'complete scenario2/{mode}');continue
                report=json.loads(path.read_text())
                assert report['scope']=='complete frozen scenario2, digital model ONLY'
                for p,h in report['sha256'].items():
                    assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
                result=report['results'];meta=load(f'burst2-burst-{mode}-skip.json')
                assert meta['stimulus']==build()
                assert result['horizon_ns']==363900_000_000_000 and result['injections']==5237
            elif case==4:
                stem=f'burst-cold-envelope-{mode}-skip'
                path=OUT/f'{stem}-checked.json'
                if not path.exists():
                    missing.append(f'scenario4 in-envelope/{mode}');continue
                report=json.loads(path.read_text())
                for p,h in report['sha256'].items():
                    assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h,p
                meta=load(stem+'.json');result=report['results']
            else:
                stem=f'{"sparse" if case==5 else "accel"}-{name}-{mode}-skip'
                result=(sparse if case==5 else acc)[stem];meta=load(stem+'.json')
            rows.append(normalize(case,mode,result,meta))
    if require_full:assert not missing,('full delivery is not ready',missing)
    if not missing:
        a,b=[load(f'burst2-burst-{mode}-skip.json') for mode in ('adaptive','fixed')]
        assert a['stimulus']==b['stimulus']
        for k in ('injections.txt','application.txt'):assert a['input_sha256'][k]==b['input_sha256'][k]
    previous=load('summary.json')
    return dict(status='complete_digital_evidence_pending_review' if not missing else 'INCOMPLETE',
        missing=missing,rows=rows,
        historical_cold_stress=[normalize(4,m,load(f'cold-{m}.json')['check'],load(f'cold-{m}.json'))
            for m in ('adaptive','fixed')],
        common_resources={k:previous[k] for k in
            ('resources_reused_not_resynthesized','STA_reused_not_rerun','startup_bytes','firmware_bytes','OCM_reserved_bytes')},
        physical_board_available=None,actual_ARM_time_ns=None,ARM_WCET_ns=None,Q_T_certified_by_emulation=False,
        constant='same PL image, all-slot FAST; no claim of best constant class',
        important_scope=['all numbers calculated in nominal digital model',
            'main comparison uses model service188160ns; historical cold stress kept separately',
            'historical cold20us application spacing is outside joint r4; NOT an in-envelope cost',
            'no application in1/2/3; app delay not applicable, not zero',
            'different scenarios are not combined into a mission-average gain',
            'lossless traces independently replayed; source/ABI/tool dependencies declared',
            'injections continue after first exceedance; no free end drain'])


def markdown(data):
    text=['# Сравнение пяти сценариев — цифровая модель','',
        '**Статус: '+data['status']+'**. Q(T) за срок эмуляцией не доказывается.','',
        '| Сценарий / режим | Горизонт, с | Средняя шина, % | Max любого1мс, % | Ответы приложения / max, нс | Полные / неполные операции |',
        '|---|---:|---:|---:|---:|---:|']
    for r in data['rows']:
        delay=r['max_application_delay_ns']
        text.append(f"| {r['scenario']} / {r['mode']} | {r['horizon_ns']/1e9:g} | "
            f"{100*r['mean_bus_fraction']:.6f} | {100*r['peak_any_1ms_fraction']:.6f} | "
            f"{r['application_completed']} / {delay if delay is not None else 'не применимо'} | "
            f"{r['completed_operations']} / {r['unfinished_operations']} |")
    if data['missing']:text+=['','Не выполнено: '+', '.join(data['missing'])+'.']
    text+=['','Полные CPU/MMIO/шина по видам — five-scenarios.json. CPU и шина не складываются.',
        'Числа операций включают точно свёрнутые пустые интервалы; не все операции исполнялись буквально.',
        'ПЛИС — один и тот же принятый образ; аппаратные ARM-время/WCET не измерены.','']
    return '\n'.join(text)


def record_table(data, output=OUT):
    """Publish only a complete table; reject changed prior data before writing."""
    assert data['status']=='complete_digital_evidence_pending_review' and not data['missing']
    documents={output/'five-scenarios.json':json.dumps(data,indent=2,allow_nan=False)+'\n',
               output/'five-scenarios.md':markdown(data)}
    for path,content in documents.items():
        if path.exists():
            assert path.read_text()==content,('published table changed; preserve and investigate',str(path))
    for path,content in documents.items():
        if not path.exists():path.write_text(content)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-incomplete',action='store_true')
    p.add_argument('--record',action='store_true')
    p.add_argument('--wait-for-full',action='store_true',help='In-task dependency wait, no publication or notifications')
    a=p.parse_args()
    if a.wait_for_full:
        assert not a.allow_incomplete
        deadline=time.monotonic()+8*3600
        while True:
            state=json.loads((HERE/'.build/full-profile-v2/state.json').read_text())
            if state['status']=='verified_both':break
            if state['status']!='running':raise RuntimeError(('full execution failed',state))
            if time.monotonic()>deadline:raise TimeoutError('full profile did not finish within8h')
            time.sleep(20)
    data=collect(not a.allow_incomplete)
    if a.record:
        assert not a.allow_incomplete,'incomplete tables are previews, not published final outputs'
        record_table(data)
    else:print(markdown(data))
