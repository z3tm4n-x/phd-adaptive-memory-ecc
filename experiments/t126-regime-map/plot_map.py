"""Russian categorical map. Float conversions are rendering only."""
import argparse
import json
from fractions import Fraction as F
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch

HERE=Path(__file__).resolve().parent
COLORS={'constant_sufficient':'#cce5d5','adaptation_needed_and_sufficient':'#aad3ea',
        'adaptive_sufficient_necessity_unknown':'#ddd0ea','period_class_excluded':'#edb6b6','unknown':'#e8e8ea'}


def draw(report, directory):
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.hashsalt':'t126-first-map'})
    fig=plt.figure(figsize=(15,11.8),layout='constrained')
    gs=fig.add_gridspec(3,1,height_ratios=[3.2,2.6,1.5])
    a=fig.add_subplot(gs[0]);b=fig.add_subplot(gs[1]);c=fig.add_subplot(gs[2])
    fig.suptitle('Карта выбора режима · первая ограниченная сетка T126\nУсловные модели, не квалификация памяти',fontsize=17)
    eps=[F('.01'),F('.001'),F('.0001')];budgets=[F('.01'),F('.1'),F('.5')]
    columns=[(262144,64000000),(262144,256000000),(1935832,64000000),(1935832,256000000)]
    rows=[x for x in report['rows'] if x['family']=='R0B_grid']
    for j,(W,R) in enumerate(columns):
        for i,(e,bu) in enumerate((e,bu) for e in eps for bu in budgets):
            r=next(x for x in rows if x['W']==W and x['R_eff_bit_s']==R and F(x['epsilon'])==e and F(x['quiet_budget'])==bu)
            a.add_patch(Rectangle((j,i),1,1,facecolor=COLORS[r['status']],edgecolor='white',linewidth=2))
            mark='*' if r['constant_excluded_T58'] else ('†' if r['constant_excluded_candidate_T126'] else '')
            label='Постоянный' if r['status']=='constant_sufficient' else 'Не установлено'+mark
            a.text(j+.5,i+.5,label,ha='center',va='center',fontsize=10)
    a.set(xlim=(0,4),ylim=(9,0));a.set_xticks([i+.5 for i in range(4)],['Малый / 64 Мбит/с','Малый / 256 Мбит/с','Большой / 64 Мбит/с','Большой / 256 Мбит/с'])
    a.xaxis.tick_top()
    a.set_yticks([i+.5 for i in range(9)],[f'ε={float(e):g}; бюджет {100*float(bu):g}%' for e in eps for bu in budgets])
    a.set_title('A1/A2 · Полное слово 39; один per-bit закон; полный диапазон периодов T58',loc='left',pad=35)
    a.set_xlabel('* Постоянный класс исключён по T58; † — только по кандидатной границе T126 (ещё не принята).\nДопустимость адаптации из исключения постоянного класса не следует.',labelpad=7)
    controls=[]
    for name,label in [('cy_T95_anchor','U + монитор · основной D*'),('cy_T95_control','U + монитор · контроль D*')]:
        controls.append((label,[x for x in report['rows'] if x['family']=='T95_control' and x['id'].startswith(name)]))
    for profile,stage,label in [('MCU_calibrated_write',2,'E + ERR · a≥0,9 · две ступени'),('MCU_calibrated_write',1,'E + ERR · a≥0,9 · одна ступень'),('singleton_write',2,'E + ERR · singleton · две ступени')]:
        controls.append((label,[x for x in report['rows'] if x['family']=='T114_control' and x['profile']==profile and x['growth']=='main' and x['stages']==stage and x['candidate_role']=='presented']))
    for i,(label,rr) in enumerate(controls):
        for j,bu in enumerate(budgets):
            r=next(x for x in rr if F(x['quiet_budget'])==bu)
            b.add_patch(Rectangle((j,i),1,1,facecolor=COLORS[r['status']],edgecolor='white',linewidth=2))
            s=r['status'];txt={'constant_sufficient':'Постоянный','adaptation_needed_and_sufficient':'Адаптация нужна\nи достаточна','unknown':'Не установлено'}.get(s,'Адаптация достаточна')
            b.text(j+.5,i+.5,txt,ha='center',va='center',fontsize=10)
    b.set(xlim=(0,3),ylim=(len(controls),0));b.set_xticks([.5,1.5,2.5],['Бюджет 1%','Бюджет 10%','Бюджет 50%']);b.xaxis.tick_top()
    b.set_yticks([i+.5 for i in range(len(controls))],[x[0] for x in controls])
    b.set_title('A3 · Прежние принятые контрольные классы при ε=0,001 · U и E не объединены',loc='left',pad=33)
    b.set_xlabel('Цена защиты с каналом и управлением; E включает общий допустимый поток приложения.\nРазные строки имеют разные предпосылки. Полные семейства и отказы — в map.json.',labelpad=8)
    cy=[x for x in report['rows'] if x['family']=='CY_new_input' and F(x['epsilon'])==F('.001') and F(x['quiet_budget'])==F('.01')]
    for i,r in enumerate(cy):
        c.add_patch(Rectangle((i,0),1,1,facecolor=COLORS['unknown'],edgecolor='white',linewidth=2))
        txt=f"{float(F(r['shield_g_cm2'])):g} г/см²\nS₂={float(F(r['S2_total'])):,.0f} с⁻¹\nНе установлено".replace(',',' ')
        c.text(i+.5,.5,txt,ha='center',va='center',fontsize=11)
    c.set(xlim=(0,4),ylim=(1,0),xticks=[],yticks=[])
    c.set_title('A3 · Новый отклик PDI + HEP: четыре толщины — один пример',loc='left',pad=12)
    c.set_xlabel('D*, совместное покрытие среды и квалификация ERR/сервиса неизвестны: все 36 узлов серые.\nA4: кривая другого образца найдена, численный перенос не замкнут. A5: орбита — вторая итерация.',labelpad=8)
    for ax in [a,b,c]:
        for sp in ax.spines.values():sp.set_visible(False)
        ax.tick_params(length=0)
    directory.mkdir(exist_ok=True,parents=True)
    fig.savefig(directory/'map.png',dpi=150,metadata={'Software':'T126 plot_map.py'})
    fig.savefig(directory/'map.svg',metadata={'Date':None,'Creator':'T126 plot_map.py'})
    plt.close(fig)
    svg=directory/'map.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',type=Path,default=HERE/'outputs');args=ap.parse_args()
    draw(json.loads((HERE/'outputs/map.json').read_text(encoding='utf-8')),args.output_dir)
