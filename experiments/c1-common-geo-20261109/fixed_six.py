"""Constant periods and lifetime protection cost for the agreed C1/C2 class."""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import sys
from coverage import CAP, environment, write_or_check
from prior import HERE, EXPERIMENTS, activate


def calculate(previous):
    activate(previous)
    import fixed
    sys.path.insert(0,str(EXPERIMENTS/'regime-map-methodology-20261019/predictability-volume-20261028'))
    import resource_preflight as resource
    _,cfg=resource.load()
    base,T,allowance=environment()
    compat=json.loads((HERE/'growth.json').read_text(encoding='utf-8'))
    assert all(p['exact_feasible'] is True and p['constructed_feasible'] and p.get('within_exposure_quota',True)
               for p in compat['profiles'].values())
    R=base['B']-base['b']; duration=allowance/R
    # The high-at-start profile is allowed for every nonnegative g. Remove the
    # first second of the plateau for the lower bound, beyond every startup scan.
    env={'S1':CAP,'S2':base['b']**2*T+(base['B']+base['b'])*allowance,
         'B':base['B'],'b':base['b'],'tau':duration-1}
    rows=[]
    for size in (2**17,2**18,2**19):
        res=resource.preflight(cfg,size)
        w=res['words']
        assert fixed.period(w,1)[2]+fixed.DE<1
        for eps in (F(1,1000),F(1,10000)):
            r=fixed.row(res,eps,env)
            r['k2']={'nominal_period_s':fixed.period(w,2)[0],'Q_all_k_ge2_lower':
                     fixed.tail_lower(w,fixed.period(w,2)[0]*fixed.XP,env),
                     'Q_k2_upper':fixed.risk_upper(w,2,env,F(0))['total']}
            if r['candidate']:
                k=r['candidate']['k']
                r['candidate']['Q_lower']=fixed.tail_lower(w,fixed.period(w,k)[0]*fixed.XP,env)
                r['candidate']['at_direct_sensitivity']=[{'d':d,'Q_upper':fixed.risk_upper(w,k,env,d)['total']}
                                                         for d in fixed.DIRECT]
            r['application']=res['application']
            r['management_progress_ns']=res['resource']['guaranteed_management_progress_ns']
            r['physical_WCET']=False
            rows.append(r)
    return {'T':T,'D':fixed.DREF,'growth_s_inv2':compat['g_s_inv2'],'S1_max':CAP,'S2_max':env['S2'],
            'F':allowance,'plateau_s':duration,'lower_witness_plateau_used_s':env['tau'],
            'delta_exec':fixed.DELTA,'per_bit_rate':'nu/D','rows':rows}


def table(data):
    import fixed
    ifmt=lambda x,p=5:fixed.fmt(x,p)
    up=lambda x,p=5:fixed.fmt(x,p,True)
    def amount(cost,toward_upper):
        cv=up if toward_upper else ifmt
        return cv(cost['percent'])+' / '+cv(cost['s']/10**6)
    lines=['# Постоянные режимы на общем классе ГСО','',
           'Код (39,32), T=315 576 000 с, D₁=0. В колонках цены указаны проценты чистой шины и миллионы защитных секунд за весь срок. Нижние границы округлены вниз, верхние вверх. Номинальные периоды даны в миллисекундах.','',
           '| МиБ | ε | Pmin, мс | Q⁻…Q⁺ при непрерывном обходе | Верх шины при непрерывном обходе, % / млн с | Допустимый k / P, мс | Q⁺ кандидата | Необходимая цена класса, % / млн с | Достаточная цена кандидата, % / млн с |',
           '|---:|---:|---:|---:|---:|---|---:|---:|---:|']
    for r in data['rows']:
        c=r['continuous'];cl=r['necessary'];a=r['candidate'];p=c['price']['bus']
        continuous=amount({'percent':p['upper_percent'],'s':p['upper_s']},True)
        low=amount({'percent':cl['bus_lower_percent'],'s':cl['bus_lower_s']},False)
        if a:
            period=f"{a['k']} / "+ifmt(a['period_s'][0]*1000,10)+(' (непрерывный)' if a['k']==1 else '')
            q=up(a['risk']['total'],7)
            price=amount({'percent':a['price']['bus']['upper_percent'],'s':a['price']['bus']['upper_s']},True)
        else:
            period='класс исключён' if r['status']=='whole_class_excluded_conditional' else 'открыто'
            q=price='—'
        lines.append('|'+' | '.join([ifmt(r['MiB']),ifmt(r['epsilon']),ifmt(c['period_s'][0]*1000,10),
                     ifmt(c['Q_lower'],6)+'…'+up(c['risk']['total'],6),continuous,period,q,low,price])+' |')
    lines+=['','При исключении расписаний необходимая цена описывает ресурс, который понадобился бы гипотетическому допустимому периоду. Инициализация и приложение учтены отдельно. [Полные величины и секунды](six.json) · [Покрытие периодов, допущения и выбор](README.md).','']
    return '\n'.join(lines)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--previous',required=True,type=Path)
    p.add_argument('--check',action='store_true');args=p.parse_args()
    result=calculate(args.previous);write_or_check(HERE/'six.json',result,args.check)
    text=table(result);path=HERE/'TABLE.md'
    if args.check:
        if path.read_text(encoding='utf-8')!=text:raise SystemExit('Mismatch: TABLE.md')
    else:path.write_text(text,encoding='utf-8',newline='\n')
    print('Confirmed six schedules/limits')
