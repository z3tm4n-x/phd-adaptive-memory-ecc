"""Render one consolidated table and one two-panel scientific figure from JSON.

No model/Q computations. PNG and SVG are two exports of the same figure.
"""
import argparse
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
import io
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext
import run as model

HERE=Path(__file__).resolve().parent


def integer(x,upper=True):
    x=F(x)
    value=model.accepted.ceil(x) if upper else x.numerator//x.denominator
    return f'{value:,}'.replace(',',' ')


def fixed(x,places=6,upper=True):
    with localcontext() as ctx:
        ctx.prec=80;ctx.rounding=ROUND_CEILING if upper else ROUND_FLOOR
        x=F(x);d=Decimal(x.numerator)/Decimal(x.denominator)
        return format(d.quantize(Decimal(1).scaleb(-places),rounding=ctx.rounding),'f')


def sci(x,upper=True):
    x=F(x)
    if not x:return '0'
    with localcontext() as ctx:
        ctx.prec=80;ctx.rounding=ROUND_CEILING if upper else ROUND_FLOOR
        d=Decimal(x.numerator)/Decimal(x.denominator)
        d=d.quantize(Decimal(1).scaleb(d.adjusted()-5),rounding=ctx.rounding)
        return f'{d:.5E}'.replace('E+','e+').replace('E-','e-')


def method(row,name):
    v=row['methods'][name]
    if 'alias' in v:return method(row,v['alias'])
    return v


def bound(row,name):
    v=method(row,name)
    return row['price_bounds'][v['price']] if v.get('pair') else None


def cost(row,name,total=False):
    b=bound(row,name)
    if b is None:return 'нет кандидата'
    key='all_known_upper_s' if total else 'protection_upper_s'
    return ' / '.join(integer(b['price']['coordinates'][x][key]) for x in ('bus','serial'))


def short_cost(row,name):
    if method(row,name).get('price')==method(row,'F_max').get('price'):
        return '=F+'
    return cost(row,name)


def bracket(v):
    if v.get('pair') is None:return 'нет кандидата'
    return '['+sci(v['Q_lower'],False)+'; '+sci(v['Q_upper'])+']'


def pair(v):
    return '('+','.join(map(str,v['pair']))+')' if v.get('pair') else '—'


def label(row):
    c=row['cell'];size=F(c['useful_bytes'],2**20)
    return f"{c['id']} · {float(size):g} МиБ · α={float(F(c['alpha'])):g} · ε={float(F(c['epsilon'])):g}"


