"""Static scientific map: discrete tested volumes, no interpolation."""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import sys
from table import directed

ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--deps-dir',type=Path,help='optional local matplotlib package directory')
args=ap.parse_args()
if args.deps_dir:sys.path.insert(0,str(args.deps_dir.resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE=Path(__file__).resolve().parent
result=json.loads((HERE/'outputs/result.json').read_text('utf-8'))
rows=sorted(result['rows'],key=lambda r:r['kib'])
fraction=lambda x:float(F(x))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.hashsalt':'t206-volume-v1'})
fig,(ax,mp)=plt.subplots(1,2,figsize=(13,5.7),layout='constrained')
xs=list(range(len(rows)))
for i,row in enumerate(rows):
    c=row['comparison']
    lo,hi=100*fraction(c['fixed_class_bus_lower']),100*fraction(c['fixed_witness_bus_upper'])
    au=100*fraction(c['adaptive_bus_upper'])
    ax.vlines(i-.11,lo,hi,color='#34495e',linewidth=3)
    ax.plot(i-.11,lo,'_',color='#34495e',markersize=15)
    ax.plot(i-.11,hi,'_',color='#34495e',markersize=15)
    ax.plot(i+.11,au,'v',color='#bc5c21',markersize=9)
    floor=100*fraction(row['price_gate']['certificate_bus_floor'])
    ax.plot(i+.11,floor,'_',color='#bc5c21',markersize=12,alpha=.6)
    gap=100*fraction(c['control_bus_sufficient_strict_below'])
    mp.bar(i,.27,width=.72,color='#edf0f3',edgecolor='#c4c9ce',linewidth=.6)
    if gap>0:
        mp.bar(i,gap,width=.72,color='#32966c')
        mp.plot([i-.36,i+.36],[gap,gap],color='#116b47',linestyle='--',linewidth=1.5)
        mp.text(i,gap+.009,directed(100*F(c['control_bus_sufficient_strict_below']),6,False),ha='center',va='bottom',fontsize=10)
    else:
        mp.text(i,.016,'выигрыш\nне доказан\nпри u = 0',ha='center',va='bottom',fontsize=9,color='#58616b')
for a in (ax,mp):
    a.set_xticks(xs,[str(r['kib']) for r in rows])
    a.set_xlabel('Долгоживущий банк, КиБ')
    a.spines[['top','right']].set_visible(False)
    a.grid(axis='y',alpha=.2)
    a.set_axisbelow(True)
ax.set_yscale('log')
ax.set_ylabel('Проверки и исправления: загрузка шины, %')
ax.set_title('Границы цены при u = 0',loc='left',fontweight='bold')
ax.legend(handles=[plt.Line2D([0],[0],color='#34495e',lw=3,label='Низ класса — верх fixed-свидетеля'),
                   plt.Line2D([0],[0],color='#bc5c21',marker='v',linestyle='',label='Верх выбранной адаптации'),
                   plt.Line2D([0],[0],color='#bc5c21',marker='_',linestyle='',label='Нижний предел вычисляемого верха')],
          loc='upper left',fontsize=9,frameon=False)
mp.set_ylim(0,.27)
mp.set_ylabel('Дополнительная загрузка управления u, п.п.')
mp.set_title('Достаточная область строгого выигрыша',loc='left',fontweight='bold')
mp.legend(handles=[Patch(facecolor='#32966c',label='Сертифицировано при u ниже границы'),
                   Patch(facecolor='#edf0f3',edgecolor='#c4c9ce',label='Сравнение не установлено')],
          loc='upper left',fontsize=9,frameon=False)
fig.suptitle('Фиксированный (39,32) · отдельный банк · 10 лет · ε = 0,001',fontsize=15,fontweight='bold')
fig.supxlabel('Четыре отдельные точки; интерполяции нет. Дополнительные veto: v = 0.\nСредний бюджет u не отменяет предельных сроков. Серая область не доказывает проигрыш.',fontsize=10)
out=HERE/'outputs'
fig.savefig(out/'volume-control-map.png',dpi=190)
svg=out/'volume-control-map.svg'
fig.savefig(svg,metadata={'Date':None})
svg.write_text('\n'.join(line.rstrip() for line in svg.read_text('utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
print('matplotlib',matplotlib.__version__)