def table(data):
    rows=list(data['cells'].values());assert len(rows)==14 and data['complete']
    assert all(method(r,'F_menu')['pair']==method(r,'F_max')['pair'] for r in rows)
    out=['# Общая таблица 14 точек #186','',
         '28.10.2026. Один объект: (39,32), T=315576000 с, прежний сервис; W/α/ε — по [закреплённому списку](inputs.json).',
         'c00 загружена из принятого PR296 по SHA256; остальные 13 вычислены. Это **условные модельные результаты**, не физическая квалификация.',
         '[Вывод, условия и рекомендация](REPORT.md); [точные числа](result.json); [один рисунок](cost.png) ([SVG](cost.svg)).','',
         '## Абсолютная цена за весь срок','',
         'В каждой числовой ячейке **bus / serial, секунд за T**. Нижние границы округлены вниз, верхние вверх.',
         'F− — необходимый низ **всего** постоянного класса; F+ — отдельный достаточный кандидат (11).',
         'Во всех 14 точках он также самый дешёвый постоянный член уже полученного меню; это не доказанный глобальный оптимум.',
         'Столбцы методов — верх **известной части защиты** (read+repair, исключения, края и работа после первого превышения).',
         'Полная координата дополняется **T·c_control,x**; неизвестный коэффициент не равен 0. CPU/энергия — отдельные параметры.',
         '`=F+` означает одно и то же исполнение и цену, а не повторный расчёт. Уточнённый N+ совпадает с M в каждой точке.','',
         '| ID | МиБ; α; ε | F−, защита | F+, защита | N0, защита | N+ пиковый, защита | M=N+ уточнённый, защита | M+app+init, известный верх |',
         '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        c=r['cell'];lo=r['fixed_class_lower_for_price']
        low='—*' if lo['P0_s'] is None else ' / '.join(integer(lo['cost'][x]['lower_s'],False) for x in ('bus','serial'))
        coords=f"{float(F(c['useful_bytes'],2**20)):g}; {float(F(c['alpha'])):g}; {float(F(c['epsilon'])):g}"
        out.append(f"| {c['id']} | {coords} | {low} | {cost(r,'F_max')} | {short_cost(r,'N0')} | {short_cost(r,'Nplus_box')} | {short_cost(r,'M')} | {cost(r,'M',True)} |")
    out+=['','*В c05/c07 зарегистрированные нижние свидетели не дали положительного необходимого ценового низа.',
          'В расчёте используется тривиальный 0; это **не** установленная нулевая цена F и не разрешение OFF.',
          'Известная верхняя цена включает (12), в частности `min(N_R,2F+U_Q·Nmax)` repair; при больших ε верх может платить repair при каждом чтении.',
          'Цена управления и физические вероятности не определены этой границей.','',
          '## Периоды и границы вероятности','',
          'Пара — (kH,kL); номинальные периоды равны k·P1 из ресурсной таблицы ниже. Q* — супремум по объявленному классу.',
          'Низ — допустимый свидетель; он не утверждается для каждой среды. Для N0 используются действительные (8)/(11), **не** V0.',
          '`?` означает нижняя≤ε<верх: нарушение **не доказано**. Для остальных выбранных строк верх≤ε.',
          'Ни одна клетка ε=10⁻⁴ не заменена другим входом; достаточные кандидаты найдены в обеих.','',
          '| ID | F+: k; [Q−;Q+] | N0: пара; [Q−;Q+] | N+ пиковый: пара; [Q−;Q+] | M=N+ уточнённый: пара; [Q−;Q+] |',
          '|---|---|---|---|---|']
    for r in rows:
        f=method(r,'F_max');vs=[]
        for name in ('N0','Nplus_box','M'):
            v=method(r,name)
            if v.get('price')==f.get('price'):
                vs.append('=F+')
            else:
                vs.append(pair(v)+'; '+bracket(v)+(' **?**' if v.get('Q_status')=='unresolved' else ''))
        out.append('| '+r['cell']['id']+' | '+str(f['pair'][0])+'; '+bracket(f)+' | '+' | '.join(vs)+' |')
    out+=['','В c01/c02/c07 исправление N+ получает достаточный допуск; допустимость выбранного N0 остаётся неустановленной.',
          'Это зазор оценок, не доказанное нарушение N0 и не доказательство необходимости особого оконного алгоритма.',
          'Здесь M выбирает другие периоды, а сильному N+ разрешено ровно это же уточнение.','',
          '## Общие app/init и ресурс','',
          'Прежнее приложение: read, без полезных записей/ремонта/ERR; app за T:',
          '`bus ∈ [14989.40873533;15305.28137090] с`, `serial ∈ [21300.73939351;21616.73825697] с`.',
          'Оно не отменено из относительных сравнений. Init до 0 оплачена полностью, но не вычтена из ресурса внутри T.','',
          '| Полезный банк | W | Требуемая raw-память, МиБ | P1 номинальный, мс | P1− / P1+, мс | Init bus / serial, с, верх |',
          '|---|---:|---:|---:|---:|---:|']
    resources={r['resource']['words']:r['resource'] for r in rows}
    for W,res in sorted(resources.items()):
        cal=res['calendar'];ini=res['initialization']
        out.append(f"| {float(F(res['useful_bytes'],2**20)):g} МиБ | {W} | {float(F(res['raw_storage_required_bytes'],2**20)):g} | {fixed(F(cal['nominal_minimum_full_pass_cycle_ns'],10**6))} | {fixed(F(cal['cycle_lower_ns'],10**6),9,False)} / {fixed(F(cal['cycle_upper_ns'],10**6),9)} | {fixed(ini['pure_bus_upper_s'],12)} / {fixed(ini['serial_upper_s'],12)} |")
    out+=['','Для всех выбранных опор: прежний пик с полным management-slot≤**67.936576476%** в любом 1 мс при cap 80%;',
          'ответ приложения≤**2533.01712 нс** при 3000 нс. Запасы≥12.063423524 п.п. и 466.98288 нс соответственно.',
          'Максимальный необходимый serial-низ F в сетке —9.43010065%, ниже доступного верха79.9932502030%.',
          'Все 14 F+ имеют достаточный Q и сохраняют условную сервисную область; постоянный класс ресурсом не исключён.',
          'Неизвестное управление должно поместиться в ту же область; положительная средняя разность не заменяет локальные сроки/слоты.','',
          '## Оконные точки: цена сведений и границы выигрыша','',
          'Ниже учитываются app/init. При неизвестном u_M применяется `G(u)=L/(U_M+T·u_M)`.',
          'Таблица показывает G(0) как границу для параметра, **не как доказанную полную экономию при бесплатном управлении**. Положительная Δ даёт достаточный бюджет',
          'дополнительного управления для выигрыша против указанного F-кандидата даже без использования его неизвестных дополнительных расходов.',
          'Класс F и один его кандидат не подменяют друг друга.','',
          '| ID | H+, с | G_class bus / serial | G_candidate bus / serial | Δ_candidate, мкс/с bus / serial | Доля serial: F+ / M, известный верх |',
          '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        v=method(r,'M');e=r['executions'][v['execution']]
        if e['constant']:continue
        b=bound(r,'M');g=b['comparisons']
        ratios=lambda key:' / '.join(fixed(g[x][key],6,False) for x in ('bus','serial'))
        cg='—*' if r['fixed_class']['excluded_from'] is None else ratios('class_ratio_lower_known')
        delta=' / '.join(fixed(g[x]['candidate_extra_management_budget_per_s']*10**6,6,False) for x in ('bus','serial'))
        fs=bound(r,'F_max')['price']['coordinates']['serial']['protection_upper_fraction']*100
        ms=b['price']['coordinates']['serial']['protection_upper_fraction']*100
        out.append(f"| {r['cell']['id']} | {fixed(e['hold']['upper_s'],9)} | {cg} | {ratios('candidate_ratio_lower_known')} | {delta} | {fixed(fs,6)}% / {fixed(ms,6)}% |")
    out+=['','У остальных 11 точек выбранное M тождественно F+: коэффициент между этими исполнениями 1, экономия 0.',
          'Во всей сетке нет положительного бюджета выигрыша M над необходимым низом **всего** F.',
          'Для c07 уменьшение достаточного верха само по себе не замыкает даже сравнение с конкретным F: нижняя и верхняя цены перекрываются.',
          'CPU, энергия, состояние/код/буферы, WCET и физическая калибровка остаются явно неизвестными; [отчёт](REPORT.md) содержит рекомендацию.','']
    return '\n'.join(out)


def figure(data):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,'svg.hashsalt':'t186-map14-fixed'})
    rows=list(data['cells'].values())
    fig,axs=plt.subplots(1,2,figsize=(14.5,9.7),sharey=True)
    all_positive=[]
    for r in rows:
        for x in ('bus','serial'):
            lo=r['fixed_class_lower_for_price']['cost'][x]['lower_s']
            if lo>0:all_positive.append(float(lo))
            all_positive.extend(float(bound(r,n)['price']['coordinates'][x]['protection_upper_s']) for n in ('F_max','M'))
    xmin=min(all_positive)/1.8;xmax=max(all_positive)*1.8
    for ax,coord,title in zip(axs,('bus','serial'),('Чистая SRAM-шина','Последовательное обслуживание с кодеком')):
        for y,r in enumerate(rows):
            if y%2==0:ax.axhspan(y-.47,y+.47,color='#f2f5f8',zorder=0)
            lo=float(r['fixed_class_lower_for_price']['cost'][coord]['lower_s'])
            up=float(bound(r,'F_max')['price']['coordinates'][coord]['protection_upper_s'])
            mp=float(bound(r,'M')['price']['coordinates'][coord]['protection_upper_s'])
            if lo>0:
                ax.plot([lo,up],[y-.09,y-.09],color='#809bb4',lw=1.5,zorder=2)
                ax.scatter([lo],[y-.09],marker='<',s=43,color='#163e65',zorder=3)
            else:
                ax.text(xmin*1.05,y-.11,'низ 0*',va='center',ha='left',fontsize=8,color='#53677d')
            ax.scatter([up],[y-.09],marker='o',s=37,facecolors='white',edgecolors='#163e65',linewidths=1.4,zorder=3)
            ax.scatter([mp],[y+.11],marker='D',s=30,color='#bd541b',zorder=4)
        ax.set_xscale('log');ax.set_xlim(xmin,xmax);ax.set_ylim(len(rows)-.4,-.6)
        ax.xaxis.set_major_locator(LogLocator(base=10));ax.xaxis.set_major_formatter(LogFormatterMathtext())
        ax.grid(axis='x',which='major',color='#b5c0cc',alpha=.65,linewidth=.7)
        ax.grid(axis='x',which='minor',color='#d8e0e8',alpha=.5,linewidth=.35)
        ax.set_title(title,pad=16);ax.set_xlabel('Занятость за 10 лет, с · логарифмическая шкала')
        ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
    axs[0].set_yticks(range(len(rows)),[label(r) for r in rows],fontsize=9)
    from matplotlib.lines import Line2D
    handles=[Line2D([],[],marker='<',color='#163e65',linestyle='none',label='Необходимый низ всего F'),
             Line2D([],[],marker='o',markerfacecolor='white',color='#163e65',linestyle='none',label='Верх достаточного F+'),
             Line2D([],[],marker='D',color='#bd541b',linestyle='none',label='Верх M = уточнённого N+')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.61,.925),ncol=3,frameon=False,fontsize=9.5)
    fig.suptitle('14 точек: цена защиты в принятом семействе p + r',x=.59,y=.97,fontweight='bold',fontsize=16)
    fig.text(.27,.077,'Известные затраты защиты; к верхам добавляется T·cуправления. Приложение и начало — отдельно в таблице.',fontsize=9)
    fig.text(.27,.052,'Горизонтальный отрезок соединяет необходимый низ и достаточный верх F; это не доверительный интервал.',fontsize=9)
    fig.text(.27,.027,'* Положительный необходимый низ не получен.  α=0 — контроль известного профиля.  c00 загружена из PR296.',fontsize=9)
    fig.subplots_adjust(left=.27,right=.985,top=.845,bottom=.14,wspace=.12)
    outputs={}
    for ext in ('svg','png'):
        buf=io.BytesIO()
        meta={'Date':None,'Creator':'t186 map-14 render.py'} if ext=='svg' else {'Software':'t186 map-14 render.py'}
        fig.savefig(buf,format=ext,dpi=160,metadata=meta)
        raw=buf.getvalue()
        # Matplotlib emits trailing spaces in SVG paths; retain path tokens
        # and normalize whitespace so Git and Windows checkouts are stable.
        if ext=='svg':
            raw=b'\n'.join(line.rstrip() for line in raw.splitlines())+b'\n'
        outputs[ext]=raw
    plt.close(fig)
    return outputs


def main(check=False):
    data=model.accepted.numeric(json.loads((HERE/'result.json').read_text('utf-8')))
    assert data['complete'] and data['total_cells']==14
    text=table(data).encode('utf-8')
    images=figure(data)
    outputs={'TABLE.md':text,**{'cost.'+ext:raw for ext,raw in images.items()}}
    for name,raw in outputs.items():
        path=HERE/name
        if check:
            existing=path.read_bytes()
            if name.endswith(('.md','.svg')):
                existing=existing.replace(b'\r\n',b'\n')
            assert existing==raw,name
        else:path.write_bytes(raw)
    print(json.dumps(dict(files=list(outputs),matplotlib=matplotlib.__version__,checked=check,model_recomputed=False)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true')
    main(p.parse_args().check)
